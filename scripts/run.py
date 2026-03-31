#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
How To Read a Book - Main Orchestration Script

Transforms EPUB-formatted ebooks into chapter-level Markdown sources for NotebookLM,
paired with a "How To Read a Book" analytical reading persona.

Usage:
    python scripts/run.py /path/to/book.epub

The script outputs JSON at the end for programmatic use.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"

# Auto-switch to virtual environment if available
# This ensures the skill works regardless of how it's invoked
if (
    VENV_PYTHON.exists()
    and sys.executable != str(VENV_PYTHON)
    and not os.environ.get("HTRAB_VENV_CHECKED")
):
    os.environ["HTRAB_VENV_CHECKED"] = "1"
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from epub_parser import EpubParser, EpubParseError
    from notebooklm_client import NotebookLMClient, NotebookLMError
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Please run: ./install.sh")
    sys.exit(1)


def print_progress(message: str):
    """Print progress indicator."""
    print(message, flush=True)


def validate_epub_path(epub_path: str) -> Path:
    """Validate EPUB file path."""
    path = Path(epub_path)

    if not path.exists():
        raise FileNotFoundError(f"EPUB file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() != '.epub':
        raise ValueError(f"File must be .epub format: {path.suffix}")

    return path


def chapter_to_markdown(chapter, book_title: str) -> str:
    """
    Convert a Chapter object to Markdown with frontmatter.
    """
    from bs4 import BeautifulSoup

    # Clean HTML content
    soup = BeautifulSoup(chapter.content, 'html.parser')

    # Extract text, preserving paragraph structure
    paragraphs = soup.find_all('p')
    if not paragraphs:
        text = soup.get_text(separator='\n\n')
    else:
        text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    # Build Markdown with frontmatter
    markdown = f"""---
chapter: {chapter.number}
title: "{chapter.title}"
book: "{book_title}"
---

# Chapter {chapter.number}: {chapter.title}

{text}
"""

    return markdown


def save_chapter_to_file(chapter, book_title: str, temp_dir: str) -> str:
    """
    Save a chapter as Markdown file.
    Returns the file path.
    """
    # Generate filename
    slug = EpubParser()._slugify(chapter.title)
    filename = f"{chapter.number:02d}-{slug}.md"
    filepath = os.path.join(temp_dir, filename)

    # Write content
    markdown = chapter_to_markdown(chapter, book_title)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)

    return filepath


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run.py <path-to-epub>")
        print("")
        print("Example:")
        print("  python scripts/run.py ~/Downloads/ThinkingFastAndSlow.epub")
        sys.exit(1)

    epub_path = sys.argv[1]

    # Initialize result dict for JSON output
    result = {
        "success": False,
        "notebook_id": None,
        "notebook_url": None,
        "book_title": None,
        "chapter_count": 0,
        "sources_uploaded": 0,
        "error": None
    }

    try:
        # Step 0: Validate environment
        client = NotebookLMClient()

        print_progress("🔍 Checking NotebookLM CLI...")
        if not client.check_installed():
            raise RuntimeError(
                "NotebookLM CLI not found.\n"
                "Install with: pip install notebooklm-py playwright && playwright install chromium"
            )

        if not client.check_authenticated():
            raise RuntimeError(
                "Not authenticated with NotebookLM.\n"
                "Run: notebooklm login"
            )

        # Step 1: Validate EPUB
        print_progress("📖 Validating EPUB file...")
        epub_path = validate_epub_path(epub_path)
        print_progress(f"   ✅ Found: {epub_path.name}")

        # Step 2: Parse EPUB
        print_progress("📚 Parsing EPUB structure...")
        parser = EpubParser()
        book_title, chapters = parser.parse(str(epub_path))
        print_progress(f"   ✅ Found: {len(chapters)} chapters")
        print_progress(f"   📕 Title: {book_title}")

        result["book_title"] = book_title
        result["chapter_count"] = len(chapters)

        # Step 3: Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="epub_reader_")
        print_progress(f"📁 Temp directory: {temp_dir}")

        # Step 4: Convert chapters to Markdown
        print_progress("✍️  Converting chapters to Markdown...")
        chapter_files = []
        for chapter in chapters:
            filepath = save_chapter_to_file(chapter, book_title, temp_dir)
            chapter_files.append(filepath)
            print_progress(f"   ✓ {os.path.basename(filepath)}")

        # Step 5: Create NotebookLM notebook
        print_progress("📓 Creating NotebookLM notebook...")
        notebook_title = f"{book_title} — Reading Companion"
        notebook_id = client.create_notebook(notebook_title)

        result["notebook_id"] = notebook_id
        result["notebook_url"] = f"https://notebooklm.google.com/notebook/{notebook_id}"

        # Step 6: Configure persona
        print_progress("⚙️  Configuring reading companion persona...")
        script_dir = Path(__file__).parent
        prompt_path = script_dir.parent / "assets" / "reading_companion_prompt.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Persona prompt not found: {prompt_path}")

        client.configure_notebook(notebook_id, str(prompt_path))

        # Step 7: Upload sources
        print_progress("📤 Uploading chapters to NotebookLM...")
        upload_results = client.upload_all_sources(notebook_id, chapter_files)

        result["sources_uploaded"] = len(upload_results["success"])

        # Step 8: Cleanup
        if len(upload_results["failed"]) == 0:
            print_progress("🧹 Cleaning up...")
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print_progress(f"⚠️  {len(upload_results['failed'])} uploads failed.")
            print_progress(f"   Temp files preserved: {temp_dir}")

        # Success!
        result["success"] = True

        # Human-readable summary
        print_progress("")
        print_progress("=" * 50)
        print_progress("🎉 SUCCESS!")
        print_progress("=" * 50)
        print_progress(f"📕 Book: {book_title}")
        print_progress(f"📚 Notebook: {notebook_title}")
        print_progress(f"📖 Chapters uploaded: {len(upload_results['success'])}/{len(chapters)}")
        if upload_results["failed"]:
            print_progress(f"❌ Failed: {len(upload_results['failed'])}")
        print_progress("")
        print_progress(f"🔗 Notebook URL: {result['notebook_url']}")
        print_progress("")
        print_progress("💡 The reading companion persona is now active.")
        print_progress("   Try asking: 'What is the main problem this book is trying to solve?'")

    except Exception as e:
        result["error"] = str(e)
        print_progress(f"")
        print_progress("=" * 50)
        print_progress("❌ ERROR")
        print_progress("=" * 50)
        print_progress(f"{e}")
        print_progress("")
        print_progress("Troubleshooting:")
        print_progress("  • Make sure the EPUB file exists and is readable")
        print_progress("  • Run ./install.sh if this is your first time")
        print_progress("  • Check that you're authenticated: notebooklm login")

    finally:
        # JSON output
        print("")
        print("---JSON_OUTPUT---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
