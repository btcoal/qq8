#!/usr/bin/env python3
"""Validate qq8 HTML pages and image assets against editorial and technical rules."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

IGNORED_DIRS = {".git", ".agents", ".agent", ".vscode", "drafts", "library", "output", "node_modules"}

RAW_SECTION_PATTERNS = [
    ("section symbol (§)", re.compile(r"§")),
    ("raw CFR citation", re.compile(r"\b15\s+CFR\b")),
    ("raw USC citation", re.compile(r"\b50\s+U\.S\.C\.")),
    ("Supplement No. citation", re.compile(r"\bSupplement\s+No\.\s+\d+")),
]

DISALLOWED_PATTERNS = [
    ("colloquial prove/proved/proves", re.compile(r"\bprove[ds]?\b", re.IGNORECASE)),
    ("colloquial proof", re.compile(r"\bproof\b", re.IGNORECASE)),
    ("PRC acronym", re.compile(r"\bPRC\b")),
    ("People's Republic phrasing", re.compile(r"People['’]s Republic", re.IGNORECASE)),
    ("SPECIAL REPORT tag", re.compile(r"SPECIAL\s+REPORT", re.IGNORECASE)),
    ("Dateline label", re.compile(r"\bDateline:", re.IGNORECASE)),
    ("local preview footer text", re.compile(r"Published locally for preview", re.IGNORECASE)),
    ("Primary Documents heading", re.compile(r"Primary\s+Documents", re.IGNORECASE)),
]

VAGUE_ATTRIBUTION_RE = re.compile(
    r"\b(officials|policymakers|reporters|sources|experts)\s+(said|warned|argued|noted|claimed|revealed)\b",
    re.IGNORECASE,
)

FORCED_RHETORIC_RE = re.compile(
    r"(irony is hard to miss|missing forensic link|the first public)",
    re.IGNORECASE,
)


class PageInspector(HTMLParser):
    """Extract links, meta tags, article lists, body paragraphs, and strong tags cleanly."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_style = False
        self.in_script = False
        self.in_article_or_main = 0
        self.body_tag_depth = 0

        self.skip_prose_depth = 0
        self.element_stack: list[tuple[str, bool]] = []
        self.in_p = False
        self.p_skip_metrics = False
        self.current_p_chunks: list[str] = []
        self.current_p_strongs = 0

        self.list_tags_in_content: list[str] = []
        self.refs: list[tuple[str, str]] = []
        self.canonical_found = False
        self.og_props: set[str] = set()

        self.visible_text_chunks: list[str] = []
        self.prose_paragraphs: list[tuple[int, str, int]] = []  # (word_count, text, strong_count)

    @staticmethod
    def _classes(attrs_dict: dict[str, str | None]) -> set[str]:
        raw = attrs_dict.get("class") or ""
        return set(raw.split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag == "style":
            self.in_style = True
        elif tag == "script":
            self.in_script = True
        elif tag == "body":
            self.body_tag_depth += 1

        if tag in ("article", "main"):
            self.in_article_or_main += 1

        if tag in ("ul", "ol", "li") and self.in_article_or_main > 0:
            self.list_tags_in_content.append(f"<{tag}>")

        if tag == "link" and (attrs_dict.get("rel") or "").lower() == "canonical":
            if attrs_dict.get("href"):
                self.canonical_found = True

        if tag == "meta":
            prop = (attrs_dict.get("property") or "").lower()
            if prop in {"og:title", "og:description", "og:image"} and attrs_dict.get("content"):
                self.og_props.add(prop)

        for attr_name in ("src", "href"):
            val = attrs_dict.get(attr_name)
            if val is not None:
                self.refs.append((attr_name, val))

        classes = self._classes(attrs_dict)
        is_skip_container = tag in ("figcaption",) or bool(
            classes & {"callout-box", "meta-bar", "story-meta", "sources-section"}
        )
        if tag not in {"meta", "link", "img", "br", "hr", "input"}:
            self.element_stack.append((tag, is_skip_container))
            if is_skip_container:
                self.skip_prose_depth += 1

        if tag == "p":
            self.in_p = True
            self.current_p_chunks = []
            self.current_p_strongs = 0
            self.p_skip_metrics = (self.skip_prose_depth > 0) or bool(
                classes & {"standfirst", "table-note"}
            )

        if tag in ("strong", "b") and self.in_p and not self.p_skip_metrics:
            self.current_p_strongs += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style":
            self.in_style = False
        elif tag == "script":
            self.in_script = False
        elif tag == "body" and self.body_tag_depth > 0:
            self.body_tag_depth -= 1

        if tag in ("article", "main") and self.in_article_or_main > 0:
            self.in_article_or_main -= 1

        if tag == "p" and self.in_p:
            if not self.p_skip_metrics and self.in_article_or_main > 0:
                text = " ".join("".join(self.current_p_chunks).split())
                words = len(text.split()) if text else 0
                if words > 0:
                    self.prose_paragraphs.append((words, text, self.current_p_strongs))
            self.in_p = False
            self.p_skip_metrics = False
            self.current_p_chunks = []
            self.current_p_strongs = 0

        for idx in range(len(self.element_stack) - 1, -1, -1):
            open_tag, was_skip = self.element_stack[idx]
            if open_tag == tag:
                for _, popped_skip in self.element_stack[idx:]:
                    if popped_skip and self.skip_prose_depth > 0:
                        self.skip_prose_depth -= 1
                del self.element_stack[idx:]
                break

    def handle_data(self, data: str) -> None:
        if self.in_style or self.in_script:
            return
        self.visible_text_chunks.append(data)
        if self.in_p:
            self.current_p_chunks.append(data)


def validate_image_magic(path: Path) -> str | None:
    """Return an error reason if the file does not look like a real image, else None."""
    try:
        header = path.read_bytes()[:512]
    except OSError as exc:
        return f"could not read file ({exc})"

    if len(header) < 8:
        return "file is empty or too short to be an image"

    if header.startswith(b"\xff\xd8\xff"):
        return None
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    if header.startswith((b"GIF87a", b"GIF89a")):
        return None
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return None
    if b"ftyp" in header[4:12]:
        return None

    ext = path.suffix.lower()
    if ext == ".svg":
        text_start = header.lstrip().lower()
        if text_start.startswith((b"<svg", b"<?xml")) or b"<svg" in header.lower():
            return None

    return f"invalid image signature for {path.name} (starts with {header[:16]!r}; possibly an HTML challenge page)"


def find_repo_root(start: Path) -> Path:
    """Locate repository root from script location or working directory."""
    for candidate in (start, *start.parents):
        if (candidate / "CNAME").exists() or (candidate / ".git").exists():
            return candidate
    return Path.cwd()


def discover_html_files(repo_root: Path) -> list[Path]:
    """Return root index.html and non-hidden <slug>/index.html files."""
    files: list[Path] = []
    root_index = repo_root / "index.html"
    if root_index.is_file():
        files.append(root_index)
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir() or child.name in IGNORED_DIRS or child.name.startswith("."):
            continue
        sub_index = child / "index.html"
        if sub_index.is_file():
            files.append(sub_index)
    return files


def check_file(html_path: Path, repo_root: Path) -> tuple[list[str], list[str]]:
    """Audit a single HTML file and return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    raw = html_path.read_text(encoding="utf-8")
    inspector = PageInspector()
    inspector.feed(raw)
    inspector.close()

    visible_text = " ".join("".join(inspector.visible_text_chunks).split())
    raw_no_style_script = re.sub(
        r"<(style|script)\b[^>]*>.*?</\1>", "", raw, flags=re.IGNORECASE | re.DOTALL
    )

    if inspector.list_tags_in_content:
        found = ", ".join(sorted(set(inspector.list_tags_in_content)))
        errors.append(f"list markup inside article/main is forbidden: {found}")

    for label, pat in RAW_SECTION_PATTERNS:
        if pat.search(visible_text):
            errors.append(f"raw statutory/section reference detected ({label})")

    for label, pat in DISALLOWED_PATTERNS:
        if pat.search(visible_text):
            errors.append(f"disallowed text detected ({label})")

    if re.search(r">\s*Documents\s*</a>", raw_no_style_script, re.IGNORECASE):
        errors.append('navigation link uses "Documents" instead of "Sources"')

    if "qq8-theme" not in raw or "qq8-width" not in raw:
        errors.append("missing shared qq8-theme / qq8-width localStorage persistence hooks")

    if not inspector.canonical_found:
        errors.append('missing <link rel="canonical" ...>')

    missing_og = sorted({"og:title", "og:description", "og:image"} - inspector.og_props)
    if missing_og:
        errors.append(f"missing Open Graph meta tags: {', '.join(missing_og)}")

    html_dir = html_path.parent
    checked_images: set[Path] = set()
    for attr_name, val in inspector.refs:
        if val.startswith(("http://", "https://", "mailto:", "data:", "#")) or not val.strip():
            continue
        clean = val.split("#", 1)[0].split("?", 1)[0]
        if clean.startswith("/"):
            target = (repo_root / clean.lstrip("/")).resolve()
        else:
            target = (html_dir / clean).resolve()

        if target.is_dir():
            if not (target / "index.html").is_file():
                errors.append(f"broken relative {attr_name}={val!r} (directory lacks index.html)")
        elif not target.is_file():
            errors.append(f"broken relative {attr_name}={val!r} ({target} not found)")
        elif attr_name == "src" and target.suffix.lower() in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".avif",
            ".svg",
        }:
            if target not in checked_images:
                checked_images.add(target)
                img_err = validate_image_magic(target)
                if img_err:
                    errors.append(img_err)

    total_body_strongs = sum(s for _, _, s in inspector.prose_paragraphs)
    if total_body_strongs > 6:
        warnings.append(
            f"body prose contains {total_body_strongs} <strong>/<b> elements (target <= 6 for sparse emphasis)"
        )

    for words, text, _ in inspector.prose_paragraphs:
        if words > 120:
            preview = " ".join(text.split()[:10])
            warnings.append(f'long paragraph ({words} words > 120): "{preview}..."')

    for match in VAGUE_ATTRIBUTION_RE.finditer(visible_text):
        warnings.append(f"possible vague attribution: {match.group(0)!r}")

    for match in FORCED_RHETORIC_RE.finditer(visible_text):
        warnings.append(f"possible forced rhetoric or unverified claim: {match.group(0)!r}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify qq8 HTML pages against editorial rules.")
    parser.add_argument("paths", nargs="*", help="HTML files to inspect (defaults to published site HTML files)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    repo_root = find_repo_root(Path(__file__).resolve())
    targets = [Path(p).resolve() for p in args.paths] if args.paths else discover_html_files(repo_root)

    if not targets:
        print(f"No HTML files found under {repo_root}", file=sys.stderr)
        return 1

    total_errors = 0
    total_warnings = 0

    for html_path in targets:
        try:
            rel = html_path.relative_to(repo_root)
        except ValueError:
            rel = html_path

        errors, warnings = check_file(html_path, repo_root)
        total_errors += len(errors)
        total_warnings += len(warnings)

        status = "FAIL" if errors else ("WARN" if warnings else "PASS")
        print(f"[{status}] {rel}")
        for err in errors:
            print(f"  ERROR: {err}")
        for warn in warnings:
            print(f"  WARN:  {warn}")

    print(f"Checked {len(targets)} file(s): {total_errors} error(s), {total_warnings} warning(s).")
    if total_errors > 0 or (args.strict and total_warnings > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
