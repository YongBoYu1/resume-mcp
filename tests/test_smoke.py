"""Smoke tests for resume-mcp public tools (live HTTP against public site)."""

from __future__ import annotations

import json

import pytest

from resume_mcp import cache as cache_mod
from resume_mcp.server import (
    get_resume_summary,
    list_projects,
    search_evidence,
    who_is_yongbo_yu,
)


@pytest.fixture(autouse=True)
def reset_cache():
    cache_mod.cache.resume = None
    cache_mod.cache.llms_text = None
    cache_mod.cache.fetched_at = None
    cache_mod.cache.errors = []
    yield


def test_who_is_yongbo_yu_includes_sources():
    data = json.loads(who_is_yongbo_yu())
    assert "YongBo" in data["name"]
    assert "sources" in data
    assert any("yongbo-yu.vercel.app" in u for u in data["sources"])
    assert data["canonical_links"]["kilodock"].endswith("/projects/kilodock")


def test_list_projects_includes_kilodock():
    data = json.loads(list_projects())
    names = [p["name"] for p in data["projects"]]
    assert "KiloDock" in names
    kilodock = next(p for p in data["projects"] if p["name"] == "KiloDock")
    assert kilodock["url"] == "https://yongbo-yu.vercel.app/projects/kilodock"
    assert any(u.endswith("/resume.json") for u in data["sources"])


def test_get_resume_summary_has_work_and_skills():
    data = json.loads(get_resume_summary())
    assert data["work"]
    assert data["education"]
    assert data["skills"]
    assert "https://yongbo-yu.vercel.app/resume.json" in data["sources"]


def test_search_evidence_finds_kilodock():
    data = json.loads(search_evidence("KiloDock gym"))
    assert data["match_count"] >= 1
    assert any("KiloDock" in m["snippet"] or "kilodock" in m["snippet"].lower() for m in data["matches"])
    assert all("source" in m for m in data["matches"])
    assert data["sources"]
