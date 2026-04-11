# how-to-read-a-book

Transform EPUB ebooks into chapter-level Markdown sources for NotebookLM — including embedded images — paired with an analytical reading companion persona based on Mortimer J. Adler and Charles van Doren's classic methodology.

![Demo](https://img.shields.io/badge/tested-works-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

**A Claude Code skill** — Let your AI agent handle the technical work while you focus on deep reading.

---

## What It Does

This skill takes an EPUB file, splits it into chapters, extracts embedded images (diagrams, charts, figures), and uploads everything to NotebookLM as separate sources. Each chapter becomes individually addressable, so you can ask questions like *"What is the main argument of Chapter 3?"* or *"How does Chapter 7 relate to the author's thesis in Chapter 1?"* Images are uploaded alongside text, so visual content like diagrams and figures is available to the reading companion.

The NotebookLM notebook is configured with a custom **Analytical Reading Companion** persona that guides you through deep reading using the four levels from *How To Read a Book*:

- **Inspectional Reading** — What is this book about as a whole?
- **Analytical Reading** — What is the author trying to prove? How is the argument structured?
- **Syntopical Reading** — How do chapters relate? What patterns emerge?

## Installation

### For Claude Code

```bash
npx skills add jarodise/how-to-read-a-book
```

### For Other Agent Systems

Add the skill to your agent's skill directory using the installation method your system supports (may vary by agent platform).

## Prerequisites

Before using this skill, ensure you have:

1. **NotebookLM CLI installed and authenticated:**
   ```bash
   # Install notebooklm-py
   pip install notebooklm-py playwright
   playwright install chromium

   # Authenticate (one-time)
   notebooklm login
   ```

2. **An EPUB file locally available** on the system where the agent runs

## Usage

### Global CLI (Recommended)

Install the `notebook` command globally so you can run it from any terminal:

```bash
# One-time setup: create a symlink
ln -sf /path/to/howtoreadabook/notebook /usr/local/bin/notebook
```

Then from **anywhere**:

```bash
notebook ~/Downloads/ThinkingFastAndSlow.epub
```

### Via Agent Skill

Once the skill is installed, simply mention you want to read a book with NotebookLM:

> "I want to read *Thinking, Fast and Slow* on NotebookLM. The EPUB is at `~/Downloads/thinking-fast-and-slow.epub`"

The agent will:
1. Parse your EPUB and extract chapters
2. Extract embedded images (diagrams, charts, figures)
3. Create a NotebookLM notebook: `{Book Title} — Reading Companion`
4. Configure the Analytical Reading Companion persona
5. Upload all chapters and images as separate sources
6. Provide you with the NotebookLM URL to start reading

### Example Session

**You:** "Upload my book to NotebookLM. It's at `/Users/me/Books/TheHumanUseOfHumanBeings.epub`"

**Agent:**
```
📖 Found: The Human Use of Human Beings.epub
📚 Extracted: 15 chapters
🖼️  Found: 8 images
📓 Created notebook: The Human Use of Human Beings — Reading Companion
⚙️  Configured reading companion persona
📤 Uploaded all 15 chapters
🖼️  Uploaded 8 images
✅ Done!

🔗 Your notebook: https://notebooklm.google.com/notebook/abc-123

Try asking your reading companion:
• "What is the main problem this book is trying to solve?"
• "Summarize Chapter 5's key argument"
• "How does Chapter 7 relate to Chapter 2?"
```

### What to Ask Your Reading Companion

Once your book is in NotebookLM, try questions like:

- **Inspectional:** "What kind of book is this? What is it about as a whole?"
- **Analytical:** "What is the author's thesis? What premises support it?"
- **Critical:** "What assumptions does the author make?"
- **Syntopical:** "How does Chapter 5 relate to the argument in Chapter 2?"
- **Unity:** "What single question is this book trying to answer?"

## How It Works

Behind the scenes, the skill:

1. **Parses the EPUB** — Uses TOC-first detection with heading-based fallback
2. **Extracts images** — Pulls embedded PNG/JPG/GIF/WebP images (skips tiny spacers <1KB and SVGs)
3. **Maps images to chapters** — Scans `<img>` tags to associate images with their chapters
4. **Splits chapters** — Creates Markdown files with chapter metadata
5. **Creates notebook** — `{Book Title} — Reading Companion`
6. **Injects persona** — Configures the Analytical Reading Companion system prompt
7. **Uploads sources** — Each chapter and image becomes an addressable source
8. **Cleans up** — Removes temporary files

## The Reading Companion Persona

The persona is based on the methodology from *How To Read a Book* and guides you to:

- **Find the unity** — What single question is the author answering?
- **Analyze the argument** — What are the premises, reasoning, and conclusions?
- **Question fairly** — Distinguish knowledge from opinion; criticize only after understanding
- **Synthesize** — How do chapters relate? What patterns emerge?

The full system prompt is in [`assets/reading_companion_prompt.txt`](assets/reading_companion_prompt.txt).

## File Structure

```
how-to-read-a-book/
├── SKILL.md                 # Agent instructions
├── README.md               # This file
├── notebook                # CLI entry point (symlink-safe)
├── run.sh                  # Shell wrapper (venv activation)
├── assets/
│   └── reading_companion_prompt.txt
├── scripts/
│   ├── run.py             # Main orchestration
│   ├── epub_parser.py     # EPUB + image parsing
│   └── notebooklm_client.py  # NotebookLM API (text + image upload)
├── package.json           # Skill metadata
├── requirements.txt       # Python dependencies
└── install.sh            # Setup helper
```

## Limitations

- **EPUB format only** — PDF, MOBI, AZW not supported
- **Local files only** — No URL downloading
- **Single persona** — One universal reading companion
- **Requires auth** — You must be logged into NotebookLM (`notebooklm login`)
- **Image filtering** — Images under 1KB and SVGs are skipped (spacers, decorators)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `notebooklm command not found` | Ask your agent to run the setup, or install manually: `pip install notebooklm-py playwright && playwright install chromium` |
| `Not authenticated` | Run `notebooklm login` and authenticate in your browser |
| `Could not extract chapters` | Some EPUBs have unusual structures — try converting with Calibre first |
| Chapter titles look wrong | The skill falls back to heading detection when metadata is poor |

## For Developers

If you want to run the scripts directly without the agent skill:

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python scripts/run.py /path/to/book.epub

# Or use the CLI
./notebook /path/to/book.epub

# Or install globally (run from anywhere)
ln -sf "$(pwd)/notebook" /usr/local/bin/notebook
notebook /path/to/book.epub
```

## Inspired By

- [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) — Pattern reference
- *How To Read a Book* by Mortimer J. Adler & Charles van Doren — The methodology

## License

MIT License — see [LICENSE](LICENSE)

## Acknowledgments

Created with Claude Code. The reading companion persona adapts the classical analytical reading methodology from Adler & van Doren.
