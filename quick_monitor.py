#!/usr/bin/env python3
"""
Quick Railway Monitor

Simple script to monitor Railway logs and suggest fixes.
Run this while watching your Railway deployment.

Usage: python quick_monitor.py
"""

import subprocess
import time
import sys
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except:
        return False, "", "Command failed"

def check_railway_status():
    """Check if Railway CLI is working"""
    success, stdout, stderr = run_cmd("railway status")
    return success

def get_railway_logs():
    """Get latest Railway logs"""
    success, stdout, stderr = run_cmd("railway logs --tail 50")
    if success:
        return stdout
    return None

def analyze_logs(logs):
    """Analyze logs for common errors and suggest fixes"""
    if not logs:
        return []
    
    suggestions = []
    
    # Check for common errors
    if "cache mounts MUST be in the format" in logs:
        suggestions.append({
            "error": "Docker cache mount syntax error",
            "fix": "Remove cache mounts from Dockerfile",
            "action": "edit_dockerfile_cache"
        })
    
    if "no match for platform in manifest" in logs or "dailyco/pipecat-base" in logs:
        suggestions.append({
            "error": "Base image not available for platform",
            "fix": "Switch to python:3.11-slim base image",
            "action": "edit_dockerfile_base"
        })
    
    if "ModuleNotFoundError" in logs or "ImportError" in logs:
        suggestions.append({
            "error": "Missing Python module",
            "fix": "Add missing dependencies to pyproject.toml",
            "action": "check_dependencies"
        })
    
    if "Permission denied" in logs:
        suggestions.append({
            "error": "Permission issues",
            "fix": "Add chmod commands to Dockerfile",
            "action": "fix_permissions"
        })
    
    if "EADDRINUSE" in logs or "Port already in use" in logs:
        suggestions.append({
            "error": "Port conflict",
            "fix": "Use Railway's PORT environment variable",
            "action": "fix_port"
        })
    
    if "uv: command not found" in logs:
        suggestions.append({
            "error": "uv not installed",
            "fix": "Add 'RUN pip install uv' to Dockerfile",
            "action": "install_uv"
        })
    
    return suggestions

def apply_fix(action):
    """Apply automatic fixes"""
    if action == "edit_dockerfile_cache":
        log("Applying cache mount fix...")
        # Read and fix Dockerfile
        try:
            with open("Dockerfile", "r") as f:
                content = f.read()
            
            # Remove cache mounts
            fixed = content.replace("--mount=type=cache,target=/root/.cache/uv \\", "")
            fixed = fixed.replace("--mount=type=cache,id=uv-cache,target=/root/.cache/uv \\", "")
            
            with open("Dockerfile", "w") as f:
                f.write(fixed)
            
            # Commit and push
            run_cmd("git add Dockerfile")
            run_cmd('git commit -m "Fix: Remove Docker cache mounts for Railway"')
            success, _, _ = run_cmd("git push")
            
            if success:
                log("✅ Cache mount fix applied and pushed!")
                return True
            else:
                log("❌ Failed to push fix", "ERROR")
                
        except Exception as e:
            log(f"❌ Failed to apply cache mount fix: {e}", "ERROR")
    
    elif action == "edit_dockerfile_base":
        log("Applying base image fix...")
        try:
            with open("Dockerfile", "r") as f:
                content = f.read()
            
            if "dailyco/pipecat-base" in content:
                # Replace base image and add dependencies
                fixed = content.replace(
                    "FROM dailyco/pipecat-base:latest",
                    "FROM python:3.11-slim"
                )
                
                if "apt-get update" not in fixed:
                    fixed = fixed.replace(
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
                    f.write(fixed)
                
                # Commit and push
                run_cmd("git add Dockerfile")
                run_cmd('git commit -m "Fix: Use python:3.11-slim base image for Railway"')
                success, _, _ = run_cmd("git push")
                
                if success:
                    log("✅ Base image fix applied and pushed!")
                    return True
                else:
                    log("❌ Failed to push fix", "ERROR")
                    
        except Exception as e:
            log(f"❌ Failed to apply base image fix: {e}", "ERROR")
    
    return False

def main():
    log("🚀 Starting Railway deployment monitor...")
    
    # Check if Railway CLI is available
    if not check_railway_status():
        log("❌ Railway CLI not available. Make sure you're logged in: railway login", "ERROR")
        return
    
    log("✅ Railway CLI is working")
    log("📡 Monitoring deployment... (Ctrl+C to stop)")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            log(f"--- Check #{iteration} ---")
            
            # Get logs
            logs = get_railway_logs()
            if logs:
                # Analyze for errors
                suggestions = analyze_logs(logs)
                
                if suggestions:
                    log(f"🔍 Found {len(suggestions)} issue(s) to fix:")
                    
                    for i, suggestion in enumerate(suggestions, 1):
                        log(f"  {i}. {suggestion['error']}")
                        log(f"     Fix: {suggestion['fix']}")
                        
                        # Auto-apply fix
                        if apply_fix(suggestion['action']):
                            log("⏳ Waiting for Railway to rebuild...")
                            time.sleep(60)  # Wait for rebuild
                            break
                else:
                    log("✅ No errors detected in logs")
                    
                    # Show recent log snippet
                    recent_logs = logs.split('\n')[-5:]
                    log("Recent logs:")
                    for line in recent_logs:
                        if line.strip():
                            log(f"  {line}")
            else:
                log("⚠️  Could not fetch logs")
            
            log("⏳ Waiting 30 seconds...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        log("👋 Monitoring stopped by user")

if __name__ == "__main__":
    main()
