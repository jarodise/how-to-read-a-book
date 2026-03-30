#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB Parser Module - Extract book metadata and chapter structure from EPUB files.

Uses TOC-first parsing with heading-based fallback for robust chapter detection.
"""

import re
import html
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import unicodedata

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError as e:
    raise ImportError(f"Required packages not installed. Run: pip install ebooklib beautifulsoup4") from e


@dataclass
class Chapter:
    """Represents a single chapter from the book."""
    number: int
    title: str
    content: str  # HTML content
    href: Optional[str] = None


class EpubParseError(Exception):
    """Raised when EPUB parsing fails."""
    pass


class EpubParser:
    """Parser for EPUB files with chapter extraction capabilities."""

    # Minimum chapters for TOC to be considered valid
    TOC_MIN_CHAPTERS = 3

    # Heading tags to scan for fallback detection
    HEADING_TAGS = ['h1', 'h2']

    # Front matter patterns (lowercase for matching)
    FRONT_MATTER_PATTERNS = [
        'cover', 'title page', 'copyright', 'dedication',
        'table of contents', 'contents', 'introduction', 'preface',
        'foreword', 'acknowledgments', 'prologue'
    ]

    # Back matter patterns
    BACK_MATTER_PATTERNS = [
        'epilogue', 'afterword', 'appendix', 'glossary',
        'bibliography', 'references', 'index', 'about the author',
        'acknowledgements'
    ]

    def __init__(self):
        self.book = None
        self.book_title = None

    def _slugify(self, title: str) -> str:
        """
        Convert title to filesystem-safe slug.
        Transliterates non-ASCII, then sanitizes with regex.
        """
        # Transliterate to ASCII
        normalized = unicodedata.normalize('NFKD', title)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')

        # Lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', ascii_text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)

        # Trim hyphens from ends and limit length
        slug = slug.strip('-')[:50]

        return slug or "untitled"

    def _clean_html(self, html_content: str) -> str:
        """Clean and normalize HTML content."""
        # Unescape HTML entities
        content = html.unescape(html_content)
        return content

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from HTML for title detection."""
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(strip=True)

    def _is_heading_important(self, text: str) -> bool:
        """Check if a heading looks like a chapter title (not front/back matter)."""
        text_lower = text.lower().strip()

        # Skip if empty or too short
        if len(text_lower) < 2:
            return False

        # Skip if matches front/back matter patterns
        for pattern in self.FRONT_MATTER_PATTERNS + self.BACK_MATTER_PATTERNS:
            if pattern in text_lower:
                return False

        # Skip common non-chapter headings
        skip_patterns = ['copyright', 'notes', 'footnote', 'copyright page']
        if any(p in text_lower for p in skip_patterns):
            return False

        return True

    def _extract_from_toc(self) -> List[Chapter]:
        """
        Extract chapters from EPUB's table of contents (NCX or NavDoc).
        Handles both tuple format and ebooklib.epub.Link objects.
        """
        chapters = []
        seen_hrefs = set()

        try:
            # Try to get TOC from ebooklib
            toc = self.book.toc

            if not toc:
                return []

            chapter_num = 0

            for item in toc:
                href = None
                title = None

                # Handle tuple format (legacy)
                if isinstance(item, tuple):
                    section = item[0]
                    href = item[1] if len(item) > 1 else None
                    title = section.name if hasattr(section, 'name') else str(section)
                    # Process subsections if present
                    subsections = item[2] if len(item) > 2 else []

                # Handle ebooklib.epub.Link format
                elif hasattr(item, 'href') and hasattr(item, 'title'):
                    href = item.href
                    title = item.title
                    subsections = []

                else:
                    continue

                if not title or not href:
                    continue

                # Skip duplicates
                if href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                # Skip front/back matter
                if not self._is_heading_important(title):
                    continue

                chapter_num += 1
                chapters.append(Chapter(
                    number=chapter_num,
                    title=title,
                    content="",
                    href=href
                ))

        except Exception as e:
            return []

        return chapters if len(chapters) >= self.TOC_MIN_CHAPTERS else []

    def _extract_from_headings(self) -> List[Chapter]:
        """
        Fallback: Extract chapters by scanning for heading tags.
        """
        chapters = []
        chapter_num = 0

        try:
            # Get all HTML documents in reading order
            items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

            for item in items:
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')

                # Find all headings
                for tag in self.HEADING_TAGS:
                    for heading in soup.find_all(tag):
                        text = heading.get_text(strip=True)

                        if self._is_heading_important(text):
                            chapter_num += 1
                            chapters.append(Chapter(
                                number=chapter_num,
                                title=text,
                                content=str(heading.find_parent()) if heading.find_parent() else "",
                                href=item.get_name()
                            ))

        except Exception as e:
            pass

        return chapters

    def _fetch_chapter_content(self, chapter: Chapter) -> str:
        """Fetch full content for a chapter from the EPUB."""
        if not chapter.href:
            return chapter.content

        try:
            # Handle href which might include fragment
            href = chapter.href.split('#')[0]

            # Find the document
            for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                if item.get_name() == href:
                    return item.get_content().decode('utf-8', errors='ignore')

        except Exception:
            pass

        return chapter.content

    def _extract_book_title(self) -> str:
        """Extract book title from metadata or content."""
        # Try OPF metadata first
        try:
            title = self.book.get_metadata('DC', 'title')
            if title:
                return title[0][0] if isinstance(title[0], tuple) else title[0]
        except:
            pass

        # Try first HTML file's h1
        try:
            for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                h1 = soup.find('h1')
                if h1:
                    return h1.get_text(strip=True)
        except:
            pass

        return "Untitled Book"

    def parse(self, epub_path: str) -> Tuple[str, List[Chapter]]:
        """
        Parse EPUB and return (book_title, chapters).

        Strategy:
        1. Try TOC-first extraction
        2. If TOC yields < 3 chapters, fall back to heading-based
        3. Fetch content for each chapter
        """
        epub_path = Path(epub_path)

        if not epub_path.exists():
            raise EpubParseError(f"EPUB file not found: {epub_path}")

        try:
            self.book = epub.read_epub(str(epub_path))
        except Exception as e:
            raise EpubParseError(f"Failed to read EPUB: {e}")

        # Extract book title
        self.book_title = self._extract_book_title()

        # Try TOC-first
        chapters = self._extract_from_toc()

        # Fallback to heading-based if needed
        if len(chapters) < self.TOC_MIN_CHAPTERS:
            chapters = self._extract_from_headings()

        if not chapters:
            raise EpubParseError("Could not extract any chapters from EPUB")

        # Fetch full content for each chapter
        for i, chapter in enumerate(chapters):
            chapter.number = i + 1
            chapter.content = self._fetch_chapter_content(chapter)

        return self.book_title, chapters


def main():
    """Simple test runner."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python epub_parser.py <path-to-epub>")
        sys.exit(1)

    parser = EpubParser()
    title, chapters = parser.parse(sys.argv[1])

    print(f"Book: {title}")
    print(f"Chapters: {len(chapters)}")
    for ch in chapters[:5]:  # Show first 5
        print(f"  {ch.number}: {ch.title}")


if __name__ == "__main__":
    main()
