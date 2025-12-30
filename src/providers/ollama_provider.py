from typing import Any, AsyncIterator, Optional, Dict, List, Union
import json
import asyncio
import logging

from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, ToolCall

from src.config import settings
from src.core.exceptions import LLMProviderError
from src.core.interfaces import ILLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(ILLMProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.timeout = timeout or settings.LLM_TIMEOUT  # Timeout in seconds (default: 600s / 10 min)

        self.llm = ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
        )

    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        model: Optional[str] = None,
        use_gpu: bool = True,
        **kwargs: Any
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate response with optional tool calling support.
        
        Args:
            prompt: User message
            system_prompt: System instructions
            tools: Optional list of tool definitions in OpenAI format
            model: Optional model override (defaults to instance model)
            use_gpu: Enable/disable GPU acceleration (default: True)
            
        Returns:
            str if text response, Dict with tool_call if model wants to use a tool
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use specified model or fallback to instance default
            llm = self.llm
            active_model = self.model
            
            # Always create new instance with explicit num_gpu
            # IMPORTANT: After setting num_gpu=0, you MUST set num_gpu=999 to re-enable GPU
            # Cannot just omit the parameter - Ollama maintains state
            num_gpu = 999 if use_gpu else 0
            llm = ChatOllama(
                base_url=self.base_url,
                model=model if model else self.model,
                temperature=self.temperature,
                num_gpu=num_gpu,
            )
            if model and model != self.model:
                logger.info(f"🔄 Model override: {model} (default: {self.model})")
                active_model = model
            
            # Log which model is being used
            gpu_status = "🟢 GPU" if use_gpu else "🔵 CPU"
            if tools:
                logger.info(f"🤖 Using model: {active_model} | Tools: {len(tools)} available | {gpu_status} | Timeout: {self.timeout}s")
                llm = llm.bind_tools(tools)
            else:
                logger.info(f"🤖 Using model: {active_model} | No tools | {gpu_status} | Timeout: {self.timeout}s")

            # Add timeout to prevent hanging
            try:
                response: AIMessage = await asyncio.wait_for(
                    llm.ainvoke(messages),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"⏱️ LLM call timed out after {self.timeout}s")
                raise LLMProviderError(f"LLM call timed out after {self.timeout} seconds. Try a simpler query or increase timeout.")
            
            # Check if response contains tool calls
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                logger.info(f"✅ LLM returned tool call: {tool_call['name']}")
                return {
                    "type": "tool_call",
                    "tool_name": tool_call["name"],
                    "tool_args": tool_call["args"],
                    "tool_call_id": tool_call.get("id", "call_" + tool_call["name"])
                }
            
            logger.info("✅ LLM returned text response")
            return response.content

        except asyncio.TimeoutError:
            raise  # Re-raise timeout errors
        except Exception as e:
            logger.error(f"❌ LLM error: {str(e)}")
            raise LLMProviderError(f"Error generating response: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        model: Optional[str] = None,
        use_gpu: bool = True,
        **kwargs: Any
    ) -> AsyncIterator[Union[str, Dict[str, Any]]]:
        """
        Stream response with optional tool calling support.
        
        Args:
            prompt: User message
            system_prompt: System instructions
            tools: Optional list of tool definitions in OpenAI format
            model: Optional model override (defaults to instance model)
            use_gpu: Enable/disable GPU acceleration (default: True)
            
        Yields:
            str chunks for text, or Dict with tool_call when complete
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Use specified model or fallback to instance default
            llm = self.llm
            active_model = self.model
            
            # Always create new instance with explicit num_gpu
            # IMPORTANT: After setting num_gpu=0, you MUST set num_gpu=999 to re-enable GPU
            # Cannot just omit the parameter - Ollama maintains state
            num_gpu = 999 if use_gpu else 0
            llm = ChatOllama(
                base_url=self.base_url,
                model=model if model else self.model,
                temperature=self.temperature,
                num_gpu=num_gpu,
            )
            if model and model != self.model:
                logger.info(f"🔄 Model override for streaming: {model} (default: {self.model})")
                active_model = model
            
            # Log which model is being used
            gpu_status = "🟢 GPU" if use_gpu else "🔵 CPU"
            if tools:
                logger.info(f"🤖 Streaming model: {active_model} | Tools: {len(tools)} | {gpu_status} | Timeout: {self.timeout}s")
                llm = llm.bind_tools(tools)
            else:
                logger.info(f"🤖 Streaming model: {active_model} | No tools | {gpu_status} | Timeout: {self.timeout}s")

            tool_call_data = None
            stream = llm.astream(messages)
            start_time = asyncio.get_event_loop().time()
            
            try:
                while True:
                    # Check timeout on each iteration
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > self.timeout:
                        logger.error(f"⏱️ Streaming LLM call timed out after {self.timeout}s")
                        yield {"type": "error", "message": f"Response timed out after {self.timeout} seconds"}
                        break
                    
                    # Get next chunk with remaining timeout
                    remaining_timeout = self.timeout - elapsed
                    try:
                        chunk = await asyncio.wait_for(stream.__anext__(), timeout=remaining_timeout)
                    except StopAsyncIteration:
                        break
                    except asyncio.TimeoutError:
                        logger.error(f"⏱️ Streaming LLM call timed out after {self.timeout}s")
                        yield {"type": "error", "message": f"Response timed out after {self.timeout} seconds"}
                        break
                    
                    # Check for tool calls in chunk
                    if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                        tool_call = chunk.tool_calls[0]
                        tool_call_data = {
                            "type": "tool_call",
                            "tool_name": tool_call["name"],
                            "tool_args": tool_call["args"],
                            "tool_call_id": tool_call.get("id", "call_" + tool_call["name"])
                        }
                        logger.info(f"✅ Streaming detected tool call: {tool_call['name']}")
                    elif hasattr(chunk, "content") and chunk.content:
                        yield chunk.content
            
                # If tool call was detected, yield it at the end
                if tool_call_data:
                    yield tool_call_data

            except asyncio.TimeoutError:
                logger.error(f"⏱️ Streaming timeout")
                yield {"type": "error", "message": f"Response timed out after {self.timeout} seconds"}
            except Exception as e:
                logger.error(f"❌ Streaming error: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"❌ Streaming error: {str(e)}")
            raise LLMProviderError(f"Error streaming response: {str(e)}")
