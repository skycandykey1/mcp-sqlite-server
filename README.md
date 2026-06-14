# MCP Server for SQLite (read-only) — safe SQL for your AI agent

[![tests](https://github.com/yourhandle/mcp-sqlite-server/actions/workflows/ci.yml/badge.svg)](https://github.com/yourhandle/mcp-sqlite-server/actions)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-8A2BE2)](https://modelcontextprotocol.io)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A small, production-minded **MCP server** (Model Context Protocol) that gives an AI agent —
Claude Desktop, Claude Code, or any MCP client — **safe, read-only SQL access** to a SQLite
database. Point it at a `.db` file and the agent can explore schemas and run `SELECT` queries —
**but never write, drop, or escape the database.**

> Built on the official MCP Python SDK (`FastMCP`). The read-only safety core has **zero MCP
> dependency** and is unit-tested on its own — the server is a thin, auditable wrapper.

## Why read-only matters

Handing an LLM a raw database connection is how you get a `DROP TABLE` in production. This server
enforces read-only at **two independent layers**:

1. **OS-level** — the connection is opened with SQLite `?mode=ro` + `PRAGMA query_only`, so any
   write fails at the engine.
2. **Statement-level** — `query` rejects anything that isn't a single `SELECT`/`WITH` (no
   multi-statements, no `INSERT`/`UPDATE`/`DELETE`/`DROP`/`PRAGMA` writes), and caps row counts.

Defense in depth: even if one layer is bypassed, the other still holds. (There's a test that proves it.)

## What the agent gets (all 3 MCP primitives)

| Primitive | Name | Does |
|-----------|------|------|
| 🔧 tool | `list_tables` | List the tables in the database |
| 🔧 tool | `describe_table` | Column schema (name, type, nullability, PK) |
| 🔧 tool | `query` | Run a single read-only `SELECT`/`WITH`, capped at `max_rows` |
| 📄 resource | `schema://tables` | The whole DB schema as text |
| 💬 prompt | `explore_database` | A ready-made "explore this DB" prompt |

## Quick start (≈ 1 minute)

```bash
git clone https://github.com/yourhandle/mcp-sqlite-server
cd mcp-sqlite-server
pip install -r requirements.txt

# make a sample DB to play with
python examples/make_sample_db.py

# inspect it live in the MCP dev inspector
SQLITE_DB_PATH=examples/sample.db mcp dev mcp_sqlite/server.py
# ...or run the server directly
SQLITE_DB_PATH=examples/sample.db python -m mcp_sqlite.server
```

## Use it from Claude Desktop

Add this to your Claude Desktop config (**Settings → Developer → Edit Config**), using absolute paths —
see [`examples/claude_desktop_config.example.json`](examples/claude_desktop_config.example.json):

```json
{
  "mcpServers": {
    "sqlite-readonly": {
      "command": "python",
      "args": ["-m", "mcp_sqlite.server"],
      "cwd": "/absolute/path/to/mcp-sqlite-server",
      "env": { "SQLITE_DB_PATH": "/absolute/path/to/your.db" }
    }
  }
}
```

Restart Claude Desktop, then ask: *"What tables are in my database? Show me the top 5 orders by amount."*

## How it fits together

```
  MCP client (Claude Desktop / Claude Code)
            │  MCP over stdio
            ▼
  mcp_sqlite/server.py   ← thin FastMCP wrapper (tools / resource / prompt)
            │
            ▼
  mcp_sqlite/db.py       ← read-only core (no MCP dep, fully unit-tested)
            │  ?mode=ro + query_only + SELECT-only guard
            ▼
        your .db  (read-only)
```

## Run the tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q       # offline — no MCP client, no API key needed
```

## License

MIT — see [LICENSE](LICENSE).

---

> 💼 **Built by `Ten Cua May` — available for AI agent & automation contract work.**
> I build agents, MCP servers, and LLM automation. → `you@example.com` · `https://calendly.com/you/intro`

<!-- After publishing (SEO):
     About: "Read-only SQLite MCP server (Model Context Protocol) — safe SQL access for AI agents"
     Topics (≥5): mcp, mcp-server, model-context-protocol, sqlite, claude, anthropic, ai-agent, python
     Add a social preview image. Pin this repo on your profile, next to ai-agent-starter. -->
