# PolyTranslate

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/tests-638%20passed-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Modern desktop translation application with beautiful UI, CLI mode, and support for multiple translation services**

[Features](#-key-features) • [Installation](#-installation) • [Usage](#-usage) • [Supported Services](#-supported-services) • [Development](#-development)

</div>

---

## 📋 Overview

PolyTranslate is a feature-rich translation application with a **modern UI** and a **full CLI mode**, built with Python and CustomTkinter. Translate text and documents using multiple translation APIs simultaneously, compare results, and manage terminology with a built-in glossary.

## 🆕 What's New in v3.1

- **⚙️ Pydantic Settings**: Config validation powered by Pydantic schemas instead of hand-rolled validators
- **🖥️ Click CLI**: CLI rewritten with Click — auto-generated help, type validation, cleaner code
- **⚡ Chunk Deduplication**: Identical text segments translated only once per service in parallel mode
- **🧠 Detection Cache**: Language detection results cached (LRU, 256 entries) — no redundant API calls
- **🌊 Streaming Translation**: LLM services stream tokens as they generate — live preview in GUI and CLI (`--stream`)

<details>
<summary>Previous versions</summary>

**v3.0 — Export & Plugins**: Export to DOCX/PDF/XLIFF, TMX exchange, SRT/ASS subtitles, plugin system, modular GUI.

**v2.6 — Batch Folder Translation**: Translate all files in a directory at once (GUI, CLI, API). Custom extensions, output directories, error resilience.

**v2.5 — CLI Mode**: Full command-line interface for scripting, automation, and terminal workflows.

**v2.4 — Multi-Agent Voting**: Multiple AI agents vote on translation quality with weighted consensus. Ren'Py context awareness for visual novel translation.

**v2.3 — AI Evaluation**: Rate translations with scores (0-10), explanations, and AI-generated improvements.

**v2.2 — Editable Translations**: Edit translations directly in the interface with auto-save. Original text comparison.

**v2.1 — Tabbed Interface**: All features in one window with integrated tabs.

</details>

### ✨ Key Features

- **9 Translation Services**: DeepL (FREE), Google (FREE), Yandex (FREE), OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI
- **11 File Formats**: TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, Markdown, Ren'Py scripts, SRT subtitles, ASS/SSA subtitles
- **🆓 FREE Services**: DeepL, Google, and Yandex work without API keys (with built-in rate limiting)
- **📁 Batch Folder Translation**: Translate all files in a directory at once
- **⌨️ CLI Mode**: Full command-line interface for scripting and automation
- **🤖 AI Evaluation**: Rate translation quality with scores, explanations, and improvements
- **🗳️ Multi-Agent Voting**: Multiple AI agents vote on translations with weighted consensus
- **🎮 Ren'Py Context**: Game-aware translation with character/scene context extraction
- **📤 Export**: Save results to DOCX, PDF, or XLIFF with original text formatting
- **🔄 TMX Exchange**: Export/import translation cache in standard TMX format for CAT tools
- **🔌 Plugin System**: Add custom translation services via Python entry points — no code changes needed
- **Translation Cache**: Avoid redundant API calls — cached results reused automatically
- **Parallel Processing**: Translate large texts in chunks with multiple workers
- **🔀 Diff View**: VS Code-style line-by-line diff with per-line revert buttons
- **Glossary & History**: Built-in glossary editor and translation history
- **Dark/Light Themes**: Toggle between light and dark themes
- **Drag & Drop**: Easy file loading with visual feedback

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Quick Install

```bash
git clone https://github.com/GoonerTim/PolyTranslate.git
cd PolyTranslate
pip install -r requirements.txt
python main.py
```

> **Reproducible install**: Use `pip install -r requirements.lock` to install exact pinned versions of all dependencies.

### Development Install

```bash
pip install -r requirements-dev.txt
pre-commit install
```

---

## 📖 Usage

### GUI Mode

```bash
python main.py
```

1. **Load Text**: Drag & drop a file or click "Open"
2. **Select Languages**: Choose source (or Auto) and target
3. **Select Services**: Check one or more translation services
4. **Translate**: Click "🚀 Translate"
5. **View Results**: Results, Comparison, Diff, AI Evaluation, History, Glossary tabs

**Batch Folder**: Click "📁 Translate Folder" → select folder → confirm → watch per-file progress.

### ⌨️ CLI Mode

```bash
# Translate text
python main.py translate "Hello world" -t ru
python main.py t "Hello world" -t de              # short alias

# Translate with specific services
python main.py translate "Hello" --services deepl google --all-services

# Translate a file
python main.py translate -f document.pdf -s en -t ru -o output.txt

# JSON output for scripting
python main.py translate "Hello" --format json

# Streaming mode (LLM tokens shown as they arrive)
python main.py translate "Hello world" -t ru --stream

# Pipe from stdin
echo "Hello world" | python main.py translate -t ru

# Batch folder translation
python main.py translate -d /path/to/game/ -t ru
python main.py translate -d /game/ -t ru --extensions .rpy .txt --output-dir /output/

# Export results to DOCX/PDF/XLIFF
python main.py translate -f doc.txt -t ru --export results.docx
python main.py translate "Hello" -t de --export output.xliff

# Translation cache TMX exchange (for CAT tools)
python main.py cache export-tmx memory.tmx
python main.py cache import-tmx memory.tmx

# Detect language
python main.py detect "Bonjour le monde"

# List services / languages
python main.py services
python main.py languages

# Configuration
python main.py config
python main.py config --set target_language de
python main.py config --set-key openai sk-your-key-here
```

| Command | Alias | Description |
|---------|-------|-------------|
| `translate` | `t` | Translate text, file, or directory |
| `services` | `s` | List available translation services |
| `languages` | `l` | List supported languages |
| `detect` | `d` | Detect language of text |
| `cache` | — | Export/import translation cache (TMX) |
| `config` | `c` | Show or update configuration |

### AI Evaluation & Multi-Agent Voting

1. Configure AI service in **Settings** → **AI Evaluation Settings**
2. Optionally add agents in **Settings** → **AI Agents** (for multi-agent voting)
3. Translate text, then click **"🤖 Evaluate All"** or **"🤖 Agent Vote"**
4. View scores (0-10), explanations, best translation, and AI-improved version

### Ren'Py Game Translation

1. Set **Game Folder** in **Settings** → **Ren'Py Settings**
2. Choose **Processing Mode**: By Scenes (recommended), By Chunks, or Full File
3. Open a `.rpy` file and translate — AI receives game context automatically

### Configuration

**Start translating immediately** with DeepL, Google, and Yandex (no API keys required)!

For other services, configure API keys in **Settings**:
- **DeepL / Google / Yandex**: ✅ Works FREE without API key
- **ChatGPT Proxy**: ✅ No API key required
- **OpenAI / Claude / Groq / OpenRouter**: Requires API key
- **LocalAI**: Requires local server URL

---

## 🔌 Supported Services

| Service | API Key | Features | Languages |
|---------|---------|----------|-----------|
| **DeepL** | 🆓 Optional | Free API, high quality | 30+ |
| **Google Translate** | 🆓 Optional | Free API, comprehensive | 100+ |
| **Yandex Translate** | 🆓 Optional | Free API, good for Cyrillic | 90+ |
| **ChatGPT Proxy** | ❌ No | Free, no registration | 100+ |
| **OpenAI GPT** | ✅ Yes | GPT-4.1, GPT-4o, o3-mini | All major |
| **Claude AI** | ✅ Yes | Sonnet 4.6, Haiku 4.5 | All major |
| **Groq** | ✅ Yes | Llama 3.3, Gemma 2, Mixtral | All major |
| **OpenRouter** | ✅ Yes | Any model via aggregator | All major |
| **LocalAI** | ❌ No* | Self-hosted, private | Depends on model |

*Requires local server setup

---

## 🛠️ Development

### Project Structure

```
PolyTranslate/
├── app/
│   ├── config/          # Configuration management
│   ├── core/            # Core translation logic
│   │   ├── batch_translator.py  # Batch folder translation
│   │   ├── renpy_context.py     # Ren'Py game context extractor
│   │   └── ...
│   ├── gui/             # Modern CustomTkinter UI
│   │   ├── main_window.py       # Main window orchestrator (~600 lines)
│   │   ├── tabs/                # Tab rendering mixins (6 modules)
│   │   ├── workflows/           # Translation workflow mixins (3 modules)
│   │   ├── widgets/             # Reusable widgets (diff, file drop, progress)
│   │   └── settings_dialog.py   # Settings dialog
│   ├── services/        # Translation service implementations
│   │   └── ...
│   ├── utils/           # Utilities (glossary, cache, rate limiter)
│   └── cli.py           # Command-line interface
├── tests/               # Test suite (652 tests, 93% coverage)
├── main.py              # Entry point (GUI or CLI)
└── pyproject.toml       # Project configuration
```

### Commands

```bash
pytest                       # Run all tests with coverage
ruff check . && ruff format . --check  # Lint and format check
mypy app/                    # Type checking
pre-commit run --all-files   # Run all pre-commit hooks
pyinstaller build.spec       # Build executable
```

### Architecture

- **Translator**: Orchestrates translation workflow, manages services
- **BatchTranslator**: Batch folder translation
- **AIEvaluator**: AI-powered translation quality analysis
- **AgentVoting**: Multi-agent voting with weighted consensus
- **FileProcessor**: File format reading/writing (11 formats incl. SRT/ASS subtitles)
- **Settings**: Pydantic-validated configuration (types, ranges, model lists)
- **Glossary / LanguageDetector**: Term replacement, language detection
- **PluginLoader**: Discovers services via `polytranslate.services` entry points

### 🔌 Writing a Plugin

Create a Python package with a class that extends `TranslationService`:

```python
# my_service/plugin.py
from app.services.base import TranslationService
from app.config.settings import Settings

class MyService(TranslationService):
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.get_api_keys().get("myservice", "")

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        ...  # call your API

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_name(self) -> str:
        return "My Service"
```

Register it in your package's `pyproject.toml`:

```toml
[project.entry-points."polytranslate.services"]
myservice = "my_service.plugin:MyService"
```

Install the package (`pip install .`) and PolyTranslate will discover it automatically.

---

## 📊 Testing

- **652 tests**, **93% coverage** (GUI excluded)
- Service mocking, AI evaluation, agent voting, batch translation, CLI, streaming, settings validation, file formats, integration tests

---

## 🌍 Supported Languages

40+ languages including: English, Russian, German, French, Spanish, Italian, Dutch, Polish, Portuguese, Chinese, Japanese, Korean, Arabic, Turkish, Ukrainian, Czech, Swedish, Danish, Finnish, Norwegian, Hungarian, Greek, Hebrew, Thai, Vietnamese, Indonesian, and more.

*Language availability depends on the selected translation service*

---

## 🔒 Privacy & Security

- **Local Processing**: Files processed locally
- **No Tracking**: No analytics or user tracking
- **Self-Hosted Option**: Use LocalAI for complete privacy

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork → Create branch → Make changes → Run tests → PR

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🐛 Bug Reports

Please use [GitHub Issues](https://github.com/GoonerTim/PolyTranslate/issues).

---

<div align="center">
Made with ❤️ by GoonerTim
</div>
