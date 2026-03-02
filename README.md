# Apple Notes MCP Server

> Powerful tools for automating Apple Notes using Model Context Protocol (MCP)

**Original project by [Henil C Alagiya](https://github.com/henilcalagiya/mcp-apple-notes)**  
**This fork maintained by [SaturdaysinthePark](https://github.com/SaturdaysinthePark/mcp-apple-notes)** — adds performance improvements and new tools for large note libraries.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Overview

Apple Notes MCP Server provides seamless integration of Apple Notes with any MCP-compatible client. It enables full note automation — including creating, reading, updating, deleting, searching, and filtering notes — through a secure AppleScript layer.

This fork extends the original with tools designed to work reliably with **large note libraries (500–1000+ notes)**, fixing timeout issues and adding date/title-based lookup.

---

## What's New in This Fork

### New Tools
| Tool | Description |
|------|-------------|
| `find_notes_by_title` | Search notes by title text (contains or exact match) — uses native AppleScript `whose` filtering |
| `find_notes_by_date` | Filter notes by creation or modification date range — uses epoch-based date arithmetic (locale-independent) |
| `get_most_recent_note` | Get the single most recently modified note with full content in one fast call |

### Bug Fixes & Performance Improvements
- **`find_notes_by_date`** — Replaced slow loop-based date iteration with AppleScript's native `whose` clause. Date literals like `date "2026-02-27"` are locale-dependent and silently fail on many macOS systems; this fork uses epoch arithmetic (`date "January 1, 2001" + N seconds`) which is always reliable.
- **`find_notes_by_title`** — Uses `whose name contains` for native server-side filtering instead of iterating all notes.
- **`list_all_notes`** — Now returns folder name, creation date, and modification date for each note.
- **`search_notes`** — Now matches keywords against both note **title** and body (previously body only). Fixed a comma-parsing bug that broke results for notes/folders with commas in their names (switched to `|||` delimiter).
- **60-second timeout** on all AppleScript calls — prevents the MCP agent from hanging indefinitely on slow operations.

---

## Requirements

- **macOS** — Required for AppleScript support
- **Python 3.10+** — Required for MCP SDK compatibility
- **Apple Notes** — Must be installed with iCloud sync enabled
- **MCP-compatible client** (e.g., Claude Desktop, Cursor, Continue.dev, Perplexity)

---

## Quick Start

### Step 1: Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Clone this fork

```bash
git clone https://github.com/SaturdaysinthePark/mcp-apple-notes.git
cd mcp-apple-notes
```

### Step 3: Add MCP Configuration

Point your MCP client at this local clone:

```json
{
  "mcpServers": {
    "apple-notes": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-apple-notes", "python", "-m", "mcp_apple_notes"]
    }
  }
}
```

Or, to use the original published package (without fork improvements):

```json
{
  "mcpServers": {
    "apple-notes": {
      "command": "uvx",
      "args": ["mcp-apple-notes@latest"]
    }
  }
}
```

> **Note:** Ensure your terminal/MCP client has Accessibility permission in **System Settings → Privacy & Security → Accessibility**.

---

## Available Tools

### Note Management (6 tools)

| Tool | Description |
|------|-------------|
| `create_note` | Create a note with HTML content in a specified folder |
| `read_note` | Read a note by ID — returns full content and metadata |
| `update_note` | Update a note's title and body by ID |
| `delete_note` | Delete a note by ID with name verification |
| `move_note` | Move a note to a different folder |
| `list_all_notes` | List all notes with name, ID, folder, creation date, and modification date |

### Folder Management (5 tools)

| Tool | Description |
|------|-------------|
| `create_folder` | Create a folder at root or nested path (up to 5 levels) |
| `read_folder` | Read folder details and list its notes and subfolders |
| `rename_folder` | Rename a folder by ID |
| `delete_folder` | Delete a folder by ID |
| `move_folder` | Move a folder to a different location |

### Search & Discovery (6 tools)

| Tool | Description |
|------|-------------|
| `search_notes` | Search notes by keywords — matches title **and** body |
| `find_notes_by_title` | Find notes whose title contains or exactly matches a string *(new)* |
| `find_notes_by_date` | Filter notes by creation or modification date range *(new)* |
| `get_most_recent_note` | Get the most recently modified note with full content *(new)* |
| `list_folder_with_structure` | Show folder hierarchy as a tree |
| `list_notes_with_structure` | Show folders + notes hierarchy as a tree |

---

## Tool Reference

### `find_notes_by_title`

Find notes whose title contains (or exactly matches) a search string.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | string | required | Text to search for in note titles |
| `exact` | boolean | `false` | If `true`, requires exact case-sensitive match. Default is case-insensitive contains. |

**Example agent prompt:** *"Find my notes about the budget meeting"*

---

### `find_notes_by_date`

Filter notes by creation or modification date. Results are sorted newest first.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date_type` | string | `"modified"` | Which date to filter on: `"created"` or `"modified"` |
| `after` | string | `""` | ISO 8601 date (e.g. `"2024-01-15"`). Include notes on or after this date. |
| `before` | string | `""` | ISO 8601 date (e.g. `"2024-12-31"`). Include notes on or before this date. |

At least one of `after` or `before` must be provided.

**Example agent prompts:**
- *"Summarize my notes from today"* → `date_type="modified", after="2026-02-27"`
- *"What did I write in January?"* → `date_type="created", after="2026-01-01", before="2026-01-31"`
- *"Show notes I haven't touched since last year"* → `date_type="modified", before="2025-12-31"`

---

### `get_most_recent_note`

Returns the single most recently modified note with its full content. No parameters required.

**Example agent prompt:** *"What was the last note I wrote?"*

---

### `search_notes`

Search all notes by comma-separated keywords. Matches against both title and body content.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `keywords` | string | Comma-separated keywords (e.g. `"budget, Q1, meeting"`) |

---

## Content Support

**HTML Formatting:** `<h1-h6>`, `<b>`, `<i>`, `<u>`, `<p>`, `<div>`, `<br>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<a>`

**Special Features:**
- Unicode and emoji support (🚀, ✅, 📝)
- Nested folder paths (up to 5 levels)
- Automatic character escaping
- Rich content with headers, lists, tables

---

## Architecture

```
MCP Client
    │
    ▼
FastMCP Server Layer  (server.py)
    │
    ▼
Tools Layer           (tools/notes_tools.py)
    │
    ▼
AppleScript Layer     (applescript/*.py)
    │
    ▼
Apple Notes (via osascript)
```

All AppleScript calls run with a **60-second timeout** to prevent agent hangs. Date filtering uses native `whose` clauses for performance with large libraries.

---

## Troubleshooting

### Notes not found for today's date
Ensure your MCP server is running the latest version of this fork (`git pull origin main`). The original package used locale-dependent date literals that silently fail on most macOS systems. This fork uses epoch arithmetic instead.

### AppleScript Permission Denied
Grant Accessibility permission to your terminal or MCP client:  
**System Settings → Privacy & Security → Accessibility**

### iCloud Notes not accessible
This server requires iCloud Notes sync to be enabled. Go to **System Settings → Apple ID → iCloud → Notes** and ensure it is turned on.

### Timeout errors on large libraries
`list_all_notes` and `list_notes_with_structure` iterate every note and can be slow with 1000+ notes. Prefer `find_notes_by_date`, `find_notes_by_title`, or `search_notes` for targeted lookups — these use native AppleScript filtering and return results much faster.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

**Original Author:** [Henil C Alagiya](https://github.com/henilcalagiya)  
- GitHub: [@henilcalagiya](https://github.com/henilcalagiya)
- LinkedIn: [Henil C Alagiya](https://linkedin.com/in/henilcalagiya)
- Original repo: [henilcalagiya/mcp-apple-notes](https://github.com/henilcalagiya/mcp-apple-notes)

**Fork Maintainer:** [SaturdaysinthePark](https://github.com/SaturdaysinthePark)  
- Fork repo: [SaturdaysinthePark/mcp-apple-notes](https://github.com/SaturdaysinthePark/mcp-apple-notes)
