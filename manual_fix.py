#!/usr/bin/env python3
"""
Manual Railway Fix Script

This script applies common fixes based on error patterns you provide.
Just run: python3 manual_fix.py "your error message here"
"""

import sys
import subprocess
import re
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

def commit_and_push(message):
    """Commit and push changes"""
    run_cmd("git add .")
    success, _, stderr = run_cmd(f'git commit -m "{message}"')
    if success:
        success, _, stderr = run_cmd("git push")
        if success:
            log(f"✅ Pushed: {message}")
            return True
        else:
            log(f"❌ Push failed: {stderr}", "ERROR")
    else:
        log("No changes to commit")
    return False

def fix_cache_mount():
    """Fix Docker cache mount issues"""
    log("Fixing Docker cache mount...")
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        # Remove cache mounts
        fixed = re.sub(r'RUN --mount=type=cache[^\\]*\\\s*', 'RUN ', content)
        
        if fixed != content:
            with open("Dockerfile", "w") as f:
                f.write(fixed)
            return commit_and_push("Fix: Remove Docker cache mounts for Railway")
        else:
            log("No cache mounts found to fix")
    except Exception as e:
        log(f"Error fixing cache mount: {e}", "ERROR")
    return False

def fix_base_image():
    """Fix Docker base image"""
    log("Fixing Docker base image...")
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        if "dailyco/pipecat-base" in content:
            # Replace base image
            fixed = content.replace(
                "FROM dailyco/pipecat-base:latest",
                "FROM python:3.11-slim"
            )
            
            # Add dependencies if not present
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
            return commit_and_push("Fix: Use python:3.11-slim base image")
        else:
            log("Base image already correct")
    except Exception as e:
        log(f"Error fixing base image: {e}", "ERROR")
    return False

def fix_uv_installation():
    """Ensure uv is installed"""
    log("Ensuring uv is installed...")
    try:
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        if "pip install uv" not in content:
            # Add uv installation
            fixed = content.replace(
                "WORKDIR /app",
                "WORKDIR /app\n\n# Install uv\nRUN pip install uv"
            )
            
            with open("Dockerfile", "w") as f:
                f.write(fixed)
            return commit_and_push("Fix: Ensure uv is installed")
        else:
            log("uv installation already present")
    except Exception as e:
        log(f"Error fixing uv: {e}", "ERROR")
    return False

def fix_port_config():
    """Fix port configuration"""
    log("Fixing port configuration...")
    try:
        with open("bot_production.py", "r") as f:
            content = f.read()
        
        # Ensure we use Railway's PORT env var
        if 'PORT = int(os.getenv("PORT", "7860"))' in content:
            fixed = content.replace(
                'PORT = int(os.getenv("PORT", "7860"))',
                'PORT = int(os.getenv("PORT", "8080"))'
            )
            
            with open("bot_production.py", "w") as f:
                f.write(fixed)
            return commit_and_push("Fix: Update port configuration for Railway")
        else:
            log("Port configuration looks correct")
    except Exception as e:
        log(f"Error fixing port: {e}", "ERROR")
    return False

def analyze_and_fix(error_text):
    """Analyze error and apply appropriate fix"""
    error_lower = error_text.lower()
    
    fixes_applied = []
    
    if "cache mounts must be in the format" in error_lower:
        if fix_cache_mount():
            fixes_applied.append("cache mount")
    
    if "no match for platform" in error_lower or "dailyco/pipecat-base" in error_lower:
        if fix_base_image():
            fixes_applied.append("base image")
    
    if "uv: command not found" in error_lower or "no module named 'uv'" in error_lower:
        if fix_uv_installation():
            fixes_applied.append("uv installation")
    
    if "eaddrinuse" in error_lower or "port already in use" in error_lower:
        if fix_port_config():
            fixes_applied.append("port configuration")
    
    if fixes_applied:
        log(f"✅ Applied fixes: {', '.join(fixes_applied)}")
        log("⏳ Railway should rebuild automatically...")
        return True
    else:
        log("❌ No automatic fixes available for this error")
        log("💡 Please share the error and I'll create a custom fix")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manual_fix.py 'error message from Railway logs'")
        print("\nOr run with common fixes:")
        print("  python3 manual_fix.py cache")
        print("  python3 manual_fix.py base-image") 
        print("  python3 manual_fix.py uv")
        print("  python3 manual_fix.py port")
        return
    
    error_or_command = sys.argv[1]
    
    log("🔧 Railway Manual Fix Tool")
    
    # Handle direct commands
    if error_or_command == "cache":
        fix_cache_mount()
    elif error_or_command == "base-image":
        fix_base_image()
    elif error_or_command == "uv":
        fix_uv_installation()
    elif error_or_command == "port":
        fix_port_config()
    else:
        # Analyze error text
        log(f"Analyzing error: {error_or_command[:100]}...")
        analyze_and_fix(error_or_command)

if __name__ == "__main__":
    main()
