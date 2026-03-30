# how-to-read-a-book

Transform EPUB ebooks into chapter-level Markdown sources for NotebookLM, paired with an analytical reading companion persona based on Mortimer J. Adler and Charles van Doren's classic methodology.

![Demo](https://img.shields.io/badge/tested-works-green)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

## What It Does

This skill takes an EPUB file, splits it into chapters, and uploads them to NotebookLM as separate sources. Each chapter becomes individually addressable, so you can ask questions like *"What is the main argument of Chapter 3?"* or *"How does Chapter 7 relate to the author's thesis in Chapter 1?"*

The NotebookLM notebook is configured with a custom **Analytical Reading Companion** persona that guides you through deep reading using the four levels from *How To Read a Book*:

- **Inspectional Reading** — What is this book about as a whole?
- **Analytical Reading** — What is the author trying to prove? How is the argument structured?
- **Syntopical Reading** — How do chapters relate? What patterns emerge?

## Demo

```bash
$ python scripts/run.py ~/Downloads/TheHumanUseOfHumanBeings.epub

📖 Validating EPUB file...
✅ Found: The Human Use of Human Beings.epub
📚 Parsing EPUB structure...
✅ Found: 15 chapters
📕 Title: The Human Use of Human Beings
✍️  Converting chapters to Markdown...
✓ 01-guide.md
✓ 02-icybernetics-in-history.md
✓ 03-iiprogress-and-entropy.md
...
📓 Creating NotebookLM notebook...
✅ Created notebook: 7678897e-a880-4036-b26f-cf1b56b6f176
⚙️  Configuring reading companion persona...
📤 Uploading chapters to NotebookLM...
✅ Uploaded all 15 chapters
🧹 Cleaning up...

🎉 SUCCESS!
📚 Notebook: The Human Use of Human Beings — Reading Companion
🔗 Notebook URL: https://notebooklm.google.com/notebook/7678897e-a880-4036-b26f-cf1b56b6f176
```

## Installation

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- NotebookLM account (Google)

### Quick Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/how-to-read-a-book.git
cd how-to-read-a-book

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or with pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Authenticate with NotebookLM
notebooklm login
```

### Alternative: Use the install script

```bash
./install.sh
```

## Usage

```bash
python scripts/run.py /path/to/your/book.epub
```

After running, you'll receive a NotebookLM URL where you can start your analytical reading session.

### Example Session

Once your book is uploaded, try asking:

- "What is the main problem this book is trying to solve?"
- "Summarize the author's argument in Chapter 5"
- "What assumptions does the author make that we should question?"
- "How does Chapter 7 relate to the themes introduced in Chapter 2?"
- "What is the author's thesis, and how do the chapters support it?"

## How It Works

1. **EPUB Parsing** — Uses `ebooklib` to extract the table of contents (TOC-first) with heading-based fallback for poorly formatted EPUBs
2. **Chapter Splitting** — Converts each chapter to Markdown with YAML frontmatter containing chapter number, title, and book source
3. **Notebook Creation** — Creates a new NotebookLM notebook titled `{Book Title} — Reading Companion`
4. **Persona Injection** — Configures the notebook with the Analytical Reading Companion system prompt
5. **Batch Upload** — Uploads all chapter Markdown files as individual sources
6. **Cleanup** — Removes temporary files after successful upload

## The Reading Companion Persona

The persona is based on the methodology from *How To Read a Book* and guides you to:

- **Find the unity** — What single question is the author answering?
- **Analyze the argument** — What are the premises, reasoning, and conclusions?
- **Question fairly** — Distinguish knowledge from opinion; criticize only after understanding
- **Synthesize** — How do chapters relate? What patterns emerge across the book?

See `assets/reading_companion_prompt.txt` for the full system prompt.

## File Structure

```
how-to-read-a-book/
├── scripts/
│   ├── run.py              # Main orchestration script
│   ├── epub_parser.py      # EPUB parsing with TOC + fallback
│   └── notebooklm_client.py # NotebookLM CLI wrapper
├── assets/
│   └── reading_companion_prompt.txt  # Analytical reading persona
├── SKILL.md                # Agent instructions (for Claude Code)
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── install.sh              # Setup script
└── package.json            # Skill metadata
```

## Requirements

- Python 3.10+
- `ebooklib` — EPUB parsing
- `beautifulsoup4` — HTML content extraction
- `notebooklm-py` — NotebookLM CLI
- `lxml` — XML parsing

## Limitations

- **EPUB format only** — PDF, MOBI, AZW not supported
- **Local files only** — No URL downloading
- **Single persona** — One universal reading companion (no book-type variations)
- **Authentication required** — You must be logged into NotebookLM

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `notebooklm command not found` | Run `pip install notebooklm-py playwright && playwright install chromium` |
| `Not authenticated` | Run `notebooklm login` and authenticate in browser |
| `EPUB file not found` | Check the file path; use absolute path if needed |
| `Could not extract chapters` | Some EPUBs have unusual structure; try converting with Calibre first |
| Chapter titles look wrong | EPUB might have poor metadata; skill falls back to heading detection |

## Development

### Testing

```bash
# Test EPUB parsing only
python scripts/epub_parser.py /path/to/book.epub

# Run full skill
python scripts/run.py /path/to/book.epub
```

### Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

## Inspired By

- [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) — Pattern reference for NotebookLM integration
- *How To Read a Book* by Mortimer J. Adler and Charles van Doren — The analytical reading methodology

## License

MIT License — see LICENSE file for details.

## Acknowledgments

Created with Claude Code. The reading companion persona is adapted from the classical analytical reading methodology developed by Mortimer J. Adler and Charles van Doren.
