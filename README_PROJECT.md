# Pipecat Quickstart - Customized Project

This is your customized Pipecat voice AI bot project, ready for development and deployment. Build and deploy voice AI bots in under 10 minutes!

## 🚀 Quick Start

### 1. Set Up API Keys (2 minutes)
Run the interactive setup script:
```bash
python setup_env.py
```

Or manually edit `.env` with your API keys:
```bash
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key
CARTESIA_API_KEY=your_cartesia_api_key
```

### 2. Run Your Bot (1 minute)
```bash
uv run bot.py
```

Open http://localhost:7860 in your browser and click "Connect" to start talking!

## 📁 Project Structure

```
pipecat-quickstart/
├── bot.py                 # Original quickstart bot
├── bot_custom.py         # Customizable template bot
├── setup_env.py          # Interactive API key setup
├── .env                  # Your API keys (keep private!)
├── pyproject.toml        # Dependencies and project config
├── Dockerfile           # For deployment
├── pcc-deploy.toml      # Pipecat Cloud deployment config
├── DEVELOPMENT.md       # Detailed development guide
└── README_PROJECT.md    # This file
```

## 🎯 Customization Options

### Quick Customizations (bot_custom.py)
The `bot_custom.py` file provides easy customization points:

```python
# Change bot personality
BOT_PERSONALITY = "You are a cooking assistant specializing in Italian cuisine."

# Change voice (browse at https://play.cartesia.ai/)
VOICE_ID = "87748186-23bb-4158-a1eb-332911b0b708"  # Child voice

# Custom greeting
CUSTOM_GREETING = "Ciao! I'm your Italian cooking assistant. What shall we cook today?"
```

### Advanced Customizations
- **Add function calling**: Integrate with external APIs
- **Memory/context**: Add conversation history and user sessions  
- **Multimodal**: Add vision or document processing capabilities
- **Custom processors**: Build specialized pipeline components

See `DEVELOPMENT.md` for detailed customization guides.

## 🔑 Required API Keys

| Service | Purpose | Sign Up |
|---------|---------|---------|
| **Deepgram** | Speech-to-Text | [console.deepgram.com/signup](https://console.deepgram.com/signup) |
| **OpenAI** | Language Model | [auth.openai.com/create-account](https://auth.openai.com/create-account) |
| **Cartesia** | Text-to-Speech | [play.cartesia.ai/sign-up](https://play.cartesia.ai/sign-up) |
| Daily (optional) | WebRTC Transport | [dashboard.daily.co/signup](https://dashboard.daily.co/signup) |

## 🌐 Deployment

### Deploy to Pipecat Cloud

1. **Install Pipecat Cloud CLI:**
   ```bash
   uv add pipecatcloud
   ```

2. **Update deployment config:**
   Edit `pcc-deploy.toml` with your Docker Hub username:
   ```toml
   image = "YOUR_DOCKERHUB_USERNAME/quickstart:0.1"
   ```

3. **Upload secrets:**
   ```bash
   uv run pcc secrets set quickstart-secrets --file .env
   ```

4. **Build and deploy:**
   ```bash
   uv run pcc docker build-push
   uv run pcc deploy
   ```

## 🛠️ Development Commands

```bash
# Install dependencies
uv sync

# Run original bot
uv run bot.py

# Run customizable bot
uv run bot_custom.py

# Set up API keys interactively
python setup_env.py

# Deploy to cloud
uv run pcc deploy
```

## 🎨 Voice Options

Browse and test voices at [Cartesia Playground](https://play.cartesia.ai/). Popular options:

- `71a7ad14-091c-4e8e-a314-022ece01c121` - British Reading Lady (default)
- `a0e99841-438c-4a64-b679-ae501e7d6091` - Barbershop Man
- `87748186-23bb-4158-a1eb-332911b0b708` - Child
- `79a125e8-cd45-4c13-8a67-188112f4dd22` - Newsman

## 🔧 Troubleshooting

### Common Issues
- **Import errors**: Run `uv sync` to install dependencies
- **API key errors**: Check `.env` file has correct keys
- **Audio issues**: Allow microphone access in browser
- **Connection issues**: Try different browser or check firewall

### Getting Help
- 📚 [Pipecat Documentation](https://docs.pipecat.ai/)
- 💬 [Discord Community](https://discord.gg/pipecat)
- 🐛 [GitHub Issues](https://github.com/pipecat-ai/pipecat/issues)

## 🎯 Next Steps

1. **Test your bot**: Run `uv run bot.py` and test basic functionality
2. **Customize personality**: Edit `bot_custom.py` to match your use case
3. **Add features**: Implement function calling, memory, or multimodal capabilities
4. **Deploy**: Push to Pipecat Cloud for production use
5. **Scale**: Add monitoring, analytics, and user management

## 📄 License

This project is based on Pipecat, which is licensed under the BSD 2-Clause License.

---

**Happy building! 🚀** Your voice AI bot is ready for customization and deployment.
