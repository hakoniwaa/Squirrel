"""
Anthropic Integration - Clean wrapper without monkey-patching

RECOMMENDED: Use LiteLLM instead for unified API and native callback support.
This integration is provided for direct Anthropic SDK usage.

Usage:
    from memori.integrations.anthropic_integration import MemoriAnthropic

    # Initialize with your memori instance
    client = MemoriAnthropic(memori_instance, api_key="your-key")

    # Use exactly like Anthropic client
    response = client.messages.create(...)
"""

from loguru import logger


class MemoriAnthropic:
    """
    Clean Anthropic wrapper that automatically records conversations
    without monkey-patching. Drop-in replacement for Anthropic client.
    """

    def __init__(self, memori_instance, api_key: str | None = None, **kwargs):
        """
        Initialize MemoriAnthropic wrapper

        Args:
            memori_instance: Memori instance for recording conversations
            api_key: Anthropic API key
            **kwargs: Additional arguments passed to Anthropic client
        """
        try:
            import anthropic

            self._anthropic = anthropic.Anthropic(api_key=api_key, **kwargs)
            self._memori = memori_instance

            # Create wrapped messages
            self.messages = self._create_messages_wrapper()

            # Pass through other attributes
            for attr in dir(self._anthropic):
                if not attr.startswith("_") and attr not in ["messages"]:
                    setattr(self, attr, getattr(self._anthropic, attr))

        except ImportError as err:
            raise ImportError(
                "Anthropic package required: pip install anthropic"
            ) from err

    def _create_messages_wrapper(self):
        """Create wrapped messages"""

        class MessagesWrapper:
            def __init__(self, anthropic_client, memori_instance):
                self._anthropic = anthropic_client
                self._memori = memori_instance

            def create(self, **kwargs):
                # Inject context if conscious ingestion is enabled
                if self._memori.is_enabled and self._memori.conscious_ingest:
                    kwargs = self._inject_context(kwargs)

                # Make the actual API call
                response = self._anthropic.messages.create(**kwargs)

                # Record conversation if memori is enabled
                if self._memori.is_enabled:
                    self._record_conversation(kwargs, response)

                return response

            def _inject_context(self, kwargs):
                """Inject relevant context into messages"""
                try:
                    # Extract user input from messages
                    user_input = ""
                    for msg in reversed(kwargs.get("messages", [])):
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            if isinstance(content, list):
                                # Handle content blocks
                                user_input = " ".join(
                                    [
                                        block.get("text", "")
                                        for block in content
                                        if isinstance(block, dict)
                                        and block.get("type") == "text"
                                    ]
                                )
                            else:
                                user_input = content
                            break

                    if user_input:
                        # Fetch relevant context
                        context = self._memori.retrieve_context(user_input, limit=3)

                        if context:
                            # Create a context prompt
                            context_prompt = "--- Relevant Memories ---\n"
                            for mem in context:
                                if isinstance(mem, dict):
                                    summary = mem.get("summary", "") or mem.get(
                                        "content", ""
                                    )
                                    context_prompt += f"- {summary}\n"
                                else:
                                    context_prompt += f"- {str(mem)}\n"
                            context_prompt += "-------------------------\n"

                            # Inject context into the system parameter
                            if kwargs.get("system"):
                                # Prepend to existing system message
                                kwargs["system"] = context_prompt + kwargs["system"]
                            else:
                                # Add as system message
                                kwargs["system"] = context_prompt

                            logger.debug(f"Injected context: {len(context)} memories")
                except Exception as e:
                    logger.error(f"Context injection failed: {e}")

                return kwargs

            def _record_conversation(self, kwargs, response):
                """Record the conversation"""
                try:
                    # Extract details
                    messages = kwargs.get("messages", [])
                    model = kwargs.get("model", "claude-unknown")

                    # Find user input (last user message)
                    user_input = ""
                    for message in reversed(messages):
                        if message.get("role") == "user":
                            content = message.get("content", "")
                            if isinstance(content, list):
                                # Handle content blocks
                                user_input = " ".join(
                                    [
                                        block.get("text", "")
                                        for block in content
                                        if isinstance(block, dict)
                                        and block.get("type") == "text"
                                    ]
                                )
                            else:
                                user_input = content
                            break

                    # Extract AI response
                    ai_output = ""
                    if hasattr(response, "content") and response.content:
                        if isinstance(response.content, list):
                            # Handle content blocks
                            ai_output = " ".join(
                                [
                                    block.text
                                    for block in response.content
                                    if hasattr(block, "text")
                                ]
                            )
                        else:
                            ai_output = str(response.content)

                    # Calculate tokens used
                    tokens_used = 0
                    if hasattr(response, "usage") and response.usage:
                        input_tokens = getattr(response.usage, "input_tokens", 0)
                        output_tokens = getattr(response.usage, "output_tokens", 0)
                        tokens_used = input_tokens + output_tokens

                    # Record conversation
                    self._memori.record_conversation(
                        user_input=user_input,
                        ai_output=ai_output,
                        model=model,
                        metadata={
                            "integration": "anthropic_wrapper",
                            "api_type": "messages",
                            "tokens_used": tokens_used,
                            "auto_recorded": True,
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to record Anthropic conversation: {e}")

        return MessagesWrapper(self._anthropic, self._memori)
