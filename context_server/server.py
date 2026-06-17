import json
import os
import requests
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Load .env from the project root (two levels up from this file)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

server = Server("context-server")

CONFLUENCE_BASE = "https://sibmee.atlassian.net/wiki/rest/api"
CONFLUENCE_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN")
CONFLUENCE_EMAIL = os.environ.get("CONFLUENCE_EMAIL")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(name="get_user_stories",    description="Get all manual user stories", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="get_bug_reports",     description="Get reported bugs", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="get_confluence_page", description="Fetch a Confluence page by ID",
                   inputSchema={"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}),
        types.Tool(name="get_all_context",     description="Get unified context for a feature area",
                   inputSchema={"type": "object", "properties": {"feature": {"type": "string"}}, "required": ["feature"]}),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_user_stories":
        stories = [f.read_text() for f in Path("context_server/stories").glob("*.md")]
        return [types.TextContent(type="text", text=json.dumps({"stories": stories, "count": len(stories)}))]

    if name == "get_bug_reports":
        bugs_dir = Path("context_server/bugs")
        bugs = [f.read_text() for f in bugs_dir.glob("*.md")] if bugs_dir.exists() else []
        return [types.TextContent(type="text", text=json.dumps({"bugs": bugs, "count": len(bugs)}))]

    if name == "get_confluence_page":
        page_id = arguments["page_id"]
        if not CONFLUENCE_TOKEN:
            return [types.TextContent(type="text", text=json.dumps({
                "error": "CONFLUENCE_API_TOKEN not set", "page_id": page_id
            }))]
        try:
            resp = requests.get(
                f"{CONFLUENCE_BASE}/content/{page_id}?expand=body.storage",
                auth=(CONFLUENCE_EMAIL, CONFLUENCE_TOKEN),
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            import re
            content = re.sub(r"<[^>]+>", " ", data["body"]["storage"]["value"])
            return [types.TextContent(type="text", text=json.dumps({"page_id": page_id, "content": content}))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e), "page_id": page_id}))]

    if name == "get_all_context":
        feature = arguments["feature"]
        confluence_page_id = arguments.get("confluence_page_id")  # optional

        # Always load local files
        stories = [f.read_text() for f in Path("context_server/stories").glob(f"*{feature}*.md")]
        bugs = [f.read_text() for f in Path("context_server/bugs").glob(f"*{feature}*.md")]

        confluence_content = None

        # Only attempt Confluence if a page ID was passed AND token exists
        if confluence_page_id and CONFLUENCE_TOKEN:
            try:
                resp = requests.get(
                    f"{CONFLUENCE_BASE}/content/{confluence_page_id}?expand=body.storage",
                    auth=(CONFLUENCE_EMAIL, CONFLUENCE_TOKEN),
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                import re
                confluence_content = re.sub(r"<[^>]+>", " ", data["body"]["storage"]["value"])
            except Exception as e:
                confluence_content = None  # silently skip, don't crash

        merged = {
            "feature": feature,
            "stories": stories,
            "bugs": bugs,
            "confluence": confluence_content,  # None if not provided or failed
            "context_sources": {
                "stories": len(stories),
                "bugs": len(bugs),
                "confluence": "yes" if confluence_content else "not available"
            }
        }

        return [types.TextContent(type="text", text=json.dumps(merged))]

    return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

async def main():
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())