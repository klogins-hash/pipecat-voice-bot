# Development Guide

## Project Structure

```
pipecat-quickstart/
├── bot.py                 # Main bot implementation
├── pyproject.toml        # Project dependencies and configuration
├── .env                  # Environment variables (API keys)
├── env.example          # Template for environment variables
├── Dockerfile           # Docker configuration for deployment
├── pcc-deploy.toml      # Pipecat Cloud deployment configuration
├── DEVELOPMENT.md       # This file - development guide
└── pipecat/            # Original Pipecat repository (for reference)
```

## Key Components

### bot.py
The main bot implementation contains:
- **Speech-to-Text (STT)**: Deepgram service for converting speech to text
- **Large Language Model (LLM)**: OpenAI service for generating responses
- **Text-to-Speech (TTS)**: Cartesia service for converting text to speech
- **Pipeline**: Connects all components together
- **Transport**: Handles WebRTC connections for real-time communication

### Key Configuration Points for Customization

1. **Voice Selection** (line 69):
   ```python
   voice_id="71a7ad14-091c-4e8e-a314-022ece01c121"  # British Reading Lady
   ```

2. **System Prompt** (lines 74-79):
   ```python
   messages = [
       {
           "role": "system",
           "content": "You are a friendly AI assistant. Respond naturally and keep your answers conversational.",
       },
   ]
   ```

3. **VAD Parameters** (line 132):
   ```python
   vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2))
   ```

## Common Customizations

### 1. Change the Bot's Personality
Edit the system message in `bot.py`:
```python
"content": "You are a helpful cooking assistant. Provide recipe suggestions and cooking tips."
```

### 2. Change the Voice
Browse available voices at [Cartesia Playground](https://play.cartesia.ai/) and update the `voice_id`:
```python
voice_id="your_new_voice_id_here"
```

### 3. Add Function Calling
You can extend the bot to call external functions by modifying the LLM configuration and adding function definitions.

### 4. Adjust Voice Activity Detection
Modify VAD sensitivity by changing `stop_secs`:
```python
VADParams(stop_secs=0.5)  # Longer pause before stopping
```

### 5. Add Memory/Context
The bot currently uses basic conversation context. You can extend this by:
- Adding conversation history persistence
- Implementing user session management
- Adding external knowledge bases

## Development Workflow

### 1. Local Development
```bash
# Install dependencies
uv sync

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Run the bot
uv run bot.py
```

### 2. Testing Changes
- Open http://localhost:7860 in your browser
- Click "Connect" to test your bot
- Make changes to `bot.py` and restart to see updates

### 3. Deployment
```bash
# Build and push Docker image
uv run pcc docker build-push

# Deploy to Pipecat Cloud
uv run pcc deploy
```

## API Keys Required

1. **Deepgram**: Speech-to-Text
   - Sign up: https://console.deepgram.com/signup
   - Get API key from dashboard

2. **OpenAI**: Language Model
   - Sign up: https://auth.openai.com/create-account
   - Get API key from API settings

3. **Cartesia**: Text-to-Speech
   - Sign up: https://play.cartesia.ai/sign-up
   - Get API key from dashboard

## Troubleshooting

### Common Issues
1. **Import errors**: Make sure all dependencies are installed with `uv sync`
2. **API key errors**: Check that all required API keys are set in `.env`
3. **Audio issues**: Ensure microphone permissions are granted in browser
4. **Connection issues**: Try different browsers or check firewall settings

### Debug Mode
Add logging to see what's happening:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps for Customization

1. **Add specialized knowledge**: Integrate with external APIs or databases
2. **Implement user authentication**: Add user management and personalization
3. **Add multimodal capabilities**: Integrate vision or document processing
4. **Create custom processors**: Build specialized pipeline components
5. **Add analytics**: Track usage and performance metrics
