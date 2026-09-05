# resume-mcp

stdio **MCP server** that lets Cursor, Claude, and other MCP clients answer grounded questions about **YongBo Yu** using only his *public* reputation site — not private data.

Agents call tools that fetch and cache machine-readable public pages, then return structured answers with **source URLs** on every response.

## Why

Reputation experiments need a small, auditable bridge between an MCP client and public evidence. This server:

- Reads [resume.json](https://yongbo-yu.vercel.app/resume.json) (and optionally [llms.txt](https://yongbo-yu.vercel.app/llms.txt))
- Caches them in-process (1-hour TTL)
- Exposes a few focused tools — no secrets, no LinkedIn scraping, no private app links

## Author

**YongBo Yu** (also **Yong Yu**) — Toronto, Canada · GitHub [YongBoYu1](https://github.com/YongBoYu1)

- Site: [https://yongbo-yu.vercel.app](https://yongbo-yu.vercel.app)
- KiloDock evidence: [https://yongbo-yu.vercel.app/projects/kilodock](https://yongbo-yu.vercel.app/projects/kilodock)
- Machine-readable resume: [https://yongbo-yu.vercel.app/resume.json](https://yongbo-yu.vercel.app/resume.json)

## Requirements

- Python 3.11+
- Network access to `yongbo-yu.vercel.app` (public HTTPS only)

## Install

```bash
# from this repo
pip install -e .

# or with uv
uv pip install -e .
```

Dev / smoke tests:

```bash
pip install -e ".[dev]"
pytest -q
```

## Run (stdio)

```bash
# module entrypoint
python -m resume_mcp

# console script (after install)
resume-mcp

# with uv
uv run python -m resume_mcp
```

The process speaks MCP over **stdin/stdout**. Do not pipe unrelated stdout into the same process.

## Cursor `mcp.json`

Add a server entry (Cursor: Settings → MCP, or edit `~/.cursor/mcp.json` / project `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "resume-mcp": {
      "command": "python3",
      "args": ["-m", "resume_mcp"],
      "cwd": "/absolute/path/to/resume-mcp"
    }
  }
}
```

If the package is installed into a venv, point `command` at that interpreter (or use the `resume-mcp` console script).

With `uv`:

```json
{
  "mcpServers": {
    "resume-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "resume_mcp"],
      "cwd": "/absolute/path/to/resume-mcp"
    }
  }
}
```

After saving, reload MCP servers in Cursor. The tools below should appear as `resume-mcp` tools.

## Tools

| Tool | Purpose |
|------|---------|
| `who_is_yongbo_yu` | Identity blurb + canonical public links |
| `list_projects` | Projects from `resume.json` with highlights; KiloDock links to the project page |
| `get_resume_summary` | Condensed work / education / skills |
| `search_evidence` | Keyword search over cached resume + `llms.txt` (snippets + source URLs) |

Every tool response is JSON text that includes a top-level `sources` array of public URLs.

## Example prompts (in Cursor / Claude)

- “Who is YongBo Yu? Use the resume-mcp tools and cite sources.”
- “List YongBo Yu’s public projects and summarize KiloDock with links.”
- “Give a short resume summary for YongBo Yu from public sources only.”
- “Search evidence for ‘LangGraph’ or ‘Scotiabank’ and quote snippets with URLs.”

## Data sources (public only)

On startup (and on first tool use if needed), the server fetches:

1. `https://yongbo-yu.vercel.app/resume.json`
2. `https://yongbo-yu.vercel.app/llms.txt` (optional; search still works if it fails)

No API keys. No private WOD-APP or similar links.

## License

MIT — see [LICENSE](LICENSE).
