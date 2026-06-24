import json
import os
import re
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

_PROJECT_ROOT = Path(__file__).parent.parent

CONFLUENCE_BASE  = "https://sibmee.atlassian.net/wiki/rest/api"
CONFLUENCE_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN")
CONFLUENCE_EMAIL = os.environ.get("CONFLUENCE_EMAIL")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def _read_dir(directory: Path, pattern: str = "*.md") -> list[str]:
    """Return file contents for every file matching pattern in directory."""
    if not directory.exists():
        return []
    return [f.read_text(encoding="utf-8") for f in sorted(directory.glob(pattern))]


def _read_dir_rich(directory: Path, pattern: str = "*.md") -> list[dict]:
    """Return dicts with filename + content for every matching file."""
    if not directory.exists():
        return []
    return [
        {"filename": f.name, "content": f.read_text(encoding="utf-8")}
        for f in sorted(directory.glob(pattern))
    ]


def _fetch_confluence(page_id: str) -> str | None:
    """Fetch and strip a Confluence page. Returns None on any error."""
    if not CONFLUENCE_TOKEN:
        return None
    try:
        resp = requests.get(
            f"{CONFLUENCE_BASE}/content/{page_id}?expand=body.storage",
            auth=(CONFLUENCE_EMAIL, CONFLUENCE_TOKEN),
            timeout=10,
        )
        resp.raise_for_status()
        return _strip_html(resp.json()["body"]["storage"]["value"])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="get_user_stories",
            description="Get all manual user stories",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_bug_reports",
            description="Get reported bugs",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_docs",
            description=(
                "Get business-logic docs for a feature area. "
                "Docs live in context_server/docs/ and capture rules, "
                "constraints, and domain knowledge that are not user stories or bugs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "feature": {
                        "type": "string",
                        "description": "Feature name (e.g. 'huddles', 'copilot', 'library')",
                    }
                },
                "required": ["feature"],
            },
        ),
        types.Tool(
            name="get_confluence_page",
            description="Fetch a Confluence page by ID",
            inputSchema={
                "type": "object",
                "properties": {"page_id": {"type": "string"}},
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="get_all_context",
            description=(
                "Get unified context for a feature area: "
                "user stories + bugs + business-logic docs + optional Confluence page."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "feature": {"type": "string"},
                    "confluence_page_id": {
                        "type": "string",
                        "description": "Optional Confluence page ID to pull spec from.",
                    },
                },
                "required": ["feature"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict):

    # ── get_user_stories ────────────────────────────────────────────────────
    if name == "get_user_stories":
        stories = _read_dir(_PROJECT_ROOT / "context_server/stories")
        return [types.TextContent(
            type="text",
            text=json.dumps({"stories": stories, "count": len(stories)}),
        )]

    # ── get_bug_reports ─────────────────────────────────────────────────────
    if name == "get_bug_reports":
        bugs = _read_dir(_PROJECT_ROOT / "context_server/bugs")
        return [types.TextContent(
            type="text",
            text=json.dumps({"bugs": bugs, "count": len(bugs)}),
        )]

    # ── get_docs ─────────────────────────────────────────────────────────────
    if name == "get_docs":
        feature = arguments["feature"]
        docs = _read_dir_rich(_PROJECT_ROOT / "context_server/docs", pattern=f"*{feature}*.md")
        return [types.TextContent(
            type="text",
            text=json.dumps({"feature": feature, "docs": docs, "count": len(docs)}),
        )]

    # ── get_confluence_page ──────────────────────────────────────────────────
    if name == "get_confluence_page":
        page_id = arguments["page_id"]
        if not CONFLUENCE_TOKEN:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "CONFLUENCE_API_TOKEN not set", "page_id": page_id}),
            )]
        content = _fetch_confluence(page_id)
        if content is None:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "Failed to fetch page", "page_id": page_id}),
            )]
        return [types.TextContent(
            type="text",
            text=json.dumps({"page_id": page_id, "content": content}),
        )]

    # ── get_all_context ──────────────────────────────────────────────────────
    if name == "get_all_context":
        feature           = arguments["feature"]
        confluence_page_id = arguments.get("confluence_page_id")

        stories = _read_dir(_PROJECT_ROOT / "context_server/stories", pattern=f"*{feature}*.md")
        bugs    = _read_dir(_PROJECT_ROOT / "context_server/bugs",    pattern=f"*{feature}*.md")
        docs    = _read_dir_rich(_PROJECT_ROOT / "context_server/docs", pattern=f"*{feature}*.md")

        confluence_content = (
            _fetch_confluence(confluence_page_id) if confluence_page_id else None
        )

        merged = {
            "feature":    feature,
            "stories":    stories,
            "bugs":       bugs,
            "docs":       docs,
            "confluence": confluence_content,
            "context_sources": {
                "stories":    len(stories),
                "bugs":       len(bugs),
                "docs":       len(docs),
                "confluence": "yes" if confluence_content else "not available",
            },
        }
        return [types.TextContent(type="text", text=json.dumps(merged))]

    # ── unknown ──────────────────────────────────────────────────────────────
    return [types.TextContent(
        type="text",
        text=json.dumps({"error": f"Unknown tool: {name}"}),
    )]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())