# 🔧 Troubleshooting Guide

## Current Status
✅ **Bot is running**: http://localhost:7860  
✅ **API keys validated**: Cartesia and Cohere working  
✅ **Custom Cohere LLM**: Direct integration implemented  

## 🚨 Connection Issues

### **Symptoms**
- Agent shows "Connecting..." but never connects
- Connection drops immediately after connecting
- No audio input/output

### **Step-by-Step Troubleshooting**

#### **1. Browser Troubleshooting**
```bash
# Try these browsers in order:
1. Chrome (recommended)
2. Firefox 
3. Safari
4. Edge
```

**Browser Settings:**
- ✅ Allow microphone access
- ✅ Allow autoplay audio
- ✅ Disable VPN if active
- ✅ Try incognito/private mode

#### **2. URL Troubleshooting**
Try these URLs in order:
```
http://localhost:7860          # Main URL
http://localhost:7860/client   # Direct client URL
http://127.0.0.1:7860         # IP address version
```

#### **3. Network Troubleshooting**
```bash
# Check if port is accessible
curl http://localhost:7860

# Check if bot is running
ps aux | grep "bot_cartesia_cohere_direct.py"

# Check port usage
lsof -i :7860
```

#### **4. Bot Restart**
```bash
# Stop current bot
pkill -f "bot_cartesia_cohere_direct.py"

# Restart with verbose logging
uv run bot_cartesia_cohere_direct.py
```

#### **5. Firewall/Security**
- Disable firewall temporarily
- Check antivirus software
- Try different network (mobile hotspot)

#### **6. Hardware Troubleshooting**
```bash
# Test microphone
# macOS: System Preferences > Sound > Input
# Check microphone levels and permissions
```

#### **7. Alternative Bot Testing**
If Cohere bot doesn't work, try simpler versions:

```bash
# Test with original bot (needs OpenAI key)
uv run bot.py

# Test with Cartesia + OpenAI (needs OpenAI key)  
uv run bot_cartesia_openai.py
```

## 🔍 **Debug Mode**

### **Enable Debug Logging**
Add this to the top of `bot_cartesia_cohere_direct.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Check Browser Console**
1. Open browser developer tools (F12)
2. Go to Console tab
3. Look for WebRTC errors
4. Check Network tab for failed requests

### **Check Bot Logs**
Look for these error patterns:
```
❌ WebRTC connection failed
❌ Cartesia STT connection error  
❌ Cohere API error
❌ Audio device not found
```

## 🛠️ **Common Fixes**

### **Fix 1: Browser Permissions**
```javascript
// In browser console, check permissions:
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => console.log("Microphone OK"))
  .catch(err => console.error("Microphone error:", err));
```

### **Fix 2: Clear Browser Data**
- Clear cookies and site data for localhost
- Restart browser completely

### **Fix 3: System Audio**
```bash
# macOS: Reset audio system
sudo killall coreaudiod
```

### **Fix 4: Bot Configuration**
Check these settings in `bot_cartesia_cohere_direct.py`:
```python
# Try increasing VAD timeout
VAD_STOP_SECONDS = 0.5  # Instead of 0.2

# Try different Cohere model
COHERE_MODEL = "command-r-08-2024"  # Instead of plus version
```

## 🆘 **Emergency Fallback**

If nothing works, use the working Cartesia + OpenAI version:

1. **Get OpenAI API key**: https://platform.openai.com/api-keys
2. **Add to .env**:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ```
3. **Run fallback bot**:
   ```bash
   uv run bot_cartesia_openai.py
   ```

## 📞 **Get Help**

### **Collect Debug Info**
```bash
# System info
uname -a
python --version

# Bot status
ps aux | grep bot

# Network status
netstat -an | grep 7860

# Browser info
# Chrome: chrome://version/
# Firefox: about:support
```

### **Log Files**
Check terminal output for:
- Connection attempts
- API errors  
- WebRTC status
- Audio device issues

## ✅ **Success Indicators**

When working correctly, you should see:
```
✅ Bot ready! → Open http://localhost:7860/client
✅ Client connected to [Bot Name]
✅ Audio stream established
✅ STT processing audio
✅ LLM generating response
✅ TTS synthesizing speech
```

---

**Still having issues?** The bot is currently running and ready to test. Try the troubleshooting steps above in order.
