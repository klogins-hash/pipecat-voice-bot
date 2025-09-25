# Cartesia + Cohere Configuration

This configuration uses:
- **Cartesia** for both Speech-to-Text (STT) and Text-to-Speech (TTS)
- **Cohere Command R** for the Language Model (via OpenRouter)

## 🚀 Quick Start

### 1. Get API Keys

You'll need API keys from two services:

#### Cartesia (STT + TTS)
1. Sign up at [play.cartesia.ai/sign-up](https://play.cartesia.ai/sign-up)
2. Get your API key from the dashboard
3. Cartesia provides both high-quality speech recognition and natural voice synthesis

#### OpenRouter (for Cohere Command R)
1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to [openrouter.ai/keys](https://openrouter.ai/keys) to get your API key
3. OpenRouter provides access to Cohere Command R and many other LLMs

### 2. Configure Environment

Run the interactive setup:
```bash
python setup_env.py
```

Or manually edit `.env`:
```bash
# Cartesia API Key (for both TTS and STT)
CARTESIA_API_KEY=your_cartesia_api_key

# OpenRouter API Key (for Cohere Command R LLM)
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 3. Run Your Bot

```bash
uv run bot_cartesia_cohere.py
```

Open http://localhost:7860 and click "Connect" to start talking!

## 🎯 Why This Configuration?

### Cartesia STT + TTS
- **High Quality**: Cartesia provides state-of-the-art speech recognition and synthesis
- **Low Latency**: Optimized for real-time conversations
- **Natural Voices**: Wide selection of natural-sounding voices
- **Unified Platform**: Single API for both STT and TTS

### Cohere Command R via OpenRouter
- **Advanced Reasoning**: Command R excels at complex reasoning and analysis
- **Cost Effective**: Competitive pricing through OpenRouter
- **Reliable**: Enterprise-grade reliability and performance
- **Easy Integration**: OpenAI-compatible API through OpenRouter

## 🔧 Customization

The bot configuration is in `bot_cartesia_cohere.py`. Key customization points:

### Change the LLM Model
```python
COHERE_MODEL = "cohere/command-r-plus-08-2024"  # Latest Command R+
# or
COHERE_MODEL = "cohere/command-r-08-2024"       # Standard Command R
```

### Change the Voice
Browse voices at [play.cartesia.ai](https://play.cartesia.ai) and update:
```python
VOICE_ID = "your_preferred_voice_id"
```

### Modify Bot Personality
```python
BOT_PERSONALITY = """Your custom personality here..."""
```

### Adjust STT Settings
```python
STT_LANGUAGE = "en"  # Language code
STT_MODEL = "sonic-english"  # Cartesia STT model
```

## 💰 Cost Comparison

This configuration is cost-effective:
- **Cartesia**: Pay-per-use for STT/TTS
- **Cohere via OpenRouter**: Competitive rates for Command R
- **No OpenAI costs**: Eliminates OpenAI API usage

## 🛠️ Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure both Cartesia and OpenRouter keys are valid
2. **Model Not Found**: Verify the Cohere model name in OpenRouter
3. **Audio Issues**: Check browser microphone permissions
4. **Connection Issues**: Try different browsers or check firewall settings

### Debug Mode
Add logging to see what's happening:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Learn More

- [Cartesia Documentation](https://docs.cartesia.ai/)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Cohere Command R Guide](https://docs.cohere.com/docs/command-r-and-command-r-plus)
- [Pipecat Documentation](https://docs.pipecat.ai/)

---

**Ready to build?** Your Cartesia + Cohere voice AI bot is configured and ready to go! 🚀
