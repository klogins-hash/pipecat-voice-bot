#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Custom Cohere LLM service implementation for Pipecat.

This module provides a direct integration with Cohere's API, allowing you to use
Cohere Command R models directly without going through OpenRouter or other proxies.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import cohere
from loguru import logger
from pydantic import BaseModel, Field

from pipecat.frames.frames import (
    Frame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesFrame,
    LLMTextFrame,
    LLMUpdateSettingsFrame,
)
from pipecat.metrics.metrics import LLMTokenUsage
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantAggregatorParams,
    LLMAssistantContextAggregator,
    LLMUserAggregatorParams,
    LLMUserContextAggregator,
)
from pipecat.utils.tracing.service_decorators import traced_llm


class CohereLLMService(LLMService):
    """Cohere LLM service implementation.
    
    Provides direct integration with Cohere's API for Command R models.
    Supports streaming responses and conversation context management.
    """

    class InputParams(BaseModel):
        """Input parameters for Cohere model configuration.
        
        Parameters:
            temperature: Controls randomness (0.0 to 1.0).
            max_tokens: Maximum tokens in response.
            k: Top-k sampling parameter.
            p: Top-p (nucleus) sampling parameter.
            frequency_penalty: Penalty for frequent tokens.
            presence_penalty: Penalty for new tokens.
            stop_sequences: List of strings that stop generation.
        """
        
        temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
        max_tokens: Optional[int] = Field(default=1000, ge=1)
        k: Optional[int] = Field(default=0, ge=0)
        p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
        frequency_penalty: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
        presence_penalty: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
        stop_sequences: Optional[List[str]] = Field(default_factory=list)

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "command-r-plus-08-2024",
        params: Optional[InputParams] = None,
        **kwargs,
    ):
        """Initialize the Cohere LLM service.
        
        Args:
            api_key: Cohere API key.
            model: The Cohere model name to use.
            params: Input parameters for model configuration.
            **kwargs: Additional arguments passed to the parent LLMService.
        """
        super().__init__(**kwargs)
        
        self._api_key = api_key
        self._model = model
        self._client = cohere.AsyncClientV2(api_key=api_key)
        
        params = params or self.InputParams()
        self._settings = {
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
            "k": params.k,
            "p": params.p,
            "frequency_penalty": params.frequency_penalty,
            "presence_penalty": params.presence_penalty,
            "stop_sequences": params.stop_sequences,
        }
        
        self.set_model_name(model)

    def can_generate_metrics(self) -> bool:
        """Check if the service can generate metrics.
        
        Returns:
            True if metrics can be generated.
        """
        return True

    async def _convert_context_to_cohere_messages(self, context: LLMContext) -> List[Dict[str, Any]]:
        """Convert LLMContext messages to Cohere format.
        
        Args:
            context: The LLM context containing conversation history.
            
        Returns:
            List of messages in Cohere format.
        """
        messages = []
        system_message = None
        
        for message in context.messages:
            if isinstance(message, dict):
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if not content:  # Skip empty messages
                    continue
                
                # Handle system message separately
                if role == "system":
                    system_message = content
                elif role == "user":
                    messages.append({
                        "role": "user", 
                        "content": content
                    })
                elif role == "assistant":
                    messages.append({
                        "role": "assistant",
                        "content": content
                    })
        
        # If we have a system message and user messages, prepend system to first user message
        if system_message and messages and messages[0]["role"] == "user":
            messages[0]["content"] = f"{system_message}\n\nUser: {messages[0]['content']}"
        elif system_message and not messages:
            # If only system message, create a user message
            messages.append({
                "role": "user",
                "content": system_message
            })
        
        return messages

    @traced_llm
    async def _process_context(self, context: LLMContext):
        """Process the LLM context and generate a response.
        
        Args:
            context: The LLM context containing conversation history.
        """
        await self.start_llm_usage_metrics(self._model)

        try:
            logger.debug(f"Generating chat: {context.messages}")
            
            # Convert context to Cohere messages
            messages = await self._convert_context_to_cohere_messages(context)
            
            if not messages:
                logger.warning("No messages to process")
                return

            # Prepare the request parameters
            request_params = {
                "model": self._model,
                "messages": messages,
                "stream": True,
                **{k: v for k, v in self._settings.items() if v is not None and v != []}
            }
            
            # Remove None values and empty lists
            request_params = {k: v for k, v in request_params.items() if v is not None}
            
            logger.debug(f"Cohere request params: {request_params}")

            await self.push_frame(LLMFullResponseStartFrame())

            # Make the streaming request to Cohere
            response_stream = await self._client.chat_stream(**request_params)
            
            full_response = ""
            
            async for event in response_stream:
                try:
                    if hasattr(event, 'type'):
                        if event.type == "content-delta":
                            if hasattr(event, 'delta') and hasattr(event.delta, 'message'):
                                if hasattr(event.delta.message, 'content') and hasattr(event.delta.message.content, 'text'):
                                    text = event.delta.message.content.text
                                    if text:
                                        full_response += text
                                        await self.push_frame(LLMTextFrame(text))
                        
                        elif event.type == "stream-end":
                            # Handle usage metrics if available
                            if hasattr(event, 'response') and hasattr(event.response, 'usage'):
                                usage = event.response.usage
                                tokens_used = LLMTokenUsage(
                                    prompt_tokens=getattr(usage, 'input_tokens', 0),
                                    completion_tokens=getattr(usage, 'output_tokens', 0),
                                    total_tokens=getattr(usage, 'input_tokens', 0) + getattr(usage, 'output_tokens', 0)
                                )
                                await self.start_llm_usage_metrics(self._model, tokens_used)
                except Exception as stream_error:
                    logger.warning(f"Error processing stream event: {stream_error}")
                    continue

            await self.push_frame(LLMFullResponseEndFrame())
            
            logger.debug(f"Cohere response: {full_response}")

        except Exception as e:
            logger.exception(f"Exception in Cohere LLM: {e}")
            # Push an error frame or handle the error appropriately
            await self.push_frame(LLMTextFrame(f"Error: {str(e)}"))
            await self.push_frame(LLMFullResponseEndFrame())
        finally:
            await self.stop_llm_usage_metrics()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process incoming frames.
        
        Args:
            frame: The frame to process.
            direction: The direction of frame processing.
        """
        await super().process_frame(frame, direction)

        context = None
        if isinstance(frame, OpenAILLMContextFrame):
            context = frame.context
        elif isinstance(frame, LLMContextFrame):
            context = frame.context
        elif isinstance(frame, LLMMessagesFrame):
            context = LLMContext.from_messages(frame.messages)
        elif isinstance(frame, LLMUpdateSettingsFrame):
            await self._update_settings(frame.settings)
            return

        if context:
            await self._process_context(context)

    async def _update_settings(self, settings: Dict[str, Any]):
        """Update model settings.
        
        Args:
            settings: Dictionary of settings to update.
        """
        logger.debug(f"Updating Cohere settings: {settings}")
        for key, value in settings.items():
            if key in self._settings:
                self._settings[key] = value

    async def run_inference(self, context: LLMContext) -> Optional[str]:
        """Run a one-shot inference with the given context.
        
        Args:
            context: The LLM context containing conversation history.
            
        Returns:
            The LLM's response as a string, or None if no response is generated.
        """
        try:
            messages = await self._convert_context_to_cohere_messages(context)
            
            if not messages:
                return None

            request_params = {
                "model": self._model,
                "messages": messages,
                "stream": False,
                **{k: v for k, v in self._settings.items() if v is not None and v != []}
            }
            
            response = await self._client.chat(**request_params)
            
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                if hasattr(response.message.content[0], 'text'):
                    return response.message.content[0].text
            
            return None
            
        except Exception as e:
            logger.exception(f"Exception in Cohere run_inference: {e}")
            return None

    def create_context_aggregator(
        self,
        context: LLMContext,
        *,
        user_params: LLMUserAggregatorParams = LLMUserAggregatorParams(),
        assistant_params: LLMAssistantAggregatorParams = LLMAssistantAggregatorParams(),
    ):
        """Create context aggregators for managing conversation context.
        
        Args:
            context: The LLM context to create aggregators for.
            user_params: Parameters for user message aggregation.
            assistant_params: Parameters for assistant message aggregation.
            
        Returns:
            A pair of context aggregators.
        """
        user = LLMUserContextAggregator(context, params=user_params)
        assistant = LLMAssistantContextAggregator(user, params=assistant_params)
        return {"user": user, "assistant": assistant}
