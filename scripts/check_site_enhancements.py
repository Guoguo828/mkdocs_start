#!/usr/bin/env python3
"""Small source checks for the local MkDocs theme enhancements."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    config = read("mkdocs.yml")
    sync_script = read("scripts/sync_notes.py")
    comments = read("overrides/partials/comments.html")
    css = read("docs/assets/stylesheets/extra.css")
    js_path = ROOT / "docs/assets/javascripts/site.js"

    # ── 基础引用 ──
    assert '"assets/javascripts/site.js"' in config
    assert '"assets/javascripts/site.js"' in sync_script
    assert "site-like" in comments
    assert "aria-pressed" in comments
    assert "isLocalPreview" in comments
    assert ".site-like" in css
    assert ".md-header__topic,\n.md-tabs__link" not in css
    assert ".md-header__ellipsis {\n  overflow: hidden;" in css
    assert js_path.exists()

    js = js_path.read_text(encoding="utf-8")

    # ── 点赞功能 ──
    assert "initLikeButton" in js
    assert "localStorage" in js
    assert "document$" in js

    for group in ("计算机系统", "程序设计与算法", "理论与数据库", "研究与专题"):
        assert f'{group}.md' in config
        assert (ROOT / f"docs/{group}.md").exists()

    # ── 阅读进度条 ──
    assert "reading-progress" in css
    assert "initReadingProgress" in js

    # ── 键盘快捷键 ──
    assert "initKeyboardShortcuts" in js

    # ── 404 页面 ──
    assert (ROOT / "docs/404.md").exists(), "404.md not found"
    assert "site-404" in css

    # ── GitHub Actions 工作流 ──
    assert (ROOT / ".github/workflows/deploy.yml").exists(), "deploy.yml not found"

    # ── 打印样式 ──
    assert "@media print" in css

    # ── 图片增强 ──
    assert ".md-typeset img" in css

    # ── 社交链接 ──
    assert "social:" in config

    # ── requirements.txt ──
    assert (ROOT / "requirements.txt").exists(), "requirements.txt not found"

    print("[OK] All enhancement checks passed.")


if __name__ == "__main__":
    main()
