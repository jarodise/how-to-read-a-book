#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB Parser Module - Extract book metadata, chapter structure, and images from EPUB files.

Uses TOC-first parsing with heading-based fallback for robust chapter detection.
Extracts embedded images for upload as separate sources.
"""

import os
import re
import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import unicodedata

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError as e:
    raise ImportError(f"Required packages not installed. Run: pip install ebooklib beautifulsoup4") from e


@dataclass
class Image:
    """Represents an image extracted from the EPUB."""
    name: str              # Original name in EPUB (e.g. "images/figure1.png")
    media_type: str        # MIME type (e.g. "image/png")
    data: bytes            # Raw binary data
    chapter_ref: Optional[int] = None  # Which chapter references this image


@dataclass
class Chapter:
    """Represents a single chapter from the book."""
    number: int
    title: str
    content: str  # HTML content
    href: Optional[str] = None
    image_names: List[str] = field(default_factory=list)  # Image names referenced by this chapter


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

    def _is_heading_important(self, text: str, document_name: Optional[str] = None) -> bool:
        """Check if a heading looks like a chapter title (not front/back matter)."""
        text_lower = text.lower().strip()
        doc_name_lower = (document_name or "").lower()

        # Skip if empty or too short
        if len(text_lower) < 2:
            return False

        # Skip if document name suggests it's a navigational file
        nav_patterns = ['nav.xhtml', 'toc.xhtml', 'cover.xhtml', 'title_page']
        if any(p in doc_name_lower for p in nav_patterns):
            return False

        # Skip if matches front/back matter patterns
        for pattern in self.FRONT_MATTER_PATTERNS + self.BACK_MATTER_PATTERNS:
            if pattern in text_lower:
                return False

        # Skip common non-chapter headings
        skip_patterns = ['copyright', 'notes', 'footnote', 'copyright page', 'start', 'cover']
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
                doc_name = item.get_name()

                # Find all headings in this document
                found_headings = []
                for tag in self.HEADING_TAGS:
                    for heading in soup.find_all(tag):
                        text = heading.get_text(strip=True)
                        if self._is_heading_important(text, doc_name):
                            found_headings.append((heading, text))

                if not found_headings:
                    continue

                # If only one primary heading is found in the document, treatment depends on size
                # Usually better to take the whole document
                if len(found_headings) == 1:
                    heading, text = found_headings[0]
                    chapter_num += 1
                    chapters.append(Chapter(
                        number=chapter_num,
                        title=text,
                        content=content, # Take the whole document content
                        href=doc_name
                    ))
                else:
                    # Multiple headings - slice by headings (TBD more complex slicing)
                    # For now, just take the first one or keep current simple parent logic
                    for heading, text in found_headings:
                        chapter_num += 1
                        chapters.append(Chapter(
                            number=chapter_num,
                            title=text,
                            content=str(heading.find_parent()) if heading.find_parent() else content,
                            href=doc_name
                        ))

        except Exception as e:
            pass

        return chapters

    def _extract_fallback_single_chapter(self) -> List[Chapter]:
        """
        Final fallback: If no chapters found, take the largest content document.
        """
        try:
            items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            content_items = []
            
            for item in items:
                name = item.get_name().lower()
                if 'nav' in name or 'cover' in name:
                    continue
                
                content = item.get_content().decode('utf-8', errors='ignore')
                text = BeautifulSoup(content, 'html.parser').get_text(strip=True)
                if len(text) > 100: # Significant text
                    content_items.append((len(text), item, content))
            
            if not content_items:
                return []
            
            # Sort by length and take the largest
            content_items.sort(key=lambda x: x[0], reverse=True)
            _, best_item, best_content = content_items[0]
            
            return [Chapter(
                number=1,
                title=self.book_title or "Full Book",
                content=best_content,
                href=best_item.get_name()
            )]
        except Exception:
            return []

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

    # Minimum image size in bytes to keep (skip spacers/decorators)
    IMAGE_MIN_SIZE = 1024  # 1KB

    # Supported image MIME types for NotebookLM upload
    SUPPORTED_IMAGE_TYPES = {
        'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'
    }

    def _extract_images(self) -> List[Image]:
        """
        Extract all meaningful images from the EPUB.
        Skips tiny spacer images (<1KB) and unsupported formats (SVG).
        """
        images = []
        seen_names = set()

        try:
            # Get images from ITEM_IMAGE
            for item in self.book.get_items_of_type(ebooklib.ITEM_IMAGE):
                name = item.get_name()
                media_type = item.media_type
                data = item.get_content()

                if name in seen_names:
                    continue
                seen_names.add(name)

                # Skip unsupported types (SVG, etc.)
                if media_type not in self.SUPPORTED_IMAGE_TYPES:
                    continue

                # Skip tiny images (spacers, bullets, decorators)
                if len(data) < self.IMAGE_MIN_SIZE:
                    continue

                images.append(Image(
                    name=name,
                    media_type=media_type,
                    data=data
                ))

            # Also check for cover images
            for item in self.book.get_items_of_type(ebooklib.ITEM_COVER):
                name = item.get_name()
                if name in seen_names:
                    continue
                seen_names.add(name)

                media_type = item.media_type
                data = item.get_content()

                if media_type not in self.SUPPORTED_IMAGE_TYPES:
                    continue
                if len(data) < self.IMAGE_MIN_SIZE:
                    continue

                images.append(Image(
                    name=name,
                    media_type=media_type,
                    data=data
                ))

        except Exception as e:
            # Non-fatal: proceed without images if extraction fails
            pass

        return images

    def _map_images_to_chapters(self, chapters: List[Chapter], images: List[Image]) -> None:
        """
        Scan chapter HTML for <img> tags and associate images with chapters.
        Updates chapter.image_names and image.chapter_ref in place.
        """
        # Build lookup: basename and full name -> image index
        image_lookup: Dict[str, int] = {}
        for idx, img in enumerate(images):
            image_lookup[img.name] = idx
            # Also index by basename for relative path matching
            basename = os.path.basename(img.name)
            if basename not in image_lookup:
                image_lookup[basename] = idx

        for chapter in chapters:
            if not chapter.content:
                continue

            soup = BeautifulSoup(chapter.content, 'html.parser')
            for img_tag in soup.find_all('img'):
                src = img_tag.get('src', '')
                if not src:
                    continue

                # Try matching by full path, basename, or URL-decoded variants
                matched_idx = None
                for candidate in [src, os.path.basename(src)]:
                    # Strip leading ../ or ./
                    cleaned = re.sub(r'^(\.\./)+', '', candidate)
                    cleaned = re.sub(r'^\./+', '', cleaned)
                    if cleaned in image_lookup:
                        matched_idx = image_lookup[cleaned]
                        break

                if matched_idx is not None:
                    img_obj = images[matched_idx]
                    if img_obj.name not in chapter.image_names:
                        chapter.image_names.append(img_obj.name)
                    if img_obj.chapter_ref is None:
                        img_obj.chapter_ref = chapter.number

    def parse(self, epub_path: str) -> Tuple[str, List[Chapter], List[Image]]:
        """
        Parse EPUB and return (book_title, chapters, images).

        Strategy:
        1. Try TOC-first extraction
        2. If TOC yields < 3 chapters, fall back to heading-based
        3. Fetch content for each chapter
        4. Extract and map images to chapters
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

        # Final fallback for single-document books
        if not chapters:
            chapters = self._extract_fallback_single_chapter()

        if not chapters:
            raise EpubParseError("Could not extract any chapters from EPUB")

        # Fetch full content for each chapter
        for i, chapter in enumerate(chapters):
            chapter.number = i + 1
            chapter.content = self._fetch_chapter_content(chapter)

        # Extract images and map to chapters
        images = self._extract_images()
        if images:
            self._map_images_to_chapters(chapters, images)

        return self.book_title, chapters, images


def main():
    """Simple test runner."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python epub_parser.py <path-to-epub>")
        sys.exit(1)

    parser = EpubParser()
    title, chapters, images = parser.parse(sys.argv[1])

    print(f"Book: {title}")
    print(f"Chapters: {len(chapters)}")
    for ch in chapters[:5]:  # Show first 5
        img_info = f" ({len(ch.image_names)} images)" if ch.image_names else ""
        print(f"  {ch.number}: {ch.title}{img_info}")
    print(f"Images: {len(images)}")
    for img in images[:10]:  # Show first 10
        ch_info = f" (ch.{img.chapter_ref})" if img.chapter_ref else ""
        print(f"  {os.path.basename(img.name)} [{img.media_type}] {len(img.data)}B{ch_info}")


if __name__ == "__main__":
    main()
