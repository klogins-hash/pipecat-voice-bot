#!/usr/bin/env python3
"""
Railway Deployment Monitor

This script monitors Railway deployment logs and automatically fixes common issues
by updating code and pushing fixes to GitHub.

Usage:
    python monitor_railway_deployment.py --service-id YOUR_SERVICE_ID --project-id YOUR_PROJECT_ID

Requirements:
    - Railway CLI installed and authenticated
    - Git repository configured
    - Python packages: requests, subprocess
"""

import subprocess
import time
import re
import json
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class RailwayMonitor:
    def __init__(self, project_id: str, service_id: Optional[str] = None):
        self.project_id = project_id
        self.service_id = service_id
        self.last_log_time = None
        self.known_fixes = {
            "cache mounts MUST be in the format": self.fix_cache_mount,
            "no match for platform in manifest": self.fix_base_image,
            "failed to solve: dailyco/pipecat-base": self.fix_base_image,
            "ModuleNotFoundError": self.fix_missing_module,
            "ImportError": self.fix_import_error,
            "Permission denied": self.fix_permissions,
            "Port already in use": self.fix_port_conflict,
            "EADDRINUSE": self.fix_port_conflict,
            "uv: command not found": self.fix_uv_installation,
            "No module named 'uv'": self.fix_uv_installation,
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_command(self, cmd: List[str], cwd: str = ".") -> Tuple[bool, str, str]:
        """Run shell command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def get_railway_logs(self) -> Optional[str]:
        """Get latest Railway deployment logs"""
        cmd = ["railway", "logs"]
        if self.service_id:
            cmd.extend(["--service", self.service_id])
            
        success, stdout, stderr = self.run_command(cmd)
        if success:
            return stdout
        else:
            self.log(f"Failed to get Railway logs: {stderr}", "ERROR")
            return None
    
    def get_railway_status(self) -> Optional[Dict]:
        """Get Railway service status"""
        cmd = ["railway", "status", "--json"]
        if self.service_id:
            cmd.extend(["--service", self.service_id])
            
        success, stdout, stderr = self.run_command(cmd)
        if success:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                self.log("Failed to parse Railway status JSON", "ERROR")
                return None
        else:
            self.log(f"Failed to get Railway status: {stderr}", "ERROR")
            return None
    
    def detect_errors(self, logs: str) -> List[Tuple[str, str]]:
        """Detect errors in logs and return (error_type, full_error_message)"""
        errors = []
        
        for error_pattern, fix_function in self.known_fixes.items():
            if error_pattern.lower() in logs.lower():
                # Extract the full error context
                lines = logs.split('\n')
                error_context = []
                for i, line in enumerate(lines):
                    if error_pattern.lower() in line.lower():
                        # Get surrounding context
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        error_context = lines[start:end]
                        break
                
                full_error = '\n'.join(error_context)
                errors.append((error_pattern, full_error))
        
        return errors
    
    def fix_cache_mount(self, error_msg: str) -> bool:
        """Fix Docker cache mount syntax"""
        self.log("Fixing Docker cache mount syntax...")
        
        # Read current Dockerfile
        try:
            with open("Dockerfile", "r") as f:
                content = f.read()
            
            # Remove cache mounts
            fixed_content = re.sub(
                r'RUN --mount=type=cache[^\\]*\\\s*',
                'RUN ',
                content
            )
            
            if fixed_content != content:
                with open("Dockerfile", "w") as f:
                    f.write(fixed_content)
                
                return self.commit_and_push("Fix Docker cache mount syntax for Railway compatibility")
            
        except Exception as e:
            self.log(f"Failed to fix cache mount: {e}", "ERROR")
            
        return False
    
    def fix_base_image(self, error_msg: str) -> bool:
        """Fix Docker base image issues"""
        self.log("Fixing Docker base image...")
        
        try:
            with open("Dockerfile", "r") as f:
                content = f.read()
            
            # Replace problematic base image
            if "dailyco/pipecat-base" in content:
                fixed_content = content.replace(
                    "FROM dailyco/pipecat-base:latest",
                    "FROM python:3.11-slim"
                )
                
                # Add necessary dependencies
                if "apt-get update" not in fixed_content:
                    fixed_content = fixed_content.replace(
                        "WORKDIR /app",
                        """WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv"""
                    )
                
                with open("Dockerfile", "w") as f:
                    f.write(fixed_content)
                
                return self.commit_and_push("Fix Docker base image for Railway compatibility")
            
        except Exception as e:
            self.log(f"Failed to fix base image: {e}", "ERROR")
            
        return False
    
    def fix_missing_module(self, error_msg: str) -> bool:
        """Fix missing Python module errors"""
        self.log("Fixing missing Python module...")
        
        # Extract module name from error
        module_match = re.search(r"No module named '([^']+)'", error_msg)
        if module_match:
            module_name = module_match.group(1)
            self.log(f"Missing module: {module_name}")
            
            # Add to pyproject.toml dependencies
            try:
                with open("pyproject.toml", "r") as f:
                    content = f.read()
                
                # Add dependency if not already present
                if module_name not in content:
                    # Simple dependency addition
                    content = content.replace(
                        'dependencies = [',
                        f'dependencies = [\n    "{module_name}",',
                        1
                    )
                    
                    with open("pyproject.toml", "w") as f:
                        f.write(content)
                    
                    return self.commit_and_push(f"Add missing dependency: {module_name}")
                    
            except Exception as e:
                self.log(f"Failed to fix missing module: {e}", "ERROR")
        
        return False
    
    def fix_import_error(self, error_msg: str) -> bool:
        """Fix import errors"""
        self.log("Fixing import error...")
        # Similar to missing module fix
        return self.fix_missing_module(error_msg)
    
    def fix_permissions(self, error_msg: str) -> bool:
        """Fix permission issues"""
        self.log("Fixing permission issues...")
        
        try:
            with open("Dockerfile", "r") as f:
                content = f.read()
            
            # Add permission fixes
            if "chmod" not in content:
                content = content.replace(
                    "COPY bot_production.py ./",
                    "COPY bot_production.py ./\nRUN chmod +x bot_production.py"
                )
                
                with open("Dockerfile", "w") as f:
                    f.write(content)
                
                return self.commit_and_push("Fix file permissions in Docker container")
            
        except Exception as e:
            self.log(f"Failed to fix permissions: {e}", "ERROR")
            
        return False
    
    def fix_port_conflict(self, error_msg: str) -> bool:
        """Fix port conflicts"""
        self.log("Fixing port conflict...")
        
        try:
            # Update bot to use Railway's PORT environment variable
            with open("bot_production.py", "r") as f:
                content = f.read()
            
            if "PORT = int(os.getenv" not in content:
                content = content.replace(
                    'PORT = int(os.getenv("PORT", "7860"))',
                    'PORT = int(os.getenv("PORT", "8080"))'
                )
                
                with open("bot_production.py", "w") as f:
                    f.write(content)
                
                return self.commit_and_push("Fix port configuration for Railway")
            
        except Exception as e:
            self.log(f"Failed to fix port conflict: {e}", "ERROR")
            
        return False
    
    def fix_uv_installation(self, error_msg: str) -> bool:
        """Fix uv installation issues"""
        self.log("Fixing uv installation...")
        
        try:
            with open("Dockerfile", "r") as f:
                content = f.read()
            
            # Ensure uv is properly installed
            if "pip install uv" not in content:
                content = content.replace(
                    "WORKDIR /app",
                    "WORKDIR /app\n\n# Install uv\nRUN pip install uv"
                )
                
                with open("Dockerfile", "w") as f:
                    f.write(content)
                
                return self.commit_and_push("Ensure uv package manager is installed")
            
        except Exception as e:
            self.log(f"Failed to fix uv installation: {e}", "ERROR")
            
        return False
    
    def commit_and_push(self, message: str) -> bool:
        """Commit changes and push to GitHub"""
        try:
            # Add all changes
            success, _, stderr = self.run_command(["git", "add", "."])
            if not success:
                self.log(f"Git add failed: {stderr}", "ERROR")
                return False
            
            # Commit changes
            success, _, stderr = self.run_command(["git", "commit", "-m", message])
            if not success:
                self.log(f"Git commit failed: {stderr}", "ERROR")
                return False
            
            # Push to GitHub
            success, _, stderr = self.run_command(["git", "push"])
            if not success:
                self.log(f"Git push failed: {stderr}", "ERROR")
                return False
            
            self.log(f"Successfully pushed fix: {message}")
            return True
            
        except Exception as e:
            self.log(f"Failed to commit and push: {e}", "ERROR")
            return False
    
    def monitor_deployment(self, interval: int = 30, max_iterations: int = 60):
        """Monitor Railway deployment and fix issues automatically"""
        self.log("Starting Railway deployment monitoring...")
        self.log(f"Project ID: {self.project_id}")
        if self.service_id:
            self.log(f"Service ID: {self.service_id}")
        
        iteration = 0
        consecutive_successes = 0
        
        while iteration < max_iterations:
            iteration += 1
            self.log(f"Monitoring iteration {iteration}/{max_iterations}")
            
            # Get current status
            status = self.get_railway_status()
            if status:
                self.log(f"Service status: {status.get('status', 'unknown')}")
            
            # Get logs
            logs = self.get_railway_logs()
            if not logs:
                self.log("No logs available, waiting...")
                time.sleep(interval)
                continue
            
            # Check for errors
            errors = self.detect_errors(logs)
            
            if errors:
                self.log(f"Found {len(errors)} error(s) to fix")
                consecutive_successes = 0
                
                for error_type, error_msg in errors:
                    self.log(f"Fixing error: {error_type}")
                    fix_function = self.known_fixes[error_type]
                    
                    if fix_function(error_msg):
                        self.log(f"Successfully applied fix for: {error_type}")
                        # Wait for Railway to pick up changes
                        self.log("Waiting for Railway to rebuild...")
                        time.sleep(60)  # Wait longer after pushing fix
                        break
                    else:
                        self.log(f"Failed to fix: {error_type}", "ERROR")
            else:
                consecutive_successes += 1
                self.log(f"No errors detected (success #{consecutive_successes})")
                
                # If we've had several successful checks, deployment might be stable
                if consecutive_successes >= 3:
                    self.log("Deployment appears stable, checking final status...")
                    
                    if status and status.get('status') == 'success':
                        self.log("🎉 Deployment successful!", "SUCCESS")
                        return True
            
            # Wait before next check
            time.sleep(interval)
        
        self.log("Monitoring completed (max iterations reached)")
        return False

def main():
    parser = argparse.ArgumentParser(description="Monitor Railway deployment and auto-fix issues")
    parser.add_argument("--project-id", required=True, help="Railway project ID")
    parser.add_argument("--service-id", help="Railway service ID (optional)")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--max-iterations", type=int, default=60, help="Maximum monitoring iterations")
    
    args = parser.parse_args()
    
    # Check if Railway CLI is available
    success, _, _ = subprocess.run(["railway", "--version"], capture_output=True).returncode == 0
    if not success:
        print("ERROR: Railway CLI not found. Please install: https://docs.railway.app/develop/cli")
        sys.exit(1)
    
    # Check if we're in a git repository
    success, _, _ = subprocess.run(["git", "status"], capture_output=True).returncode == 0
    if not success:
        print("ERROR: Not in a git repository")
        sys.exit(1)
    
    # Start monitoring
    monitor = RailwayMonitor(args.project_id, args.service_id)
    success = monitor.monitor_deployment(args.interval, args.max_iterations)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
