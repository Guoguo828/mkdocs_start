#!/usr/bin/env python3
"""Sync selected markdown note folders into the MkDocs site.

This script copies source notes from ../../markdown into docs/, generates
landing pages for each category, rewrites the site homepage, and rebuilds
mkdocs.yml navigation so the site stays aligned with the local note folders.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Category:
    slug: str
    title: str
    group: str
    icon: str
    description: str


CATEGORIES: list[Category] = [
    Category("计组", "计算机组成", "计算机系统", ":material-cpu-64-bit:", "围绕 CPU、流水线、存储层次和 I/O 的课程笔记。"),
    Category("体系结构", "计算机体系结构", "计算机系统", ":material-chip:", "偏体系结构和高级处理器设计的课程整理。"),
    Category("sl", "数字逻辑", "计算机系统", ":material-vector-intersection:", "数字逻辑课程笔记，覆盖组合逻辑、时序逻辑和存储器。"),
    Category("H265", "H.265 编码", "计算机系统", ":material-video:", "H.265/HEVC 相关概述、预测、量化和熵编码笔记。"),
    Category("oop", "面向对象编程", "程序设计与算法", ":material-language-cpp:", "C++ 与 OOP 课程笔记，覆盖类、继承、多态、模板和 STL。"),
    Category("fds", "数据结构基础", "程序设计与算法", ":material-graph:", "树、堆、并查集、图、排序、哈希等数据结构笔记。"),
    Category("ads", "高级数据结构与算法", "程序设计与算法", ":material-source-branch:", "AVL、红黑树、回溯、分治、动态规划、随机化与近似算法。"),
    Category("数据库", "数据库", "理论与数据库", ":material-database:", "数据库系统导论、关系模型、SQL、设计范式、索引与查询处理。"),
    Category("ls", "离散数学", "理论与数据库", ":material-set-all:", "逻辑、集合、计数、关系、图论与树的课程笔记。"),
    Category("论文笔记", "论文笔记", "研究与专题", ":material-file-document-multiple:", "论文阅读记录、解读和阶段性整理。"),
    Category("alphafold2", "AlphaFold2", "研究与专题", ":material-dna:", "AlphaFold2 学习笔记与相关图示材料。"),
    Category("形策", "形势与政策", "研究与专题", ":material-newspaper-variant-outline:", "形策课程整理、复习提纲与热点材料。"),
]

GROUP_ORDER = ["计算机系统", "程序设计与算法", "理论与数据库", "研究与专题"]
GROUP_ICONS = {
    "计算机系统": ":material-chip:",
    "程序设计与算法": ":material-code-braces:",
    "理论与数据库": ":material-database-search:",
    "研究与专题": ":material-flask-outline:",
}
EXCLUDED_MARKDOWN = {"README.md", "README.zh-CN.md"}
LANDING_PAGE = "index.md"
TITLE_OVERRIDES = {
    ("体系结构", "l1.md"): "计算机体系结构导论",
    ("体系结构", "l3.md"): "内存系统",
    ("体系结构", "l4.md"): "存储层次设计进阶",
    ("体系结构", "l5.md"): "浮点运算",
    ("论文笔记", "近期安排.md"): "近期安排与阅读进度",
    ("论文笔记", "论文整理.md"): "论文阅读总整理",
}


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def start_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_root() -> Path:
    return workspace_root() / "markdown"


def docs_root() -> Path:
    return start_root() / "docs"


def natural_key(value: str) -> list[object]:
    parts = re.split(r"(\d+)", value.casefold())
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


def markdown_files(path: Path) -> list[Path]:
    files = [item for item in path.glob("*.md") if item.name not in EXCLUDED_MARKDOWN]
    return sorted(files, key=lambda item: natural_key(item.name))


def asset_files(path: Path) -> list[Path]:
    return sorted(
        [item for item in path.iterdir() if item.is_file() and item.suffix.lower() not in {".md"}],
        key=lambda item: natural_key(item.name),
    )


def extract_title(markdown_path: Path) -> str:
    override = TITLE_OVERRIDES.get((markdown_path.parent.name, markdown_path.name))
    if override:
        return override
    text = markdown_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return markdown_path.stem.replace("_", " ").strip()


def read_summary(category_path: Path, fallback: str) -> str:
    for candidate in ("README.zh-CN.md", "README.md"):
        readme = category_path / candidate
        if readme.exists():
            lines = [line.strip() for line in readme.read_text(encoding="utf-8").splitlines()]
            paragraphs = [line for line in lines if line and not line.startswith("#")]
            if paragraphs:
                return paragraphs[0]
    return fallback


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def nav_label(value: str) -> str:
    return value.replace(":", " - ").replace("：", " - ").strip()


def ensure_clean_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def clean_docs_root() -> None:
    docs = docs_root()
    allowed_dirs = {"assets", "首页文章", *[category.slug for category in CATEGORIES]}
    allowed_files = {"index.md", "使用指南.md", "更新记录.md"}

    for item in docs.iterdir():
        if item.is_dir() and item.name not in allowed_dirs:
            shutil.rmtree(item)
        elif item.is_file() and item.name not in allowed_files:
            item.unlink()


def sync_category(category: Category) -> dict[str, object]:
    src_dir = source_root() / category.slug
    if not src_dir.exists():
        raise FileNotFoundError(f"Missing source folder: {src_dir}")

    dst_dir = docs_root() / category.slug
    ensure_clean_directory(dst_dir)

    for item in src_dir.iterdir():
        if item.is_file() and item.name in EXCLUDED_MARKDOWN:
            continue
        target = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    md_files = markdown_files(src_dir)
    pdf_lookup = {item.stem.casefold(): item.name for item in src_dir.glob("*.pdf")}
    notes = []
    for md in md_files:
        notes.append(
            {
                "file": md.name,
                "title": extract_title(md),
                "pdf": pdf_lookup.get(md.stem.casefold(), ""),
            }
        )

    summary = read_summary(src_dir, category.description)
    stats = {
        "markdown_count": len(md_files),
        "asset_count": len(asset_files(src_dir)),
        "pdf_count": len(list(src_dir.glob("*.pdf"))),
    }

    meta_path = dst_dir / ".meta.yml"
    meta_path.write_text(
        "\n".join(
            [
                "comments: true",
                "tags:",
                f"  - {category.group}",
                f"  - {category.title}",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )

    landing_path = dst_dir / LANDING_PAGE
    landing_path.write_text(build_category_index(category, summary, notes, stats), encoding="utf-8", newline="\n")

    return {
        "category": category,
        "summary": summary,
        "notes": notes,
        "stats": stats,
    }


def build_category_index(
    category: Category,
    summary: str,
    notes: list[dict[str, str]],
    stats: dict[str, int],
) -> str:
    lines = [
        f"# {category.title}",
        "",
        f"> {summary}",
        "",
        f"- 笔记数量：`{stats['markdown_count']}`",
        f"- 配套资源：`{stats['asset_count']}`",
        f"- PDF 数量：`{stats['pdf_count']}`",
        "",
        "## 快速进入",
        "",
    ]

    lines.extend(build_cards([
        {
            "title": note["title"],
            "href": note["file"],
            "summary": f'`{note["file"]}`',
            "meta": f'[在线阅读]({note["file"]})' + '{ .md-button .md-button--primary }' + (
                f' [PDF]({note["pdf"]})' + '{ .md-button }' if note["pdf"] else ""
            ),
        }
        for note in notes
    ]))

    lines.extend(
        [
            "",
            "",
            "## 文件清单",
            "",
            "| 笔记 | 在线阅读 | PDF |",
            "| --- | --- | --- |",
        ]
    )

    for note in notes:
        pdf_link = f'[下载]({note["pdf"]})' if note["pdf"] else "—"
        lines.append(f'| {note["title"]} | [打开]({note["file"]}) | {pdf_link} |')

    lines.extend(
        [
            "",
            "!!! tip \"使用建议\"",
            "    左侧导航适合按课程顺序阅读，搜索框适合按概念、算法名、章节名直接跳转。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_homepage(category_data: list[dict[str, object]]) -> str:
    grouped: dict[str, list[dict[str, object]]] = {group: [] for group in GROUP_ORDER}
    for item in category_data:
        grouped[item["category"].group].append(item)

    total_notes = sum(int(item["stats"]["markdown_count"]) for item in category_data)  # type: ignore[index]
    total_assets = sum(int(item["stats"]["asset_count"]) for item in category_data)  # type: ignore[index]
    sync_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# gxy 的学习空间",
        "",
        "课程笔记、论文阅读与个人知识整理站，适合按课程顺序复习，也适合直接搜索关键词。",
        "{: .hero-subtitle }",
        "",
        '[快速上手](使用指南.md){ .md-button .md-button--primary }',
        f'[去看论文笔记](论文笔记/{LANDING_PAGE})' + '{ .md-button }',
        '[查看 GitHub 仓库](https://github.com/Guoguo828/mkdocs_start){ .md-button }',
        "",
        "## :material-view-dashboard-outline: 站点概览",
        "",
        "这里收录了计算机系统、算法、数据库、离散数学、OOP、论文阅读等方向的课程与专题笔记，阅读路径偏向课程体系，同时保留搜索与标签索引来提升查阅效率。",
        "",
    ]

    lines.extend(build_cards(
        [
            {
                "title": ":material-shape-outline: 专题目录",
                "href": "tags.md",
                "summary": f"`{len(category_data)} 个学习分区`",
                "meta": "按课程和专题组织，适合系统复习。",
            },
            {
                "title": ":material-notebook-multiple-outline: Markdown 笔记",
                "href": "使用指南.md",
                "summary": f"`{total_notes} 篇可在线阅读笔记`",
                "meta": "覆盖课程主线、重点概念与实验整理。",
            },
            {
                "title": ":material-image-multiple-outline: 配套资源",
                "href": "更新记录.md",
                "summary": f"`{total_assets} 份图像 / PDF / 附件`",
                "meta": "截图、讲义和 PDF 可直接配合阅读。",
            },
            {
                "title": ":material-clock-outline: 最近同步",
                "href": "更新记录.md",
                "summary": f"`{sync_time}`",
                "meta": "首页、导航与索引会随同步一并更新。",
            },
        ],
        classes="metrics-grid",
    ))

    lines.extend(
        [
            "",
            "## :material-library-shelves: 学习分区",
            "",
        ]
    )

    for group in GROUP_ORDER:
        group_icon = GROUP_ICONS.get(group, ":material-folder-outline:")
        lines.extend(
            [
                f"### {group_icon} {group}",
                "",
            ]
        )
        lines.extend(build_cards([
            {
                "title": f'{item["category"].icon} {item["category"].title}',  # type: ignore[index]
                "href": f'{item["category"].slug}/{LANDING_PAGE}',  # type: ignore[index]
                "summary": str(item["summary"]),
                "meta": f'`{item["stats"]["markdown_count"]} 篇笔记 · {item["stats"]["pdf_count"]} 份 PDF`',  # type: ignore[index]
            }
            for item in grouped[group]
        ]))
        lines.append("")

    lines.extend(
        [
            "## :material-star-four-points-outline: 站点亮点",
            "",
        ]
    )
    lines.extend(build_cards(
        [
            {
                "title": ":material-text-search: 搜索导向",
                "href": "使用指南.md",
                "summary": "支持搜索建议、关键词高亮和搜索结果分享。",
                "meta": "适合直接检索算法名、章节名或关键术语。",
            },
            {
                "title": ":material-tag-multiple-outline: 标签索引",
                "href": "tags.md",
                "summary": "可以按课程和专题做交叉浏览，不必只靠目录找内容。",
                "meta": "临考前做交叉回看会更顺手。",
            },
            {
                "title": ":material-theme-light-dark: 双主题阅读",
                "href": "使用指南.md",
                "summary": "保留浅色 / 深色阅读体验，并强化内容面板与卡片层次。",
                "meta": "长文阅读更稳，夜间浏览也更舒服。",
            },
            {
                "title": ":material-open-in-new: 源码直达",
                "href": "https://github.com/Guoguo828/mkdocs_start",
                "summary": "顶部仓库入口可以直接查看源码与原始 Markdown。",
                "meta": "方便从网页切回 GitHub 继续维护。",
            },
        ],
        classes="feature-grid",
    ))

    lines.extend(
        [
            "",
            '!!! tip "推荐阅读方式"',
            "    课程复习时从分区首页顺着目录阅读；需要查一个具体知识点时，优先用顶部搜索框或标签索引。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_usage_page() -> str:
    return """# 使用指南

## 怎么最快找到笔记

1. 先用顶部搜索框搜课程名、算法名、章节名或关键术语。
2. 如果你想系统看一门课，用顶部标签切到对应分区，再从目录页进具体笔记。
3. 如果你知道 PDF 存在，可以直接在专题首页点 `PDF` 链接下载。

## 这个站点新增了什么

- 搜索建议和高亮
- Material 原生 cards 导航
- 标签索引页
- GitHub 仓库入口
- 页面评论入口（需仓库侧启用）
- 本地点赞反馈
- 深色 / 浅色主题切换

## 建议的阅读方式

- 课程复习：从专题首页按顺序点每一篇笔记
- 查概念：直接用搜索
- 对照原材料：优先打开 Markdown，再按需下载同名 PDF
"""


def build_updates_page(category_data: list[dict[str, object]]) -> str:
    lines = [
        "# 更新记录",
        "",
        f"- 最近同步时间：`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- 同步目录数：`{len(category_data)}`",
        "",
        "## 本次纳入站点的目录",
        "",
    ]
    for item in category_data:
        category: Category = item["category"]  # type: ignore[assignment]
        stats = item["stats"]  # type: ignore[assignment]
        lines.append(f'- **{category.title}**：{stats["markdown_count"]} 篇 Markdown，{stats["asset_count"]} 个资源文件。')
    return "\n".join(lines) + "\n"


def build_tags_page() -> str:
    return """# 标签索引

这里汇总了站点内各页的标签，便于按课程和专题交叉检索。

<!-- material/tags -->
"""


def build_cards(items: list[dict[str, str]], classes: str = "") -> list[str]:
    class_names = "grid cards"
    if classes:
        class_names += f" {classes}"
    lines: list[str] = [f'<div class="{class_names}" markdown>']
    for item in items:
        lines.append(f'-   __[{item["title"]}]({item["href"]})__')
        lines.append("    ---")
        lines.append(f'    {item["summary"]}')
        lines.append(f'    {item["meta"]}')
        lines.append("")
    lines.append("</div>")
    return lines


def build_mkdocs_config(category_data: list[dict[str, object]]) -> str:
    group_map: dict[str, list[dict[str, object]]] = {group: [] for group in GROUP_ORDER}
    for item in category_data:
        group_map[item["category"].group].append(item)

    lines = [
        'site_name: "gxy 的学习空间"',
        'site_description: "课程笔记、论文阅读与个人知识整理站"',
        'site_url: "https://guoguo828.github.io/mkdocs_start/"',
        'docs_dir: "docs"',
        'site_dir: "site"',
        "use_directory_urls: false",
        'repo_url: "https://github.com/Guoguo828/mkdocs_start"',
        'repo_name: "Guoguo828/mkdocs_start"',
        'edit_uri: "edit/main/docs/"',
        "",
        "theme:",
        '  name: "material"',
        '  language: "zh"',
        '  logo: "assets/images/logo.svg"',
        '  custom_dir: "overrides"',
        "  icon:",
        '    repo: "fontawesome/brands/github"',
        "  features:",
        '    - navigation.tabs',
        '    - navigation.tabs.sticky',
        '    - navigation.sections',
        '    - navigation.expand',
        '    - navigation.indexes',
        '    - navigation.top',
        '    - navigation.tracking',
        '    - navigation.path',
        '    - navigation.footer',
        '    - navigation.instant',
        '    - navigation.instant.progress',
        '    - navigation.instant.prefetch',
        '    - header.autohide',
        '    - announce.dismiss',
        '    - search.suggest',
        '    - search.highlight',
        '    - search.share',
        '    - toc.follow',
        '    - content.code.copy',
        '    - content.code.select',
        '    - content.action.edit',
        '    - content.action.view',
        '    - content.tabs.link',
        '    - content.code.annotate',
        '    - content.tooltips',
        "  palette:",
        '    - scheme: "default"',
        '      primary: "custom"',
        '      accent: "custom"',
        "      toggle:",
        '        icon: "material/weather-night"',
        '        name: "切换到深色模式"',
        '    - scheme: "slate"',
        '      primary: "custom"',
        '      accent: "custom"',
        "      toggle:",
        '        icon: "material/weather-sunny"',
        '        name: "切换到浅色模式"',
        "  font:",
        '    text: "Noto Sans SC"',
        '    code: "JetBrains Mono"',
        "",
        "plugins:",
        "  - meta",
        "  - search:",
        "      lang:",
        '        - "zh"',
        '        - "en"',
        "      separator: '[\\s\\-\\.]+'",
        "  - tags",
        "  - git-revision-date-localized:",
        "      type: \"datetime\"",
        "      locale: \"zh\"",
        "      enable_creation_date: false",
        "      fallback_to_build_date: true",
        "  - minify:",
        "      minify_html: true",
        "",
        "markdown_extensions:",
        "  - admonition",
        "  - attr_list",
        "  - md_in_html",
        "  - tables",
        "  - toc:",
        '      permalink: true',
        "      toc_depth: 3",
        '      title: "本页目录"',
        "  - pymdownx.details",
        "  - pymdownx.superfences",
        "  - pymdownx.tabbed:",
        "      alternate_style: true",
        "  - pymdownx.highlight:",
        "      anchor_linenums: true",
        "  - pymdownx.inlinehilite",
        "  - pymdownx.snippets",
        "  - pymdownx.emoji:",
        "      emoji_index: !!python/name:material.extensions.emoji.twemoji",
        "      emoji_generator: !!python/name:material.extensions.emoji.to_svg",
        "  - abbr",
        "  - pymdownx.mark",
        "  - pymdownx.tasklist:",
        "      custom_checkbox: true",
        "  - pymdownx.keys",
        "",
        "extra_css:",
        '  - "assets/stylesheets/extra.css"',
        "",
        "extra_javascript:",
        '  - "assets/javascripts/particles.min.js"',
        '  - "assets/javascripts/particles.js"',
        '  - "assets/javascripts/site.js"',
        "",
        "validation:",
        "  nav:",
        "    omitted_files: ignore",
        'copyright: "Copyright © 2006-2026 郭响宇"',
        "",
        "nav:",
        f"  - {yaml_quote(nav_label('首页'))}:",
        f'      - {yaml_quote(nav_label("欢迎页"))}: {yaml_quote("index.md")}',
        f'      - {yaml_quote(nav_label("使用指南"))}: {yaml_quote("使用指南.md")}',
        f'      - {yaml_quote(nav_label("更新记录"))}: {yaml_quote("更新记录.md")}',
        f'      - {yaml_quote(nav_label("标签索引"))}: {yaml_quote("tags.md")}',
        f"  - {yaml_quote(nav_label('关于我'))}:",
        f'      - {yaml_quote(nav_label("GXY 介绍"))}: {yaml_quote("首页文章/gxy介绍.md")}',
        f'      - {yaml_quote(nav_label("简介"))}: {yaml_quote("首页文章/关于我.md")}',
    ]

    for group in GROUP_ORDER:
        lines.append(f"  - {yaml_quote(nav_label(group))}:")
        for item in group_map[group]:
            category: Category = item["category"]  # type: ignore[assignment]
            lines.append(f'      - {yaml_quote(nav_label(category.title))}: {yaml_quote(f"{category.slug}/{LANDING_PAGE}")}')

    return "\n".join(lines) + "\n"


def main() -> None:
    clean_docs_root()
    results = [sync_category(category) for category in CATEGORIES]

    docs = docs_root()
    (docs / "index.md").write_text(build_homepage(results), encoding="utf-8", newline="\n")
    (docs / "使用指南.md").write_text(build_usage_page(), encoding="utf-8", newline="\n")
    (docs / "更新记录.md").write_text(build_updates_page(results), encoding="utf-8", newline="\n")
    (docs / "tags.md").write_text(build_tags_page(), encoding="utf-8", newline="\n")

    config_path = start_root() / "mkdocs.yml"
    config_path.write_text(build_mkdocs_config(results), encoding="utf-8", newline="\n")

    print(f"Synced {len(results)} categories into {docs}")
if __name__ == "__main__":
    main()
