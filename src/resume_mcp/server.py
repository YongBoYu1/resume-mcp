"""stdio MCP server exposing YongBo Yu public resume evidence tools."""

from __future__ import annotations

import json
import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from resume_mcp.cache import (
    ABOUT_URL,
    GITHUB_URL,
    KILODOCK_URL,
    LLMS_TXT_URL,
    RESUME_URL,
    SITE_URL,
    cache,
    flatten_resume_text,
)

mcp = FastMCP(
    "resume-mcp",
    instructions=(
        "Answer questions about YongBo Yu (also Yong Yu), a Toronto AI engineer, "
        "using only his public reputation site data. Always cite the source URLs "
        "returned by each tool. Do not invent private employment or unpublished links."
    ),
)


def _sources(*urls: str) -> list[str]:
    seen: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.append(url)
    return seen


def _payload(data: dict[str, Any], *urls: str) -> str:
    body = {**data, "sources": _sources(*urls)}
    return json.dumps(body, ensure_ascii=False, indent=2)


def _github_from_resume(resume: dict[str, Any]) -> str:
    profiles = (resume.get("basics") or {}).get("profiles") or []
    for profile in profiles:
        if str(profile.get("network", "")).lower() == "github" and profile.get("url"):
            return str(profile["url"])
    return GITHUB_URL


def _project_url(project: dict[str, Any]) -> str | None:
    name = str(project.get("name") or "")
    url = project.get("url")
    if url:
        return str(url)
    if name.lower() == "kilodock":
        return KILODOCK_URL
    return None


@mcp.tool()
def who_is_yongbo_yu() -> str:
    """Identity blurb and canonical public links for YongBo Yu (also Yong Yu)."""
    resume = cache.require_resume()
    basics = resume.get("basics") or {}
    location = basics.get("location") or {}
    loc_parts = [
        location.get("city"),
        location.get("region"),
        location.get("countryCode"),
    ]
    location_str = ", ".join(p for p in loc_parts if p) or "Toronto, Canada"

    return _payload(
        {
            "name": basics.get("name") or "YongBo Yu",
            "also_known_as": ["Yong Yu"],
            "label": basics.get("label"),
            "summary": basics.get("summary"),
            "location": location_str,
            "github": _github_from_resume(resume),
            "canonical_links": {
                "site": SITE_URL,
                "about": ABOUT_URL,
                "kilodock": KILODOCK_URL,
                "resume_json": RESUME_URL,
                "llms_txt": LLMS_TXT_URL,
                "github": _github_from_resume(resume),
            },
            "cache_notes": cache.errors or None,
        },
        SITE_URL,
        ABOUT_URL,
        RESUME_URL,
        KILODOCK_URL,
        LLMS_TXT_URL,
        _github_from_resume(resume),
    )


@mcp.tool()
def list_projects() -> str:
    """List projects from public resume.json with highlights; KiloDock links to its project page."""
    resume = cache.require_resume()
    projects_out: list[dict[str, Any]] = []
    source_urls = [RESUME_URL]

    for project in resume.get("projects") or []:
        url = _project_url(project)
        item = {
            "name": project.get("name"),
            "description": project.get("description"),
            "startDate": project.get("startDate"),
            "endDate": project.get("endDate"),
            "highlights": project.get("highlights") or [],
            "url": url,
        }
        projects_out.append(item)
        if url:
            source_urls.append(url)

    # Always surface KiloDock evidence page even if missing from JSON.
    names = {str(p.get("name") or "").lower() for p in projects_out}
    if "kilodock" not in names:
        projects_out.insert(
            0,
            {
                "name": "KiloDock",
                "description": "CrossFit gym operating system (demo) — see project page.",
                "highlights": [],
                "url": KILODOCK_URL,
            },
        )
        source_urls.append(KILODOCK_URL)
    elif KILODOCK_URL not in source_urls:
        source_urls.append(KILODOCK_URL)

    return _payload(
        {
            "projects": projects_out,
            "cache_notes": cache.errors or None,
        },
        *source_urls,
    )


@mcp.tool()
def get_resume_summary() -> str:
    """Condensed work experience, education, and skills from public resume.json."""
    resume = cache.require_resume()
    basics = resume.get("basics") or {}

    work = []
    for job in resume.get("work") or []:
        work.append(
            {
                "name": job.get("name"),
                "position": job.get("position"),
                "startDate": job.get("startDate"),
                "endDate": job.get("endDate"),
                "summary": job.get("summary"),
                "highlights": (job.get("highlights") or [])[:3],
            }
        )

    education = []
    for edu in resume.get("education") or []:
        education.append(
            {
                "institution": edu.get("institution"),
                "studyType": edu.get("studyType"),
                "area": edu.get("area"),
                "startDate": edu.get("startDate"),
                "endDate": edu.get("endDate"),
                "score": edu.get("score"),
            }
        )

    skills = []
    for skill in resume.get("skills") or []:
        skills.append(
            {
                "name": skill.get("name"),
                "keywords": skill.get("keywords") or [],
            }
        )

    return _payload(
        {
            "name": basics.get("name") or "YongBo Yu",
            "label": basics.get("label"),
            "summary": basics.get("summary"),
            "work": work,
            "education": education,
            "skills": skills,
            "certificates": resume.get("certificates") or [],
            "cache_notes": cache.errors or None,
        },
        RESUME_URL,
        SITE_URL,
    )


@mcp.tool()
def search_evidence(query: str, limit: int = 8) -> str:
    """Keyword search over cached resume.json and llms.txt; returns snippets with source URLs."""
    if not query or not query.strip():
        return _payload(
            {"query": query, "matches": [], "error": "query must be a non-empty string"},
            RESUME_URL,
            LLMS_TXT_URL,
        )

    cache.ensure_loaded()
    limit = max(1, min(int(limit), 25))
    tokens = [t for t in re.split(r"\s+", query.strip().lower()) if t]
    matches: list[dict[str, Any]] = []

    def score_line(line: str) -> int:
        lower = line.lower()
        return sum(1 for t in tokens if t in lower)

    # Search resume as line-oriented JSON text.
    if cache.resume is not None:
        for line in flatten_resume_text(cache.resume).splitlines():
            stripped = line.strip().rstrip(",")
            if len(stripped) < 8:
                continue
            s = score_line(stripped)
            if s:
                matches.append(
                    {
                        "score": s,
                        "snippet": stripped[:400],
                        "source": RESUME_URL,
                    }
                )

    # Search llms.txt paragraphs / bullets.
    if cache.llms_text:
        for block in re.split(r"\n\s*\n", cache.llms_text):
            snippet = " ".join(block.split())
            if len(snippet) < 8:
                continue
            s = score_line(snippet)
            if s:
                matches.append(
                    {
                        "score": s,
                        "snippet": snippet[:400],
                        "source": LLMS_TXT_URL,
                    }
                )

    matches.sort(key=lambda m: (-m["score"], m["source"], m["snippet"]))
    # Deduplicate near-identical snippets.
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in matches:
        key = f"{match['source']}|{match['snippet'][:120]}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)
        if len(deduped) >= limit:
            break

    source_urls = [RESUME_URL]
    if cache.llms_text is not None:
        source_urls.append(LLMS_TXT_URL)
    for match in deduped:
        if match["source"] not in source_urls:
            source_urls.append(match["source"])

    return _payload(
        {
            "query": query,
            "match_count": len(deduped),
            "matches": deduped,
            "cache_notes": cache.errors or None,
        },
        *source_urls,
    )


def main() -> None:
    """Run the MCP server over stdio (default FastMCP transport)."""
    # Warm cache so the first tool call is fast; failures are retained for tool notes.
    try:
        cache.ensure_loaded()
    except Exception:  # noqa: BLE001
        pass
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
