# Golem Provider Automation API

A comprehensive FastAPI-based automation system for managing Golem provider nodes directly on the host machine. This system provides a complete set of APIs for bootstrapping, managing, and monitoring Golem provider services.

## 🚀 Features

- **Complete Bootstrap Process**: Automated installation of Golem, KVM, and dependencies
- **Real-time Monitoring**: Status, logs, uptime, and performance tracking
- **Dynamic Configuration**: Runtime settings modification
- **Cross-platform Support**: Works on macOS, Windows, and Linux
- **Robust Error Handling**: Comprehensive error reporting and recovery

## 📋 Prerequisites

- **Linux Host**: Currently optimized for Linux systems
- **Virtualization Support**: CPU must support virtualization (VMX/SVM)
- **Python 3.8+**: Required for FastAPI backend
- **Sudo Access**: Required for KVM installation and permissions

## 🛠️ Installation

### Quick Start

1. **Navigate to the automation directory:**

   ```bash
   cd automation/golem
   ```

2. **Start the backend server:**

   ```bash
   # On macOS/Linux
   ./scripts/run-macOS.sh

   # On Windows
   ./scripts/run-windows.bat

   ```

3. **Access the API:**
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc

## 🔧 API Endpoints

### Bootstrap & Setup

#### `POST /bootstrap`

Complete system bootstrap process. Installs Golem, KVM, and configures the environment.

**Process Steps:**

1. Check host requirements (Linux + virtualization)
2. Install Expect (if needed)
3. Install Golem provider
4. Add Golem to PATH
5. Install KVM (with timeout protection)
6. Set KVM permissions

Some times this can become a long running process ( > 10mins) if it does that,

1. Your internet might not support downloading golem so you will need a vpn
2. it has intalled and you need to cross-check that with /verify-installation

**Response:**

```json
{
  "status": "success",
  "message": "Bootstrap completed successfully",
  "steps_completed": 5,
  "total_steps": 5,
  "bootstrap_steps": [...],
  "completion_time": "2024-01-15 14:30:45",
  "note": "Use /verify-installation to check if everything is working"
}
```

#### `GET /verify-installation`

Verify that Golem and KVM are properly installed.

**Response:**

```json
{
  "status": "success",
  "message": "Installation verification completed",
  "all_systems_go": true,
  "verification": {
    "golem_installed": true,
    "golem_path": "/home/user/.local/bin/golemsp",
    "kvm_available": true,
    "kvm_device": "crw-rw-rw- 1 root kvm 10, 232 Jan 15 14:30 /dev/kvm"
  }
}
```

#### `GET /check-requirements`

Check if the host meets all requirements for running Golem.

### Provider Management

#### `POST /start-golem`

Start the Golem provider service.

**Features:**

- Checks if already running using `golemsp status`
- Starts provider in background with logging
- Returns optimistic response for long-running startup

**Response:**

```json
{
  "status": "success",
  "message": "Golem provider starting in background",
  "log_file": "~/.local/share/yagna/yagna_rCURRENT.log",
  "pid": "12345",
  "note": "Use /golem-status to check if fully started"
}
```

#### `POST /stop-golem`

Stop the Golem provider service.

#### `GET /golem-status`

Get comprehensive provider status information.

**Returns:**

- Service status (running/not running)
- Version information
- Node details
- Earnings information
- VM status

**Response:**

```json
{
  "status": "success",
  "golem_status": {
    "timestamp": 1705329045,
    "service_status": "is running",
    "version": "0.12.0",
    "node_name": "my-provider",
    "earnings": {
      "amount_total": "0.5 GLM",
      "pending": "0.1 GLM (2)"
    }
  }
}
```

### Configuration

#### `GET /golem-settings`

Get current provider settings and pricing.

#### `POST /edit-golem`

Dynamically update provider settings.

**Supported Settings:**

- `cores`: CPU cores allocation
- `memory`: Memory allocation
- `disk`: Disk space allocation
- `starting_fee`: Initial fee for jobs
- `env_per_hour`: Environment cost per hour
- `cpu_per_hour`: CPU cost per hour
- `account`: Wallet address

**Example Request:**

```json
{
  "cores": 4,
  "memory": "8GB",
  "starting_fee": "0.1 GLM",
  "cpu_per_hour": "0.05 GLM"
}
```

### Monitoring & Logs

#### `GET /node-id`

Get the provider's node ID and wallet information.

**Response:**

```json
{
  "status": "success",
  "message": "Node ID retrieved",
  "node_data": {
    "node_id": "0x8b5079bceddbe45ebac311712c5942d91c08edfd",
    "alias": null,
    "is_default": true,
    "is_locked": false
  }
}
```

#### `GET /golem-uptime`

Get the uptime of the Golem provider process.

**Response:**

```json
{
  "status": "success",
  "uptime": "2-15:30:45",
  "timestamp": "2024-01-15 14:30:45"
}
```

#### `GET /golem-log`

Get yagna daemon logs.

**Parameters:**

- `lines`: Number of log lines to retrieve (default: 20)

**Path:** `~/.local/share/yagna/yagna_rCURRENT.log`

#### `GET /ya-provider-log`

Get ya-provider daemon logs.

**Parameters:**

- `lines`: Number of log lines to retrieve (default: 20)

**Path:** `~/.local/share/ya-provider/ya-provider_rCURRENT.log`

## 📁 Log Files

### 🔧 ya-provider Logs

**Location:** `~/.local/share/ya-provider/ya-provider_rCURRENT.log`

**Purpose:** Tracks what the provider service is doing:

- Market negotiations (offers, demands)
- Job execution details
- Resource allocation (CPUs, memory, disk)
- VM/spawned runtime management

_Think of this as the "host" side log for people offering compute._

### ⚙️ yagna Logs

**Location:** `~/.local/share/yagna/yagna_rCURRENT.log`

**Purpose:** Tracks the general Golem node runtime activity:

- Wallet management
- Network discovery
- Payment activity (GLM transfers)
- API calls (from golemsp or client apps)
- Service startup and registration

## 🏗️ Architecture

### Direct Host Execution

- **No VM Overhead**: Runs directly on the host OS
- **Better Performance**: Direct access to hardware resources
- **Simplified Management**: Single system to manage

### API Structure

- **FastAPI Backend**: Modern, fast Python web framework
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Responses**: Consistent response format
- **Error Handling**: Comprehensive error reporting

### Process Management

- **Optimistic Responses**: For long-running operations
- **Background Processing**: Non-blocking operations
- **Status Checking**: Reliable process detection using `golemsp status`

## 🔍 Troubleshooting

### Common Issues

1. **Bootstrap Hanging**

   - The bootstrap process includes timeout protection
   - KVM installation is limited to 5 minutes
   - Use `/verify-installation` to check completion

2. **Provider Not Starting**

   - Check requirements with `/check-requirements`
   - Verify installation with `/verify-installation`
   - Check logs with `/golem-log` and `/ya-provider-log`

3. **Permission Issues**
   - Ensure user is in the `kvm` group
   - Check `/dev/kvm` permissions
   - Verify sudo access for installation

### Debug Commands

```bash
# Check if Golem is installed
which golemsp

# Check KVM availability
kvm-ok

# Check virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo

# Check process status
ps -eo etime,cmd | grep '[g]olemsp run'
```

## 🚀 Development

### Project Structure

```
automation/golem/
├── apis/
│   ├── main.py              # Main FastAPI application
│   └── bootstrap_host.py    # Bootstrap logic
├── scripts/
│   ├── run-macOS.sh         # macOS setup script
│   ├── run-windows.bat      # Windows setup script
│   ├── install-golem.sh     # Golem installation
│   ├── install-kvm.sh       # KVM installation
│   ├── set-kvm-permission.sh # KVM permissions
│   └── add-golem-path.sh    # PATH configuration
└── README.md                # This file
```

### Adding New Endpoints

1. **Define the endpoint** in `apis/main.py`
2. **Add error handling** for robustness
3. **Update this README** with documentation
4. **Test thoroughly** with different scenarios

---
