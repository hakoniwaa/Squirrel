"""PROMPT-002: Memory Extractor agent."""

import json
import os

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from sqrl.models.episode import ExistingProjectMemory, ExistingUserStyle
from sqrl.models.extraction import ExtractorOutput

SYSTEM_PROMPT = """You are the Memory Extractor for Squirrel, a coding memory system.

You receive corrections where a user corrected the AI. Your job: classify each correction.

## Two Types of Memories

### 1. User Styles (Global Preferences)
Preferences that apply to ALL projects. Synced to agent.md files automatically.

Examples:
- "never use emoji"
- "prefer async/await over callbacks"
- "be concise, no lengthy explanations"
- "always use TypeScript, not JavaScript"

Signals that indicate User Style:
- User says "always", "never", "I prefer", "I hate"
- User corrects AI behavior/communication style
- Applies regardless of project

### 2. Project Memories (Project-Specific AI Mistakes)
Mistakes the AI made in THIS specific project. User triggers via MCP when needed.

Examples:
- "use httpx not requests (SSL issues in this environment)"
- "this API needs timeout set to 30s"
- "tests must run with --no-cache flag"

Signals that indicate Project Memory:
- Technical issue specific to this codebase/environment
- User corrects AI's technical choice for this project
- Would NOT apply to other projects

## Decision Flow
1. Did user correct AI? (already filtered by Log Cleaner)
2. Is this about user's general preference? → User Style
3. Is this about this project's technical specifics? → Project Memory
4. Not sure? → Project Memory (safer default)

## Operations

| Op | When to Use |
|----|-------------|
| ADD | New correction not in existing memories |
| UPDATE | Correction modifies existing memory (provide target_id) |
| DELETE | Existing memory is now wrong (provide target_id) |

## Output Format (JSON only)

{
  "user_styles": [
    { "op": "ADD", "text": "preference description" },
    { "op": "UPDATE", "target_id": "id", "text": "updated preference" },
    { "op": "DELETE", "target_id": "id" }
  ],
  "project_memories": [
    { "op": "ADD", "category": "frontend|backend|docs_test|other", "text": "..." },
    { "op": "UPDATE", "target_id": "id", "text": "updated memory" },
    { "op": "DELETE", "target_id": "id" }
  ]
}

If the correction doesn't warrant a memory, return empty arrays:
{
  "user_styles": [],
  "project_memories": [],
  "skip_reason": "why no memory needed"
}"""


def _get_model() -> OpenAIModel:
    """Get model configured for OpenRouter."""
    model_name = os.getenv("SQRL_STRONG_MODEL", "google/gemini-2.0-flash-001")
    api_key = os.getenv("OPENROUTER_API_KEY")
    provider = OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return OpenAIModel(model_name, provider=provider)


class MemoryExtractor:
    """Memory Extractor agent using PydanticAI."""

    def __init__(self) -> None:
        self.agent = Agent(
            model=_get_model(),
            system_prompt=SYSTEM_PROMPT,
            output_type=ExtractorOutput,
            retries=3,
        )

    async def extract(
        self,
        project_id: str,
        project_root: str,
        correction_context: str,
        existing_user_styles: list[ExistingUserStyle],
        existing_project_memories: list[ExistingProjectMemory],
    ) -> ExtractorOutput:
        """Extract memories from user correction."""
        styles_json = json.dumps(
            [{"id": s.id, "text": s.text} for s in existing_user_styles],
            indent=2,
        )
        memories_json = json.dumps(
            [
                {
                    "id": m.id,
                    "category": m.category,
                    "subcategory": m.subcategory,
                    "text": m.text,
                }
                for m in existing_project_memories
            ],
            indent=2,
        )

        user_prompt = f"""PROJECT: {project_id}
PROJECT ROOT: {project_root}

EXISTING USER STYLES:
{styles_json}

EXISTING PROJECT MEMORIES:
{memories_json}

USER CORRECTION:
{correction_context}

Classify this correction. Return JSON only."""

        result = await self.agent.run(user_prompt)
        return result.output
