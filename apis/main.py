from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
import subprocess
import time
import json
import platform
import random
import string
import os
import re
import requests
import tempfile
from . import bootstrap_host

app = FastAPI()



# Golem settings model (same as before)
class GolemSettings(BaseModel):
    cores: Optional[int] = None
    memory: Optional[str] = None
    disk: Optional[str] = None
    starting_fee: Optional[str] = None
    env_per_hour: Optional[str] = None
    cpu_per_hour: Optional[str] = None
    account: Optional[str] = None



# Import helper functions from bootstrap_host module
from .bootstrap_host import clean_ansi, check_golem_installed, check_golem_running, check_requirement

# Helper function to check if Golem is running using golemsp status
def is_golem_running() -> bool:
    """Check if Golem is running using golemsp status"""
    try:
        result = subprocess.run(["golemsp", "status"], capture_output=True, text=True, check=True)
        raw_output = result.stdout.strip()
        
        # Parse the status using existing function
        parsed_status = parse_golem_status(raw_output)
        
        # Check if service_status is "is running"
        return parsed_status.get("service_status") == "is running"
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Parsing functions (imported from main.py)
def parse_golem_status(output: str) -> dict:
    parsed = {}
    output = clean_ansi(output)

    # Core status info
    patterns = {
        "service_status": r"Service\s+(is not running|is running)",
        "version": r"Version\s+([\d\.]+)",
        "commit": r"Commit\s+([a-f0-9]+)",
        "date": r"Date\s+([\d\-]+)",
        "build": r"Build\s+(\d+)",
        "node_name": r"Node Name\s+(.+)",
        "subnet": r"Subnet\s+(\w+)",
        "vm_status": r"VM\s+(valid|invalid)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        parsed[key] = match.group(1).strip() if match else None

    # Earnings block
    earnings_patterns = {
        "network": r"network\s+([a-zA-Z0-9]+)",
        "amount_total": r"amount \(total\)\s+([\d\.]+ GLM)",
        "amount_onchain": r"\(on-chain\)\s+([\d\.]+ GLM)",
        "amount_polygon": r"\(polygon\)\s+([\d\.]+ GLM)",
        "pending": r"pending\s+([\d\.]+ GLM \(\d+\))",
        "issued": r"issued\s+([\d\.]+ GLM \(\d+\))",
    }

    earnings = {}
    for key, pattern in earnings_patterns.items():
        match = re.search(pattern, output)
        if match:
            earnings[key] = match.group(1).strip()

    if earnings:
        parsed["earnings"] = earnings

    return parsed

def parse_golem_settings(output: str) -> dict:
    settings_data = {
        "raw_output": output,
        "name": None,
        "cpu_cores": None,
        "memory": None,
        "disk": None,
        "account": None,
        "presets": {},
        "timestamp": time.time(),
    }

    current_preset = None

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        # Parse shared resource lines
        if line.startswith("cores:"):
            settings_data["cpu_cores"] = line.split(":", 1)[1].strip()
        elif line.startswith("memory:"):
            settings_data["memory"] = line.split(":", 1)[1].strip()
        elif line.startswith("disk:"):
            settings_data["disk"] = line.split(":", 1)[1].strip()

        # Detect preset name
        elif "Pricing for preset" in line:
            match = re.search(r'"([^"]+)"', line)
            if match:
                current_preset = match.group(1)
                settings_data["presets"][current_preset] = {}

        # Parse pricing lines
        elif "GLM" in line and current_preset:
            parts = line.split("GLM")
            if len(parts) >= 1:
                price_info = parts[0].strip()
                description = parts[1].strip()
                # Clean and normalize
                key = description.lower().replace(" ", "_")
                value = float(price_info)
                settings_data["presets"][current_preset][key] = value

        # Detect wallet/account line (optional)
        elif "account:" in line or "wallet:" in line:
            settings_data["account"] = line.split(":", 1)[1].strip()

        # Detect name if available
        elif line.lower().startswith("name:"):
            settings_data["name"] = line.split(":", 1)[1].strip()

    return settings_data

def parse_yagna_id_output(output: str) -> dict:
    """Parse yagna id show output and extract node information"""
    # Extract node ID using regex
    node_id_match = re.search(r'nodeId:\s+(0x[a-f0-9]+)', output)
    if not node_id_match:
        return None
    
    node_id = node_id_match.group(1)
    parsed_data = {
        "nodeId": node_id,
        "raw_output": output
    }
    
    # Extract other fields
    alias_match = re.search(r'alias:\s+(null|\S+)', output)
    if alias_match:
        parsed_data["alias"] = None if alias_match.group(1) == "null" else alias_match.group(1)
    
    deleted_match = re.search(r'deleted:\s+(true|false)', output)
    if deleted_match:
        parsed_data["deleted"] = deleted_match.group(1) == "true"
    
    is_default_match = re.search(r'isDefault:\s+(true|false)', output)
    if is_default_match:
        parsed_data["isDefault"] = is_default_match.group(1) == "true"
    
    is_locked_match = re.search(r'isLocked:\s+(true|false)', output)
    if is_locked_match:
        parsed_data["isLocked"] = is_locked_match.group(1) == "true"
    
    return parsed_data


# Bootstrap endpoint for direct host
@app.post("/bootstrap")
def bootstrap_host_endpoint():
    """Bootstrap Golem provider directly on host"""
    return bootstrap_host.bootstrap_host()

# Golem management endpoints (simplified - no VM names)
@app.get("/golem-status")
def golem_status():
    """Get Golem provider status"""
    try:
        result = subprocess.run(["golemsp", "status"], capture_output=True, text=True, check=True)
        raw_output = result.stdout.strip()
        
        # Parse status using the imported function
        clean_data = parse_golem_status(raw_output)
        
        return {
            "status": "success",
            "golem_status": {
                "timestamp": time.time(),
                **clean_data,
                "raw_output": raw_output  # Optional for debugging
            }
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not get Golem status",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

@app.post("/start-golem")
def start_golem():
    """Start Golem provider on host"""
    try:
        # Check if already running
        if is_golem_running():
            return {
                "status": "success",
                "message": "Golem provider is already running",
                "log_file": "~/.local/share/yagna/yagna_rCURRENT.log"
            }
        
        # Start golemsp in background
        cmd = "nohup golemsp run > ~/.local/share/yagna/yagna_rCURRENT.log 2>&1 & echo $!"
        result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        pid = result.stdout.strip()
        
        return {
            "status": "success",
            "message": "Golem provider starting in background",
            "log_file": "~/.local/share/yagna/yagna_rCURRENT.log",
            "pid": pid,
            "note": "Use /golem-status to check if fully started"
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not start Golem provider",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

@app.post("/stop-golem")
def stop_golem():
    """Stop Golem provider on host"""
    try:
        if not is_golem_running():
            return {
                "status": "success",
                "message": "Golem provider is not running"
            }
        
        result = subprocess.run(["golemsp", "stop"], capture_output=True, text=True, check=True)
        
        return {
            "status": "success",
            "message": "Golem provider stopped",
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not stop Golem provider",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

@app.get("/node-id")
def get_node_id():
    """Get node ID using yagna id show"""
    try:
        if not is_golem_running():
            return {
                "status": "error",
                "message": "Golem provider is not running",
                "note": "Start the provider first using /start-golem"
            }
        
        result = subprocess.run(["yagna", "id", "show"], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        # Parse yagna output using the imported function
        parsed_data = parse_yagna_id_output(output)
        
        if parsed_data:
            return {
                "status": "success",
                "message": "Node ID retrieved",
                "node_data": parsed_data
            }
        else:
            return {
                "status": "error",
                "message": "Could not parse node ID from yagna output",
                "raw_output": output
            }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not get node ID",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

@app.get("/golem-settings")
def golem_settings():
    """Get Golem provider settings"""
    try:
        result = subprocess.run(["golemsp", "settings", "show"], capture_output=True, text=True, check=True)
        settings_output = result.stdout.strip()
        
        # Parse settings using the imported function
        parsed_settings = parse_golem_settings(settings_output)
        
        return {
            "status": "success",
            "golem_settings": parsed_settings
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not get Golem settings",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

@app.post("/edit-golem")
def edit_golem_settings(settings: GolemSettings = Body(...)):
    """Edit Golem provider settings"""
    try:
        # Build the golemsp settings command
        settings_commands = []
        
        if settings.cores is not None:
            settings_commands.extend(["--cores", str(settings.cores)])
        if settings.memory is not None:
            settings_commands.extend(["--memory", settings.memory])
        if settings.disk is not None:
            settings_commands.extend(["--disk", settings.disk])
        if settings.starting_fee is not None:
            settings_commands.extend(["--starting-fee", settings.starting_fee])
        if settings.env_per_hour is not None:
            settings_commands.extend(["--env-per-hour", settings.env_per_hour])
        if settings.cpu_per_hour is not None:
            settings_commands.extend(["--cpu-per-hour", settings.cpu_per_hour])
        if settings.account is not None:
            settings_commands.extend(["--account", settings.account])
        
        if not settings_commands:
            return {
                "status": "error",
                "message": "No settings provided to update",
                "available_settings": [
                    "cores", "memory", "disk", "starting_fee", 
                    "env_per_hour", "cpu_per_hour", "account"
                ]
            }
        
        cmd = ["golemsp", "settings", "set"] + settings_commands
        settings_args = " ".join(cmd)  # For display purposes
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        return {
            "status": "success",
            "message": "Golem settings updated",
            "updated_settings": {k: v for k, v in settings.dict().items() if v is not None},
            "command": settings_args,
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not update Golem settings",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }


@app.get("/check-requirements")
def check_requirements():
    """Check host requirements for Golem"""
    try:
        requirements = check_requirement()
        
        return {
            "status": "success",
            "requirements": requirements
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not check requirements: {str(e)}"
        }

@app.get("/verify-installation")
def verify_installation():
    """Verify that Golem and KVM are properly installed"""
    try:
        verification_results = {}
        
        # Verify Golem installation
        try:
            golem_result = subprocess.run(["which", "golemsp"], capture_output=True, text=True, check=True)
            golem_path = golem_result.stdout.strip()
            verification_results["golem_path"] = golem_path
            verification_results["golem_installed"] = True
        except subprocess.CalledProcessError:
            verification_results["golem_path"] = None
            verification_results["golem_installed"] = False
        
        # Verify KVM availability
        try:
            kvm_result = subprocess.run(["ls", "-l", "/dev/kvm"], capture_output=True, text=True, check=True)
            kvm_info = kvm_result.stdout.strip()
            verification_results["kvm_device"] = kvm_info
            verification_results["kvm_available"] = True
        except subprocess.CalledProcessError:
            verification_results["kvm_device"] = None
            verification_results["kvm_available"] = False
        
        # Check if everything is working
        all_good = verification_results.get("golem_installed", False) and verification_results.get("kvm_available", False)
        
        return {
            "status": "success" if all_good else "warning",
            "message": "Installation verification completed",
            "all_systems_go": all_good,
            "verification": verification_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not verify installation: {str(e)}"
        }


@app.get("/golem-log")
def get_golem_log(lines: int = 20):
    """Get Golem provider logs"""
    try:
        log_file = os.path.expanduser("~/.local/share/yagna/yagna_rCURRENT.log")
        if not os.path.exists(log_file):
            return {
                "status": "error",
                "message": "Golem log file not found",
                "note": "Provider may not be running or logs not generated yet"
            }
        
        result = subprocess.run(["tail", "-n", str(lines), log_file], capture_output=True, text=True, check=True)
        
        return {
            "status": "success",
            "log": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not fetch Golem logs",
            "details": str(e)
        }

@app.get("/golem-uptime")
def get_golem_uptime():
    """Get Golem provider uptime"""
    try:
        # Check if Golem is running first
        if not is_golem_running():
            return {
                "status": "error",
                "message": "Golem provider is not running",
                "note": "Start the provider first using /start-golem"
            }
        
        # Get uptime using ps command
        cmd = "ps -eo etime,cmd | grep '[g]olemsp run' | awk '{print $1}'"
        result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        uptime = result.stdout.strip()
        
        if not uptime:
            return {
                "status": "error",
                "message": "Could not determine uptime",
                "note": "Golem process may not be running or command failed"
            }
        
        return {
            "status": "success",
            "uptime": uptime,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not get Golem uptime",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }

@app.get("/ya-provider-log")
def get_ya_provider_log(lines: int = 20):
    """Get ya-provider daemon logs"""
    try:
        log_file = os.path.expanduser("~/.local/share/ya-provider/ya-provider_rCURRENT.log")
        if not os.path.exists(log_file):
            return {
                "status": "error",
                "message": "ya-provider log file not found",
                "note": "Provider daemon may not be running or logs not generated yet"
            }
        
        result = subprocess.run(["tail", "-n", str(lines), log_file], capture_output=True, text=True, check=True)
        
        return {
            "status": "success",
            "log": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Could not fetch ya-provider logs",
            "details": str(e)
        }



@app.get("/hello-world")
def hello_world():
    """Execute hello world script from Idle Finance GitHub repository"""
    try:
        print("🚀 [HELLO-WORLD] Starting hello-world endpoint")
        
        # GitHub raw URL for the hello-world script
        script_url = "https://raw.githubusercontent.com/skillDeCoder/idle-finance-v2/main/automation/golem/scripts/hello-world.sh"
        print(f"📥 [HELLO-WORLD] Downloading script from: {script_url}")
        
        # Download the script with timeout
        response = requests.get(script_url, timeout=15)
        print(f"📊 [HELLO-WORLD] HTTP Response Status: {response.status_code}")
        
        if response.status_code == 404:
            print(f"❌ [HELLO-WORLD] File not found at GitHub URL")
            # Create a simple test script as fallback
            test_script = """#!/bin/bash
echo "Hello World from Local Fallback!"
echo "GitHub file not found, using local test script"
echo "Current time: $(date)"
"""
            print(f"📄 [HELLO-WORLD] Using fallback script content")
            response.text = test_script
        else:
            response.raise_for_status()  # Raise an exception for bad status codes
        
        print(f"📄 [HELLO-WORLD] Downloaded script content ({len(response.text)} chars):")
        print(f"📄 [HELLO-WORLD] Script preview: {response.text[:200]}...")
        
        # Create a temporary file and write the script content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            temp_file.write(response.text)
            temp_script_path = temp_file.name
        
        print(f"💾 [HELLO-WORLD] Saved script to temp file: {temp_script_path}")
        
        # Make the script executable
        os.chmod(temp_script_path, 0o755)
        print(f"🔒 [HELLO-WORLD] Made script executable")
        
        # Execute the script
        print(f"⚡ [HELLO-WORLD] Executing script...")
        result = subprocess.run(["bash", temp_script_path], capture_output=True, text=True, check=True)
        print(f"✅ [HELLO-WORLD] Script execution completed")
        print(f"📤 [HELLO-WORLD] Script output: {result.stdout.strip()}")
        print(f"📤 [HELLO-WORLD] Script stderr: {result.stderr.strip()}")
        
        # Clean up the temporary file
        os.unlink(temp_script_path)
        print(f"🗑️ [HELLO-WORLD] Cleaned up temp file: {temp_script_path}")
        
        print(f"🎉 [HELLO-WORLD] Successfully completed!")
        
        return {
            "status": "success",
            "message": result.stdout.strip(),
            "script_url": script_url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script_content_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text
        }
        
    except requests.RequestException as e:
        print(f"❌ [HELLO-WORLD] Request error: {str(e)}")
        return {
            "status": "error",
            "message": "Could not download hello world script from GitHub",
            "script_url": script_url,
            "details": str(e)
        }
    except subprocess.CalledProcessError as e:
        print(f"❌ [HELLO-WORLD] Script execution error: {str(e)}")
        print(f"❌ [HELLO-WORLD] Script stdout: {e.stdout}")
        print(f"❌ [HELLO-WORLD] Script stderr: {e.stderr}")
        return {
            "status": "error",
            "message": "Could not execute hello world script",
            "details": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }
    except Exception as e:
        print(f"❌ [HELLO-WORLD] Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }























