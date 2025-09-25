#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Customized Pipecat Bot Template.

This is a template for customizing your Pipecat bot. Copy this file and modify
the configuration sections below to create your own specialized voice AI bot.

Required AI services:
- Deepgram (Speech-to-Text)
- OpenAI (LLM)
- Cartesia (Text-to-Speech)

Run the bot using::

    uv run bot_custom.py
"""

import os

from dotenv import load_dotenv
from loguru import logger

print("🚀 Starting Custom Pipecat bot...")
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
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)

# =============================================================================
# CUSTOMIZATION SECTION - Modify these values to customize your bot
# =============================================================================

# Bot Configuration
BOT_NAME = "Custom Assistant"
BOT_PERSONALITY = """You are a helpful and knowledgeable AI assistant. 
You speak in a friendly, conversational tone and provide clear, accurate information.
Keep your responses concise but informative."""

# Voice Configuration (Browse voices at: https://play.cartesia.ai/)
VOICE_ID = "71a7ad14-091c-4e8e-a314-022ece01c121"  # British Reading Lady
# Alternative voices:
# "a0e99841-438c-4a64-b679-ae501e7d6091"  # Barbershop Man
# "79a125e8-cd45-4c13-8a67-188112f4dd22"  # Child
# "87748186-23bb-4158-a1eb-332911b0b708"  # Newsman

# Audio Configuration
VAD_STOP_SECONDS = 0.2  # How long to wait before stopping speech detection
ENABLE_METRICS = True   # Enable performance metrics
ENABLE_USAGE_METRICS = True  # Enable usage tracking

# Greeting Configuration
CUSTOM_GREETING = f"Hello! I'm {BOT_NAME}, your AI assistant. How can I help you today?"

# =============================================================================
# END CUSTOMIZATION SECTION
# =============================================================================


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting {BOT_NAME}")

    # Initialize services with API keys
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=VOICE_ID,
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Set up conversation context with custom personality
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
            stt,  # Speech-to-Text
            context_aggregator.user(),  # User responses
            llm,  # Large Language Model
            tts,  # Text-to-Speech
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
    """Main bot entry point for the custom bot."""

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
