#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Pipecat Bot with Cartesia STT/TTS and OpenAI (Temporary).

This bot uses:
- Cartesia for Speech-to-Text (STT)
- Cartesia for Text-to-Speech (TTS)  
- OpenAI for LLM (temporary while OpenRouter is being fixed)

Required API services:
- Cartesia (STT and TTS)
- OpenAI (LLM)

Run the bot using::

    uv run bot_cartesia_openai.py
"""

import os

from dotenv import load_dotenv
from loguru import logger

print("🚀 Starting Cartesia + OpenAI Pipecat bot...")
print("⏳ Loading models and imports (20 seconds, first run only)\n")

logger.info("Loading Local Smart Turn Analyzer V3...")
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

logger.info("✅ Local Smart Turn Analyzer V3 loaded")
logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

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

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)

# =============================================================================
# CONFIGURATION SECTION - Modify these values to customize your bot
# =============================================================================

# Bot Configuration
BOT_NAME = "Cartesia + OpenAI Assistant"
BOT_PERSONALITY = """You are a helpful and knowledgeable AI assistant. 
You speak in a friendly, conversational tone and provide clear, accurate information.
Keep your responses concise but informative, and feel free to ask clarifying questions."""

# OpenAI Model
OPENAI_MODEL = "gpt-4o-mini"  # Cost-effective and fast
# Alternative models:
# "gpt-4o"          # Most capable
# "gpt-3.5-turbo"   # Most cost-effective

# Voice Configuration (Browse voices at: https://play.cartesia.ai/)
VOICE_ID = "71a7ad14-091c-4e8e-a314-022ece01c121"  # British Reading Lady

# Audio Configuration
VAD_STOP_SECONDS = 0.2  # How long to wait before stopping speech detection
ENABLE_METRICS = True   # Enable performance metrics
ENABLE_USAGE_METRICS = True  # Enable usage tracking

# Cartesia STT Configuration
STT_LANGUAGE = "en"  # Language for speech recognition
STT_MODEL = "sonic-english"  # Cartesia STT model

# Greeting Configuration
CUSTOM_GREETING = f"Hello! I'm {BOT_NAME}, powered by Cartesia's voice technology and OpenAI. How can I help you today?"

# =============================================================================
# END CONFIGURATION SECTION
# =============================================================================


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting {BOT_NAME}")

    # Initialize Cartesia STT service
    stt = CartesiaSTTService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        language=STT_LANGUAGE,
        model=STT_MODEL,
    )

    # Initialize Cartesia TTS service
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=VOICE_ID,
    )

    # Initialize OpenAI LLM
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=OPENAI_MODEL,
    )

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
            transport.input(),  # Transport user input
            rtvi,  # RTVI processor
            stt,  # Cartesia Speech-to-Text
            context_aggregator.user(),  # User responses
            llm,  # OpenAI LLM
            tts,  # Cartesia Text-to-Speech
            transport.output(),  # Transport bot output
            context_aggregator.assistant(),  # Assistant spoken responses
        ]
    )

    # Create the pipeline task with custom configuration
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
        # Start the conversation with custom greeting
        messages.append({"role": "system", "content": f"Say: '{CUSTOM_GREETING}'"})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected from {BOT_NAME}")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the Cartesia + OpenAI bot."""

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=VAD_STOP_SECONDS)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=VAD_STOP_SECONDS)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
