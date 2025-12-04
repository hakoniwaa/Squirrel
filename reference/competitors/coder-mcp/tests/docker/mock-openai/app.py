import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock OpenAI API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
RESPONSE_DELAY = float(os.getenv("RESPONSE_DELAY", "0"))
RESPONSES_DIR = Path("/app/responses")


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "text-embedding-ada-002"
    encoding_format: str = "float"


class CompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class MockResponses:
    """Manage mock responses."""

    def __init__(self, responses_dir: Path):
        self.responses_dir = responses_dir
        self.responses = self._load_responses()
        self.call_history = []

    def _load_responses(self) -> Dict[str, Any]:
        """Load predefined responses from JSON files."""
        responses = {}

        if not self.responses_dir.exists():
            return responses

        for file_path in self.responses_dir.glob("*.json"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    responses[file_path.stem] = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.error("Failed to load %s: %s", file_path, e)

        return responses

    def get_embedding_response(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """Generate embedding response."""
        # Record the call
        self.call_history.append(
            {
                "type": "embedding",
                "request": request.dict(),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Handle single or batch input
        inputs = request.input if isinstance(request.input, list) else [request.input]

        # Generate deterministic embeddings based on input
        embeddings = []
        for i, text in enumerate(inputs):
            # Create a deterministic embedding based on text content
            seed = sum(ord(c) for c in text) + i
            np.random.seed(seed)
            embedding = np.random.randn(3072).tolist()  # Ada-002 dimension

            embeddings.append({"object": "embedding", "embedding": embedding, "index": i})

        return {
            "object": "list",
            "data": embeddings,
            "model": request.model,
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in inputs),
                "total_tokens": sum(len(text.split()) for text in inputs),
            },
        }

    def get_completion_response(self, request: CompletionRequest) -> Dict[str, Any]:
        """Generate completion response."""
        # Record the call
        self.call_history.append(
            {
                "type": "completion",
                "request": request.dict(),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Check for predefined responses
        last_message = request.messages[-1]["content"] if request.messages else ""

        # Look for matching predefined response
        for key, response_data in self.responses.get("completions", {}).items():
            if key in last_message:
                return response_data

        # Generate default response
        response_text = self._generate_default_response(request.messages)

        return {
            "id": f"chatcmpl-mock-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": sum(len(msg["content"].split()) for msg in request.messages),
                "completion_tokens": len(response_text.split()),
                "total_tokens": sum(len(msg["content"].split()) for msg in request.messages)
                + len(response_text.split()),
            },
        }

    def _generate_default_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a default response based on the input."""
        last_message = messages[-1]["content"] if messages else ""

        # Simple pattern matching for common test scenarios
        if "analyze" in last_message.lower():
            return (
                "Analysis complete. The code appears to be well-structured "
                "with good error handling."
            )
        elif "refactor" in last_message.lower():
            return "Here's the refactored version with improved readability and performance."
        elif "test" in last_message.lower():
            return "Test case generated successfully. All edge cases are covered."
        elif "error" in last_message.lower():
            return "Error detected: Invalid syntax at line 42."
        else:
            return "I understand your request. Here's a helpful response for testing purposes."


# Initialize mock responses
mock_responses = MockResponses(RESPONSES_DIR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """Mock embeddings endpoint."""
    # Simulate network delay
    if RESPONSE_DELAY > 0:
        await asyncio.sleep(RESPONSE_DELAY)

    try:
        response = mock_responses.get_embedding_response(request)
        return Response(content=json.dumps(response), media_type="application/json")
    except Exception as e:
        logger.error("Error generating embedding response: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/chat/completions")
async def create_completion(request: CompletionRequest):
    """Mock chat completions endpoint."""
    # Simulate network delay
    if RESPONSE_DELAY > 0:
        await asyncio.sleep(RESPONSE_DELAY)

    try:
        if request.stream:
            # Return streaming response
            return create_streaming_response(request)
        else:
            response = mock_responses.get_completion_response(request)
            return Response(content=json.dumps(response), media_type="application/json")
    except Exception as e:
        logger.error("Error generating completion response: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_streaming_response(request: CompletionRequest):
    """Create a streaming response."""

    async def generate():
        response_text = mock_responses._generate_default_response(request.messages)
        words = response_text.split()

        # Send initial chunk
        initial_chunk = {"choices": [{"delta": {"role": "assistant"}}]}
        yield f"data: {json.dumps(initial_chunk)}\n\n"

        # Stream words
        for word in words:
            content_str = word + " "
            delta_dict = {"content": content_str}
            choice_dict = {"delta": delta_dict, "index": 0}
            chunk = {"choices": [choice_dict]}
            chunk_json = json.dumps(chunk)
            data_str = f"data: {chunk_json}\n\n"
            yield data_str
            await asyncio.sleep(0.01)  # Small delay between words

        # Send done signal
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": "text-embedding-ada-002",
                "object": "model",
                "created": 1677649358,
                "owned_by": "openai",
            },
            {"id": "gpt-3.5-turbo", "object": "model", "created": 1677649358, "owned_by": "openai"},
            {"id": "gpt-4", "object": "model", "created": 1677649358, "owned_by": "openai"},
        ],
    }


@app.get("/test/history")
async def get_call_history():
    """Get history of API calls for testing."""
    return {
        "total_calls": len(mock_responses.call_history),
        "history": mock_responses.call_history[-100:],  # Last 100 calls
    }


@app.post("/test/reset")
async def reset_history():
    """Reset call history."""
    mock_responses.call_history = []
    return {"message": "History reset successfully"}


@app.post("/test/set-response")
async def set_custom_response(endpoint: str, key: str, response: Dict[str, Any]):
    """Set a custom response for testing."""
    if endpoint not in mock_responses.responses:
        mock_responses.responses[endpoint] = {}

    mock_responses.responses[endpoint][key] = response
    return {"message": f"Custom response set for {endpoint}/{key}"}


# Error simulation endpoints
@app.post("/test/simulate-error")
async def simulate_error(error_type: str = "rate_limit", duration_seconds: int = 60):
    """Simulate various error conditions."""
    # This would be used to test error handling
    return {"message": f"Simulating {error_type} for {duration_seconds} seconds"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
