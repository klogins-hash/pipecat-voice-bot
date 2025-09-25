# 🚀 Railway Deployment Guide

This guide will help you deploy your Pipecat voice AI bot to Railway.

## 📋 Prerequisites

### Required API Keys
- ✅ **Cartesia API Key**: Get from [play.cartesia.ai](https://play.cartesia.ai)
- ✅ **OpenAI API Key**: Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- 🔄 **Cohere API Key** (optional): Get from [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)

### Accounts Needed
- [GitHub Account](https://github.com) (for code repository)
- [Railway Account](https://railway.app) (for deployment)

## 🎯 Deployment Steps

### Step 1: Prepare GitHub Repository

1. **Create a new GitHub repository**:
   ```bash
   # Initialize git in your project
   cd /Users/franksimpson/CascadeProjects/pipecat-quickstart
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit: Pipecat voice AI bot"
   
   # Add remote (replace with your repo URL)
   git remote add origin https://github.com/yourusername/pipecat-voice-bot.git
   
   # Push to GitHub
   git push -u origin main
   ```

2. **Verify these files are included**:
   - ✅ `Dockerfile`
   - ✅ `railway.json`
   - ✅ `bot_production.py`
   - ✅ `cohere_llm_service.py`
   - ✅ `pyproject.toml`
   - ✅ `uv.lock`
   - ✅ `.gitignore`

### Step 2: Deploy to Railway

1. **Login to Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**:
   Go to your project → Variables tab and add:

   ```bash
   # Required
   CARTESIA_API_KEY=your_cartesia_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional
   COHERE_API_KEY=your_cohere_api_key_here
   
   # Production settings (Railway sets these automatically)
   NODE_ENV=production
   PYTHONUNBUFFERED=1
   ```

4. **Deploy**:
   - Railway will automatically detect the Dockerfile
   - The build will start automatically
   - Wait for deployment to complete (5-10 minutes)

### Step 3: Access Your Bot

1. **Get your Railway URL**:
   - Go to Settings → Domains
   - Copy the generated URL (e.g., `https://your-app-name.railway.app`)

2. **Test the deployment**:
   - Open the Railway URL in your browser
   - Click "Connect" and allow microphone access
   - Start talking with your bot!

## 🔧 Configuration Options

### Bot Selection
The production bot automatically selects the best LLM based on available API keys:

1. **OpenAI** (if `OPENAI_API_KEY` is set) - Uses GPT-4o-mini
2. **Cohere** (if `COHERE_API_KEY` is set) - Uses Command R+
3. **Fallback**: Error if no valid keys

### Custom Bot Selection
To force a specific bot, update the Railway start command:

```bash
# In Railway Settings → Deploy
# Change start command to:

# For OpenAI bot:
uv run bot_cartesia_openai.py

# For Cohere bot:
uv run bot_cartesia_cohere_direct.py

# For production auto-select:
uv run bot_production.py
```

## 📊 Monitoring & Logs

### View Logs
1. Go to your Railway project
2. Click on the service
3. Go to "Logs" tab
4. Monitor for:
   - ✅ "Production bot starting"
   - ✅ "All components loaded successfully"
   - ✅ "Bot ready!"

### Health Check
Your bot includes a health check endpoint:
- URL: `https://your-app.railway.app/health`
- Should return: `{"status": "healthy"}`

## 🛠️ Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check these in Railway logs:
- Missing dependencies in pyproject.toml
- Docker build errors
- UV sync issues
```

**Solution**: Ensure all files are committed to GitHub

#### 2. Runtime Errors
```bash
# Check for:
- Missing API keys
- Invalid API keys
- Network connectivity issues
```

**Solution**: Verify environment variables in Railway

#### 3. Connection Issues
```bash
# Check:
- HTTPS is enabled (Railway provides this)
- WebRTC permissions in browser
- Firewall/network restrictions
```

### Debug Commands

```bash
# Test API keys locally:
uv run test_api_keys.py

# Test production bot locally:
uv run bot_production.py

# Check Docker build:
docker build -t pipecat-bot .
docker run -p 7860:7860 pipecat-bot
```

## 🔄 Updates & Redeployment

### Update Your Bot
1. Make changes locally
2. Test with `uv run bot_production.py`
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot configuration"
   git push
   ```
4. Railway will automatically redeploy

### Environment Variable Updates
1. Go to Railway → Variables
2. Update values
3. Railway will restart the service automatically

## 💰 Cost Considerations

### Railway Costs
- **Hobby Plan**: $5/month (includes $5 credit)
- **Pro Plan**: $20/month (includes $20 credit)
- Additional usage: $0.000463 per GB-hour

### API Costs
- **Cartesia**: Pay-per-use (STT + TTS)
- **OpenAI**: Pay-per-token (GPT-4o-mini is cost-effective)
- **Cohere**: Pay-per-token (Command R+ pricing)

### Optimization Tips
1. Use GPT-4o-mini for lower costs
2. Optimize bot responses for shorter lengths
3. Monitor usage in Railway dashboard

## 🎉 Success Checklist

- ✅ Repository created and pushed to GitHub
- ✅ Railway project created and connected
- ✅ Environment variables configured
- ✅ Deployment successful
- ✅ Bot accessible via Railway URL
- ✅ Voice interaction working
- ✅ Health check responding

## 📞 Support

### If You Need Help
1. **Check Railway logs** for specific error messages
2. **Test locally** with the same environment variables
3. **Verify API keys** are valid and have credits
4. **Check GitHub repository** has all required files

### Useful Links
- [Railway Documentation](https://docs.railway.app)
- [Pipecat Documentation](https://docs.pipecat.ai)
- [Docker Documentation](https://docs.docker.com)

---

**Your voice AI bot is ready for production! 🚀**
