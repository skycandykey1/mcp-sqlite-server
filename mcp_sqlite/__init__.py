"""mcp-sqlite-server — a read-only SQLite MCP server."""
# NB: do not import .server here — it pulls in the `mcp` package. Keeping __init__
# light lets the safety-critical db module be imported/tested without it.
__version__ = "0.1.0"
