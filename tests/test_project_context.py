"""Tests for utils.project_context.

Covers the pure-function paths: project lookup, fuzzy normalization, context
build with a synthetic project directory, and the in-memory cache.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from utils import project_context as pc


def test_known_projects_includes_expected_set() -> None:
    """Every project listed in PROJECT_PATHS must surface via known_projects()."""
    names = set(pc.known_projects())
    assert {"jobs-os", "mmt-os", "yos", "portfolio", "_workspace-os"} <= names


def test_project_path_returns_path_for_known_project() -> None:
    p = pc.project_path("jobs-os")
    assert p is not None
    assert p.name == "Jobs-OS"


def test_project_path_returns_none_for_unknown() -> None:
    assert pc.project_path("does-not-exist") is None


def test_unknown_project_returns_warning_context() -> None:
    """Building context for a non-existent project should not raise; should warn."""
    pc.invalidate_cache()
    ctx = pc.load_project_context("totally-fake-project")
    assert "not found" in ctx.lower() or "failed" in ctx.lower()


def test_build_with_synthetic_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject a fake project under PROJECT_PATHS and confirm the loader assembles
    CLAUDE.md + learnings.md into the system prompt."""
    fake = tmp_path / "fake-os"
    fake.mkdir()
    (fake / "CLAUDE.md").write_text("# fake instructions\nuse the test framework")
    (fake / "memory").mkdir()
    (fake / "memory" / "learnings.md").write_text("- be careful with X")

    monkeypatch.setitem(pc.PROJECT_PATHS, "fake-os", fake)
    pc.invalidate_cache("fake-os")

    ctx = pc.load_project_context("fake-os")
    assert "# Active project: fake-os" in ctx
    assert "fake instructions" in ctx
    assert "be careful with X" in ctx


def test_cache_returns_same_object_within_ttl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two calls inside the TTL window must hit the cache (same object identity)."""
    fake = tmp_path / "cache-os"
    fake.mkdir()
    (fake / "CLAUDE.md").write_text("v1")
    monkeypatch.setitem(pc.PROJECT_PATHS, "cache-os", fake)
    pc.invalidate_cache("cache-os")

    a = pc.load_project_context("cache-os")
    (fake / "CLAUDE.md").write_text("v2")  # mutate after first load
    b = pc.load_project_context("cache-os")
    assert a is b  # cache hit — v2 not seen until invalidate or TTL expiry

    pc.invalidate_cache("cache-os")
    c = pc.load_project_context("cache-os")
    assert "v2" in c


def test_truncation_keeps_head_and_tail(tmp_path: Path) -> None:
    """_read_truncated must preserve start + end when content exceeds budget."""
    f = tmp_path / "long.md"
    f.write_text("A" * 10_000 + "ZTAIL")
    out = pc._read_truncated(f, 1000)
    assert out.startswith("AAAA")
    assert out.endswith("ZTAIL")
    assert "truncated" in out
