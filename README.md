# how-to-read-a-book

Transform EPUB ebooks into chapter-level Markdown sources for NotebookLM, paired with an analytical reading companion persona based on Mortimer J. Adler and Charles van Doren's classic methodology.

![Demo](https://img.shields.io/badge/tested-works-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

**A Claude Code skill** — Let your AI agent handle the technical work while you focus on deep reading.

---

## What It Does

This skill takes an EPUB file, splits it into chapters, and uploads them to NotebookLM as separate sources. Each chapter becomes individually addressable, so you can ask questions like *"What is the main argument of Chapter 3?"* or *"How does Chapter 7 relate to the author's thesis in Chapter 1?"*

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

Once the skill is installed, simply mention you want to read a book with NotebookLM:

> "I want to read *Thinking, Fast and Slow* on NotebookLM. The EPUB is at `~/Downloads/thinking-fast-and-slow.epub`"

The agent will:
1. Parse your EPUB and extract chapters
2. Create a NotebookLM notebook: `{Book Title} — Reading Companion`
3. Configure the Analytical Reading Companion persona
4. Upload all chapters as separate sources
5. Provide you with the NotebookLM URL to start reading

### Example Session

**You:** "Upload my book to NotebookLM. It's at `/Users/me/Books/TheHumanUseOfHumanBeings.epub`"

**Agent:**
```
📖 Found: The Human Use of Human Beings.epub
📚 Extracted: 15 chapters
📓 Created notebook: The Human Use of Human Beings — Reading Companion
⚙️  Configured reading companion persona
📤 Uploaded all 15 chapters
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
2. **Splits chapters** — Creates Markdown files with chapter metadata
3. **Creates notebook** — `{Book Title} — Reading Companion`
4. **Injects persona** — Configures the Analytical Reading Companion system prompt
5. **Uploads sources** — Each chapter becomes an addressable source
6. **Cleans up** — Removes temporary files

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
├── assets/
│   └── reading_companion_prompt.txt
├── scripts/
│   ├── run.py             # Main orchestration
│   ├── epub_parser.py     # EPUB parsing
│   └── notebooklm_client.py
├── package.json           # Skill metadata
├── requirements.txt       # Python dependencies
└── install.sh            # Setup helper
```

## Limitations

- **EPUB format only** — PDF, MOBI, AZW not supported
- **Local files only** — No URL downloading
- **Single persona** — One universal reading companion
- **Requires auth** — You must be logged into NotebookLM (`notebooklm login`)

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
```

## Inspired By

- [CNinfo2Notebookllm](https://github.com/jarodise/CNinfo2Notebookllm) — Pattern reference
- *How To Read a Book* by Mortimer J. Adler & Charles van Doren — The methodology

## License

MIT License — see [LICENSE](LICENSE)

## Acknowledgments

Created with Claude Code. The reading companion persona adapts the classical analytical reading methodology from Adler & van Doren.
