"""Quick test for the memory extraction pipeline."""

import asyncio

from sqrl.ipc.handlers import handle_process_episode


async def main():
    """Test the pipeline with a sample episode."""
    params = {
        "project_id": "test-project",
        "project_root": "/home/lyrica/projects/test-project",
        "events": [
            {
                "ts": "2024-12-10T10:00:00Z",
                "role": "user",
                "content_summary": "asked to call Stripe API using requests",
            },
            {
                "ts": "2024-12-10T10:01:00Z",
                "role": "assistant",
                "content_summary": "wrote code using requests library",
            },
            {
                "ts": "2024-12-10T10:01:30Z",
                "role": "tool_error",
                "content_summary": "SSLError: certificate verify failed",
            },
            {
                "ts": "2024-12-10T10:02:00Z",
                "role": "user",
                "content_summary": "said: just use httpx instead, requests always has SSL issues",
            },
            {
                "ts": "2024-12-10T10:03:00Z",
                "role": "assistant",
                "content_summary": "rewrote code using httpx, API call succeeded",
            },
        ],
        "existing_user_styles": [
            {"id": "style-1", "text": "Prefer async/await over callbacks"},
        ],
        "existing_project_memories": [],
    }

    print("Testing pipeline...")
    print(f"Input: {len(params['events'])} events")
    print()

    result = await handle_process_episode(params)

    print("Result:")
    print(f"  skipped: {result['skipped']}")
    if result.get("skip_reason"):
        print(f"  skip_reason: {result['skip_reason']}")
    print(f"  user_styles: {result['user_styles']}")
    print(f"  project_memories: {result['project_memories']}")


if __name__ == "__main__":
    asyncio.run(main())
