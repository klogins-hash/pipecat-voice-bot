#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Production Pipecat Bot for Railway Deployment.

This bot is optimized for production deployment on Railway with:
- Environment variable configuration
- Health check endpoint
- Graceful shutdown handling
- Production logging
- Automatic bot selection based on available API keys

Run the bot using::

    uv run bot_production.py
"""

import os
import sys
import signal
import asyncio
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

# Configure production logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

print("🚀 Starting Production Pipecat Bot...")
print("⏳ Loading models and imports (v3)...")

logger.info("Loading basic components...")
try:
    from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
    logger.info("✅ Local Smart Turn Analyzer V3 loaded")
except Exception as e:
    logger.warning(f"Could not load Smart Turn Analyzer: {e}")
    LocalSmartTurnAnalyzerV3 = None

try:
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    logger.info("✅ Silero VAD model loaded")
except Exception as e:
    logger.warning(f"Could not load Silero VAD: {e}")
    SileroVADAnalyzer = None

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame

logger.info("Loading pipeline components...")
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.cartesia.stt import CartesiaSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

# Try to import custom Cohere service
try:
    from cohere_llm_service import CohereLLMService
    COHERE_AVAILABLE = True
except ImportError:
    logger.warning("Cohere LLM service not available")
    COHERE_AVAILABLE = False

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)

# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

# Bot Configuration
BOT_NAME = "Production Voice AI Assistant"
BOT_PERSONALITY = """You are a professional AI assistant deployed in production. 
You speak clearly and concisely, providing helpful and accurate information.
You are having a voice conversation, so keep responses natural and conversational.
Be professional but friendly in your interactions."""

# Model Selection (based on available API keys)
def select_llm_service() -> tuple[str, any]:
    """Select the best available LLM service based on API keys."""
    
    openai_key = os.getenv("OPENAI_API_KEY")
    cohere_key = os.getenv("COHERE_API_KEY")
    
    if openai_key and openai_key != "your_openai_api_key":
        logger.info("Using OpenAI GPT-4o-mini for LLM")
        return "OpenAI", OpenAILLMService(
            api_key=openai_key,
            model="gpt-4o-mini",
        )
    elif cohere_key and cohere_key != "your_cohere_api_key" and COHERE_AVAILABLE:
        logger.info("Using Cohere Command R+ for LLM")
        return "Cohere", CohereLLMService(
            api_key=cohere_key,
            model="command-r-plus-08-2024",
            params=CohereLLMService.InputParams(
                temperature=0.7,
                max_tokens=1000,
                p=0.9,
            )
        )
    else:
        logger.error("No valid LLM API key found!")
        sys.exit(1)

# Voice Configuration
VOICE_ID = "71a7ad14-091c-4e8e-a314-022ece01c121"  # British Reading Lady

# Audio Configuration
VAD_STOP_SECONDS = 0.3  # Slightly longer for production stability
ENABLE_METRICS = True
ENABLE_USAGE_METRICS = True

# Cartesia Configuration
STT_LANGUAGE = "en"
STT_MODEL = "sonic-english"

# Production Settings
PORT = int(os.getenv("PORT", "8080"))  # Railway default port
HOST = "0.0.0.0"  # Listen on all interfaces for Railway

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

async def health_check_handler(request):
    """Simple health check endpoint for Railway."""
    return {"status": "healthy", "bot": BOT_NAME}

# =============================================================================
# BOT IMPLEMENTATION
# =============================================================================

async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting {BOT_NAME}")

    # Validate Cartesia API key
    cartesia_key = os.getenv("CARTESIA_API_KEY")
    if not cartesia_key or cartesia_key == "your_cartesia_api_key":
        logger.error("CARTESIA_API_KEY not configured!")
        sys.exit(1)

    # Initialize Cartesia services
    stt = CartesiaSTTService(
        api_key=cartesia_key,
        language=STT_LANGUAGE,
        model=STT_MODEL,
    )

    tts = CartesiaTTSService(
        api_key=cartesia_key,
        voice_id=VOICE_ID,
    )

    # Select and initialize LLM service
    llm_name, llm = select_llm_service()
    
    # Create greeting message
    greeting = f"Hello! I'm {BOT_NAME}, powered by Cartesia's voice technology and {llm_name}. How can I help you today?"

    # Set up conversation context
    messages = [
        {
            "role": "system",
            "content": BOT_PERSONALITY,
        },
    ]

    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Build the processing pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    # Create the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=ENABLE_METRICS,
            enable_usage_metrics=ENABLE_USAGE_METRICS,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected to {BOT_NAME}")
        messages.append({"role": "system", "content": f"Say: '{greeting}'"})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected from {BOT_NAME}")
        await task.cancel()

    # Graceful shutdown handling
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(task.cancel())

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    try:
        await runner.run(task)
    except Exception as e:
        logger.exception(f"Error running bot: {e}")
        raise


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for production deployment."""

    # Create VAD and turn analyzer if available
    vad_analyzer = None
    turn_analyzer = None
    
    if SileroVADAnalyzer:
        try:
            vad_analyzer = SileroVADAnalyzer(params=VADParams(stop_secs=VAD_STOP_SECONDS))
        except Exception as e:
            logger.warning(f"Could not create VAD analyzer: {e}")
    
    if LocalSmartTurnAnalyzerV3:
        try:
            turn_analyzer = LocalSmartTurnAnalyzerV3()
        except Exception as e:
            logger.warning(f"Could not create turn analyzer: {e}")

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=vad_analyzer,
            turn_analyzer=turn_analyzer,
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=vad_analyzer,
            turn_analyzer=turn_analyzer,
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    logger.info(f"🎯 Production bot starting on {HOST}:{PORT}")
    logger.info(f"🔑 Cartesia API key: {'✅ Configured' if os.getenv('CARTESIA_API_KEY') else '❌ Missing'}")
    logger.info(f"🔑 OpenAI API key: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    logger.info(f"🔑 Cohere API key: {'✅ Configured' if os.getenv('COHERE_API_KEY') else '❌ Missing'}")
    
    # Set the port for Pipecat to use
    import sys
    sys.argv.extend(["--port", str(PORT), "--host", HOST])
    
    from pipecat.runner.run import main
    main()
