# resume-mcp

## Problem

Agents invent bios and career claims without citations. When you ask an MCP client who someone is or what they shipped, you often get fluent prose and no way to verify it.

## Solution

A **stdio MCP server** that:

1. Fetches public machine-readable pages (`resume.json`, optionally `llms.txt`)
2. Caches them in-process (1-hour TTL)
3. Exposes tools that return structured answers with a top-level `sources[]` of public URLs on every response

No secrets, no LinkedIn scraping, no private app links — only HTTPS to the wired public corpus.

The default dataset is [YongBo Yu’s public site](https://yongbo-yu.vercel.app) (`resume.json` / `llms.txt`). The pattern is general: point the same fetch/cache/source-URL shape at any public machine-readable resume corpus.

## Requirements

- Python 3.11+
- Network access to the wired public host (default: `yongbo-yu.vercel.app`)

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
| `who_is_yongbo_yu` | Identity blurb + canonical public links from the wired corpus |
| `list_projects` | Projects from `resume.json` with highlights; KiloDock links to the project page |
| `get_resume_summary` | Condensed work / education / skills |
| `search_evidence` | Keyword search over cached resume + `llms.txt` (snippets + source URLs) |

Every tool response is JSON text that includes a top-level `sources` array of public URLs.

## Example prompts (in Cursor / Claude)

- “Summarize the public resume this MCP is wired to, with sources.”
- “List projects from the cached resume.json and cite the source URLs.”
- “Search the wired public corpus for ‘LangGraph’ and quote snippets with URLs.”
- “Use `who_is_yongbo_yu` for the identity blurb + links from this corpus (not invented bio text).”

## Data sources (public only)

On startup (and on first tool use if needed), the server fetches:

1. `https://yongbo-yu.vercel.app/resume.json`
2. `https://yongbo-yu.vercel.app/llms.txt` (optional; search still works if it fails)

No API keys. No private WOD-APP or similar links.

## Author

**YongBo Yu** (also **Yong Yu**) — Toronto, Canada · GitHub [YongBoYu1](https://github.com/YongBoYu1)

- Site: [https://yongbo-yu.vercel.app](https://yongbo-yu.vercel.app)
- KiloDock evidence: [https://yongbo-yu.vercel.app/projects/kilodock](https://yongbo-yu.vercel.app/projects/kilodock)
- Machine-readable resume: [https://yongbo-yu.vercel.app/resume.json](https://yongbo-yu.vercel.app/resume.json)

## License

MIT — see [LICENSE](LICENSE).
