import subprocess
import time
import platform
import os
import re
import requests
import tempfile

# GitHub script URLs - change these to point to different repositories or branches
GITHUB_SCRIPT_BASE_URL = "https://raw.githubusercontent.com/skillDeCoder/idle-finance-v2/main/automation/golem/scripts"
GITHUB_SCRIPT_URLS = {
    "install_golem": f"{GITHUB_SCRIPT_BASE_URL}/install-golem.sh",
    "add_golem_path": f"{GITHUB_SCRIPT_BASE_URL}/add-golem-path.sh",
    "install_kvm": f"{GITHUB_SCRIPT_BASE_URL}/install-kvm.sh",
    "set_kvm_permissions": f"{GITHUB_SCRIPT_BASE_URL}/set-kvm-permission.sh"
}

def clean_ansi(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def check_golem_installed() -> bool:
    """Check if golemsp is installed and available"""
    try:
        subprocess.run(["golemsp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_golem_running() -> bool:
    """Check if golemsp is currently running"""
    try:
        subprocess.run(["pgrep", "golemsp"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_requirement() -> dict:
    """Check if host machine meets requirements for Golem provider"""
    requirements = {
        "platform": platform.system(),
        "virtualization_support": False,
        "virtualization_count": 0,
        "meets_requirements": False
    }
    
    # Check if platform is Linux
    if platform.system() != "Linux":
        requirements["meets_requirements"] = False
        return requirements
    
    # Check virtualization support
    try:
        result = subprocess.run(["egrep", "-c", "(vmx|svm)", "/proc/cpuinfo"], 
                              capture_output=True, text=True, check=True)
        virtualization_count = int(result.stdout.strip())
        requirements["virtualization_count"] = virtualization_count
        requirements["virtualization_support"] = virtualization_count > 0
        requirements["meets_requirements"] = virtualization_count > 0
    except (subprocess.CalledProcessError, ValueError):
        requirements["virtualization_support"] = False
        requirements["meets_requirements"] = False
    
    return requirements

def bootstrap_host():
    """
    Bootstrap Golem provider directly on host:
    1. Check requirements
    2. Install expect (if needed)
    3. Install Golem
    4. Add Golem path
    5. Install KVM
    6. Set KVM permissions
    """
    bootstrap_steps = []
    current_step = 0
    
    try:
        # Step 1: Check requirements
        current_step += 1
        print(f"[STEP {current_step}/5] Checking host requirements")
        requirements = check_requirement()
        
        if not requirements["meets_requirements"]:
            bootstrap_steps.append({
                "step": current_step,
                "action": "check_requirements",
                "status": "error",
                "message": f"Host requirements not met: {requirements}",
                "requirements": requirements
            })
            return {
                "status": "error",
                "message": "Host requirements not met",
                "requirements": requirements,
                "steps": bootstrap_steps
            }
        
        bootstrap_steps.append({
            "step": current_step,
            "action": "check_requirements",
            "status": "success",
            "message": "Host requirements met",
            "requirements": requirements
        })
        print(f"Step {current_step} completed: Requirements checked")
        
        # Wait a moment
        time.sleep(2)
        
        # Step 2: Install expect (if needed)
        current_step += 1
        print(f"[STEP {current_step}/5] Installing expect (if needed)")
        
        # Check if expect is already installed
        try:
            subprocess.run(["expect", "-c", "exit"], capture_output=True, check=True)
            bootstrap_steps.append({
                "step": current_step,
                "action": "install_expect",
                "status": "success",
                "message": "Expect is already installed"
            })
            print(f"Step {current_step} completed: Expect already installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Install expect using apt
                result = subprocess.run(["sudo", "apt", "update"], capture_output=True, text=True, check=True)
                result = subprocess.run(["sudo", "apt", "install", "-y", "expect"], capture_output=True, text=True, check=True)
                
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_expect",
                    "status": "success",
                    "message": "Expect installed successfully",
                    "output": result.stdout
                })
                print(f"Step {current_step} completed: Expect installed")
            except subprocess.CalledProcessError as e:
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_expect",
                    "status": "error",
                    "message": "Failed to install expect",
                    "error": str(e),
                    "stdout": e.stdout,
                    "stderr": e.stderr
                })
                return {
                    "status": "error",
                    "message": f"Bootstrap failed at step {current_step}",
                    "steps": bootstrap_steps,
                    "error": str(e)
                }
        
        # Wait for expect installation
        time.sleep(2)
        
        # Step 3: Install Golem
        current_step += 1
        print(f"[STEP {current_step}/5] Installing Golem")
        
        if check_golem_installed():
            bootstrap_steps.append({
                "step": current_step,
                "action": "install_golem",
                "status": "success",
                "message": "Golem is already installed"
            })
            print(f"Step {current_step} completed: Golem already installed")
        else:
            # Install Golem using the GitHub script
            try:
                script_url = GITHUB_SCRIPT_URLS["install_golem"]
                
                # Download the script
                response = requests.get(script_url, timeout=15)
                response.raise_for_status()
                
                # Create temporary file and write script content
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                    temp_file.write(response.text)
                    temp_script_path = temp_file.name
                
                # Make script executable
                os.chmod(temp_script_path, 0o755)
                
                # Execute the script
                result = subprocess.run(["bash", temp_script_path], capture_output=True, text=True, check=True)
                
                # Clean up
                os.unlink(temp_script_path)
                
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_golem",
                    "status": "success",
                    "message": "Golem installed successfully",
                    "output": result.stdout,
                    "script_url": script_url
                })
                print(f"Step {current_step} completed: Golem installed")
            except requests.RequestException as e:
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_golem",
                    "status": "error",
                    "message": "Failed to download install-golem script from GitHub",
                    "error": str(e),
                    "script_url": script_url
                })
                return {
                    "status": "error",
                    "message": f"Bootstrap failed at step {current_step}",
                    "steps": bootstrap_steps,
                    "error": str(e)
                }
            except subprocess.CalledProcessError as e:
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_golem",
                    "status": "error",
                    "message": "Failed to install Golem",
                    "error": str(e),
                    "stdout": e.stdout,
                    "stderr": e.stderr
                })
                return {
                    "status": "error",
                    "message": f"Bootstrap failed at step {current_step}",
                    "steps": bootstrap_steps,
                    "error": str(e)
                }
        
        # Wait for Golem installation
        time.sleep(5)
        
        # Step 4: Add Golem path
        current_step += 1
        print(f"[STEP {current_step}/5] Adding Golem path")
        
        try:
            # Add Golem path using the GitHub script
            script_url = GITHUB_SCRIPT_URLS["add_golem_path"]
            
            # Download the script
            response = requests.get(script_url, timeout=15)
            response.raise_for_status()
            
            # Create temporary file and write script content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                temp_file.write(response.text)
                temp_script_path = temp_file.name
            
            # Make script executable
            os.chmod(temp_script_path, 0o755)
            
            # Execute the script
            result = subprocess.run(["bash", temp_script_path], capture_output=True, text=True, check=True)
            
            # Clean up
            os.unlink(temp_script_path)
            
            bootstrap_steps.append({
                "step": current_step,
                "action": "add_golem_path",
                "status": "success",
                "message": "Golem path added successfully",
                "output": result.stdout,
                "script_url": script_url
            })
            print(f"Step {current_step} completed: Golem path added")
        except requests.RequestException as e:
            bootstrap_steps.append({
                "step": current_step,
                "action": "add_golem_path",
                "status": "error",
                "message": "Failed to download add-golem-path script from GitHub",
                "error": str(e),
                "script_url": script_url
            })
            return {
                "status": "error",
                "message": f"Bootstrap failed at step {current_step}",
                "steps": bootstrap_steps,
                "error": str(e)
            }
        except subprocess.CalledProcessError as e:
            bootstrap_steps.append({
                "step": current_step,
                "action": "add_golem_path",
                "status": "error",
                "message": "Failed to add Golem path",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            })
            return {
                "status": "error",
                "message": f"Bootstrap failed at step {current_step}",
                "steps": bootstrap_steps,
                "error": str(e)
            }
        
        # Wait for path setup
        time.sleep(2)
        
        # Step 5: Install KVM (long-running process)
        current_step += 1
        print(f"[STEP {current_step}/5] Installing KVM (long-running process)")
        
        # Check if KVM is already available
        try:
            subprocess.run(["kvm-ok"], capture_output=True, check=True)
            bootstrap_steps.append({
                "step": current_step,
                "action": "install_kvm",
                "status": "success",
                "message": "KVM is already available"
            })
            print(f"Step {current_step} completed: KVM already available")
        except subprocess.CalledProcessError:
            # Install KVM using the GitHub script
            try:
                script_url = GITHUB_SCRIPT_URLS["install_kvm"]
                
                # Download the script
                response = requests.get(script_url, timeout=15)
                response.raise_for_status()
                
                # Create temporary file and write script content
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                    temp_file.write(response.text)
                    temp_script_path = temp_file.name
                
                # Make script executable
                os.chmod(temp_script_path, 0o755)
                
                # Execute the script as a background process
                kvm_process = subprocess.Popen(["bash", temp_script_path], 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.PIPE, 
                                             text=True)
                
                # Wait 5 seconds for initial progress
                time.sleep(5)
                
                # Check if process is still running
                if kvm_process.poll() is None:
                    # Process is still running, return optimistic response
                    bootstrap_steps.append({
                        "step": current_step,
                        "action": "install_kvm",
                        "status": "success",
                        "message": "KVM installation started (running in background)",
                        "note": "KVM installation is a long-running process. Use /check-requirements to verify completion.",
                        "script_url": script_url
                    })
                    print(f"Step {current_step} completed: KVM installation started (background)")
                else:
                    # Process completed quickly
                    stdout, stderr = kvm_process.communicate()
                    if kvm_process.returncode == 0:
                        bootstrap_steps.append({
                            "step": current_step,
                            "action": "install_kvm",
                            "status": "success",
                            "message": "KVM installed successfully",
                            "output": stdout,
                            "script_url": script_url
                        })
                        print(f"Step {current_step} completed: KVM installed")
                    else:
                        raise subprocess.CalledProcessError(kvm_process.returncode, kvm_process.args, stdout, stderr)
                
                # Clean up temp file
                os.unlink(temp_script_path)
                        
            except requests.RequestException as e:
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_kvm",
                    "status": "error",
                    "message": "Failed to download install-kvm script from GitHub",
                    "error": str(e),
                    "script_url": script_url
                })
                return {
                    "status": "error",
                    "message": f"Bootstrap failed at step {current_step}",
                    "steps": bootstrap_steps,
                    "error": str(e)
                }
            except subprocess.CalledProcessError as e:
                bootstrap_steps.append({
                    "step": current_step,
                    "action": "install_kvm",
                    "status": "error",
                    "message": "Failed to install KVM",
                    "error": str(e),
                    "stdout": getattr(e, 'stdout', ''),
                    "stderr": getattr(e, 'stderr', '')
                })
                return {
                    "status": "error",
                    "message": f"Bootstrap failed at step {current_step}",
                    "steps": bootstrap_steps,
                    "error": str(e)
                }
        
        # Wait for KVM installation
        time.sleep(5)
        
        # Step 5: Set KVM permissions
        current_step += 1
        print(f"[STEP {current_step}/5] Setting KVM permissions")
        
        try:
            # Set KVM permissions using the GitHub script
            script_url = GITHUB_SCRIPT_URLS["set_kvm_permissions"]
            
            # Download the script
            response = requests.get(script_url, timeout=15)
            response.raise_for_status()
            
            # Create temporary file and write script content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                temp_file.write(response.text)
                temp_script_path = temp_file.name
            
            # Make script executable
            os.chmod(temp_script_path, 0o755)
            
            # Execute the script
            result = subprocess.run(["bash", temp_script_path], capture_output=True, text=True, check=True)
            
            # Clean up
            os.unlink(temp_script_path)
            
            bootstrap_steps.append({
                "step": current_step,
                "action": "set_kvm_permissions",
                "status": "success",
                "message": "KVM permissions set successfully",
                "output": result.stdout,
                "script_url": script_url
            })
            print(f"Step {current_step} completed: KVM permissions set")
        except requests.RequestException as e:
            bootstrap_steps.append({
                "step": current_step,
                "action": "set_kvm_permissions",
                "status": "error",
                "message": "Failed to download set-kvm-permission script from GitHub",
                "error": str(e),
                "script_url": script_url
            })
            return {
                "status": "error",
                "message": f"Bootstrap failed at step {current_step}",
                "steps": bootstrap_steps,
                "error": str(e)
            }
        except subprocess.CalledProcessError as e:
            bootstrap_steps.append({
                "step": current_step,
                "action": "set_kvm_permissions",
                "status": "error",
                "message": "Failed to set KVM permissions",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            })
            return {
                "status": "error",
                "message": f"Bootstrap failed at step {current_step}",
                "steps": bootstrap_steps,
                "error": str(e)
            }
        
        print("Bootstrap process completed successfully!")
        return {
            "status": "success",
            "message": "Bootstrap completed successfully",
            "steps_completed": len(bootstrap_steps),
            "total_steps": 5,
            "bootstrap_steps": bootstrap_steps,
            "completion_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Use /verify-installation to check if everything is working, then /start-golem to start the provider"
        }
        
    except subprocess.CalledProcessError as e:
        # Handle step-specific errors
        error_step = {
            "step": current_step,
            "action": f"step_{current_step}",
            "status": "error",
            "message": f"Failed at step {current_step}",
            "error": str(e),
            "stdout": getattr(e, 'stdout', ''),
            "stderr": getattr(e, 'stderr', '')
        }
        
        bootstrap_steps.append(error_step)
        
        return {
            "status": "error",
            "message": f"Bootstrap failed at step {current_step}",
            "steps_completed": len(bootstrap_steps) - 1,
            "total_steps": 5,
            "failed_step": current_step,
            "bootstrap_steps": bootstrap_steps,
            "error": str(e)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error during bootstrap",
            "steps_completed": len(bootstrap_steps),
            "total_steps": 5,
            "bootstrap_steps": bootstrap_steps,
            "error": str(e)
        } 