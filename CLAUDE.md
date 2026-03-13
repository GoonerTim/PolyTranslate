# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PolyTranslate** - Modern translation application with beautiful GUI and full CLI mode. Supports 9 translation services (DeepL FREE, Google FREE, Yandex FREE, OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI) and 9 file formats (TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py). Built with Python 3.10+ and CustomTkinter GUI.

### Key Features (v2.6)
- **🆓 FREE Translation**: DeepL, Google, and Yandex work without API keys using unofficial public APIs
- **🎨 Modern UI**: Redesigned interface with gradients, icons, animations, card-based layout, tabbed interface
- **📁 Batch Folder Translation**: Translate all files in a directory at once — GUI, CLI, and core API (v2.6)
- **⌨️ CLI Mode**: Full command-line interface for scripting, automation, and terminal workflows (v2.5)
- **🤖 AI-Powered Evaluation**: Rate translation quality with scores (0-10), explanations, and AI-generated improvements
- **🗳️ Multi-Agent Voting**: Multiple AI agents (local + cloud) independently evaluate and vote on best translations (v2.4)
- **🎮 Ren'Py Context Awareness**: Game context extraction (characters, scenes, dialogue) for smarter translation of visual novels (v2.4)

## Common Commands

### Running the Application
```bash
# GUI mode
python main.py

# CLI mode
python main.py translate "Hello world" -t ru
python main.py --help

# Batch folder translation (CLI)
python main.py translate -d /path/to/game/ -t ru
python main.py translate -d /path/to/game/ -t ru --extensions .rpy .txt --output-dir /output/
```

### Testing
```bash
# All tests with coverage (requires 70%+)
pytest

# Specific test file
pytest tests/test_translator.py -v

# Single test method
pytest tests/test_translator.py::TestTranslator::test_translate_success -v

# Generate HTML coverage report
pytest --cov-report=html
```

### Code Quality
```bash
# Run all quality checks at once
pytest && ruff check . && ruff format . --check && mypy app/

# Linting (auto-fix available)
ruff check .
ruff check . --fix

# Formatting
ruff format .
ruff format . --check  # Check only

# Type checking (expect ~36 warnings from GUI libraries)
mypy app/
```

### Pre-commit Hooks
```bash
pre-commit install          # One-time setup
pre-commit run --all-files  # Manual run
```

### Building
```bash
pyinstaller build.spec      # Creates dist/PolyTranslate/
```

## Architecture

### Core Translation Flow
```
User Input (File/Text)
  → FileProcessor.process_file() [Extracts text from various formats]
  → Translator.split_text() [Breaks into sentence chunks]
  → Translator.translate_parallel() [Uses ThreadPoolExecutor]
      → For each chunk + service:
          → TranslationService.translate() [API call to service]
      → Collect results
  → Reassemble chunks
  → Glossary.apply() [Post-processing term replacement]
  → Display in GUI tabs
```

### Service Architecture Pattern

All translation services **must** implement `app/services/base.py::TranslationService`:

```python
class TranslationService(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str

    @abstractmethod
    def is_configured(self) -> bool

    @abstractmethod
    def get_name(self) -> str
```

Services are **dynamically initialized** in `Translator._initialize_services()`.

**Important:** DeepL, Google, and Yandex services are **always initialized** (even without API keys) because they support free unofficial APIs as fallback:
- If API key exists: tries paid API first, falls back to free API on failure
- If no API key: uses free API directly
- `is_configured()` always returns `True` for these services
- **Rate Limiting**: All free services use `RateLimiter` (class-level, thread-safe) to enforce minimum interval between requests (DeepL: 1.0s, Google: 0.5s, Yandex: 0.5s); automatically retries with exponential backoff (2s, 4s, 8s) on HTTP 429 errors

### Key Architectural Decisions

1. **Parallel Processing**: `Translator.translate_parallel()` uses `ThreadPoolExecutor` to translate multiple chunks across multiple services concurrently. Configurable via `max_workers` and `chunk_size`.

2. **Sentence Tokenization**: Uses NLTK's `sent_tokenize()` with `SimpleTokenizer` fallback if NLTK data unavailable.

3. **Language Detection**: `LanguageDetector.detect()` wraps `langdetect` library with graceful degradation (returns None if unavailable or text too short).

4. **Settings Persistence**: `Settings` class manages JSON-based config in `config.json`. Uses deep merge strategy for updates (`_deep_merge()` method).

5. **GUI-Core Separation**: GUI (`app/gui/`) is completely decoupled from core logic (`app/core/`). Communication via callbacks and threading to prevent UI freezing.

6. **Free API Fallback**: DeepL, Google, and Yandex services implement automatic fallback to unofficial free APIs when API key is missing or paid API fails.

### File Processing Strategy

`FileProcessor` uses a **strategy pattern** with format-specific static methods:
- `read_txt()`, `read_pdf()`, `read_docx()`, etc.
- `process_file()` dispatches based on file extension
- `process_bytes()` for in-memory processing
- Special handling for Ren'Py (`.rpy`) with dialogue extraction and reconstruction
- `split_rpy_by_scenes()`: Splits `.rpy` content by `label` blocks into `(label_name, scene_content)` tuples

### Module Responsibilities

**CLI** (v2.5):
- **`app/cli.py`**: Command-line interface with 5 commands (translate, services, languages, detect, config)
  - `cmd_translate()`: Translates text/file with progress bar and file info header (name, languages, services), supports stdin pipe, JSON output
  - `_cmd_translate_directory()`: Batch folder translation with per-file progress (v2.6)
  - CLI flags for batch: `-d`/`--directory`, `--output-dir`, `--extensions`, `--no-recursive`, `--service`
  - Smart dispatch in `main.py`: CLI commands auto-detected from `sys.argv[1]`, falls back to GUI

**Core Logic**:
- **`app/core/translator.py`**: Orchestrates entire translation workflow, manages service lifecycle
- **`app/core/batch_translator.py`**: Batch folder translation (v2.6)
  - `BatchTranslator`: Orchestrates file discovery and per-file translation
  - `find_files()`: Discovers files by extensions, recursive or not (default: `.rpy`)
  - `translate_file()`: Translates single file, saves with language suffix (`script.rpy` → `script_ru.rpy`)
  - `translate_folder()`: Translates all matching files with progress callback
  - `BatchFileResult` / `BatchProgress`: Dataclasses for results and progress tracking
  - For `.rpy` files: extracts dialogue, translates, reconstructs via `FileProcessor.reconstruct_rpy()`
  - Output directory support with relative path preservation; failed files skipped
- **`app/core/file_processor.py`**: File format handling (9 formats), encoding detection, content extraction
- **`app/core/language_detector.py`**: Wrapper around langdetect with availability checks
- **`app/core/renpy_context.py`**: Ren'Py game context extractor — parses characters, scenes, dialogue from `.rpy` files

**Configuration**:
- **`app/config/settings.py`**: JSON persistence, API key management, config deep merge, settings validation
  - `OPENAI_MODELS`, `CLAUDE_MODELS`, `GROQ_MODELS`: Canonical model lists (single source of truth for services, settings, and GUI)
  - `VALIDATORS`: Declarative validation rules (type, choices, min/max) for known keys
  - `validate()` called by `set()` — enforces types, ranges, allowed values, and model names
- **`app/config/languages.py`**: Language code mappings for different services

**Services** (with FREE API support):
- **`app/services/deepl.py`**: DeepL - **FREE mode** (unofficial JSON-RPC API) + paid API with fallback
- **`app/services/google.py`**: Google Translate - **FREE mode** (unofficial API) + paid API with fallback
- **`app/services/yandex.py`**: Yandex Translate - **FREE mode** (unofficial API) + paid API with fallback
- **`app/services/openai_service.py`**: OpenAI GPT (requires API key)
- **`app/services/claude.py`**: Claude AI (requires API key)
- **`app/services/groq_service.py`**: Groq (requires API key)
- **`app/services/openrouter.py`**: OpenRouter (requires API key)
- **`app/services/chatgpt_proxy.py`**: ChatGPT Proxy (no key required)
- **`app/services/localai.py`**: LocalAI (self-hosted)
- **`app/services/ai_evaluator.py`**: AI-powered translation evaluation — scores (0-10), explanations, improved translations
- **`app/services/agent_voting.py`**: Multi-agent voting system — parallel voting, weighted consensus, graceful degradation

**Modern UI** (excluded from test coverage):
- **`app/gui/main_window.py`**: Main window with 6 tabs (Results, Comparison, Diff, AI Evaluation, History, Glossary)
  - "📁 Translate Folder" button: batch folder translation with confirmation, threaded execution, per-file progress (v2.6)
  - Agent voting integration, dynamic evaluate button text
- **`app/gui/widgets/diff_view.py`**: VS Code-style line-by-line diff with per-line revert buttons (`↩`), color-coded `+`/`-` lines, stats
- **`app/gui/widgets/file_drop.py`**: Drag-drop zone
- **`app/gui/widgets/progress.py`**: Progress bar
- **`app/gui/settings_dialog.py`**: Settings dialog with AI Agents and Ren'Py sections
- **`app/gui/history_view.py`**: TranslationHistory class for persistence

**Utilities**:
- **`app/utils/glossary.py`**: Term dictionary with post-processing replacement, JSON persistence
- **`app/utils/logging.py`**: Structured logging setup — file handler (`polytranslate.log`) + optional console handler
- **`app/utils/cache.py`**: Translation cache — in-memory + JSON persistence, LRU eviction, thread-safe
- **`app/utils/rate_limiter.py`**: Thread-safe rate limiter — enforces minimum interval between free API requests, used by DeepL (1.0s), Google (0.5s), Yandex (0.5s)

### Testing Strategy

**457 tests, 91% coverage** (GUI excluded)

- **Service Tests**: Mock HTTP with `responses` library
- **Free API Tests**: Test fallback mechanism for DeepL, Google, and Yandex
- **Diff View Tests** (`tests/test_diff_view.py`): 10 tests (diff logic, revert, edge cases)
- **Settings Tests** (`tests/test_settings.py`): 43 tests (includes validation for types, ranges, models)
- **Rate Limiter Tests** (`tests/test_rate_limiter.py`): 8 tests, 100% coverage
- **AI Evaluator Tests** (`tests/test_ai_evaluator.py`): 19 tests, 97% coverage
- **Agent Voting Tests** (`tests/test_agent_voting.py`): 25 tests, 95% coverage
- **Ren'Py Context Tests** (`tests/test_renpy_context.py`): 13 tests, 92% coverage
- **Ren'Py Scene Splitting Tests** (`tests/test_file_processor_renpy_scenes.py`): 6 tests
- **CLI Tests** (`tests/test_cli.py`): 42 tests (includes batch directory tests)
- **Batch Translator Tests** (`tests/test_batch_translator.py`): 25 tests, 88% coverage
- **Integration Tests** (`tests/test_integration.py`): End-to-end workflows
- **File Format Tests** (`tests/test_file_processor_formats.py`): Actual file creation and extraction
- **Fixtures** (`tests/conftest.py`): `temp_dir`, `sample_txt_file`, `sample_rpy_content`

### Configuration Files

Runtime config (gitignored):
- **`config.json`**: API keys, theme, chunk_size, max_workers, selected_services, ai_evaluator_service, agents, renpy_game_folder, renpy_processing_mode, cache_enabled, cache_max_size
- **`cache.json`**: Translation cache (auto-generated, gitignored)
- **`glossary.json`**: User term dictionary
- **`history.json`**: Translation history with evaluation scores

## Adding New Features

### Add Translation Service

**Standard Service (requires API key)**:
1. Create `app/services/newservice.py` implementing `TranslationService` (translate, is_configured, get_name)
2. Register in `app/services/__init__.py`
3. Add initialization in `Translator._initialize_services()`
4. Create `tests/services/test_newservice.py` with mocked HTTP

**Service with Free API Fallback** (like Google/Yandex):
1. Implement `_translate_with_api_key()` and `_translate_free()` methods
2. `translate()` tries paid API first, falls back to free on error
3. `is_configured()` always returns `True`
4. Add class-level `_rate_limiter = RateLimiter(min_interval=...)` and call `self._rate_limiter.wait()` before each free API request

### Add Voting Agent Type

1. Add case in `AgentVoting._create_agent_client()`
2. Add to `SettingsDialog.AGENT_TYPES` list
3. Add tests in `tests/test_agent_voting.py`

### Add File Format

1. Add method in `FileProcessor`: `read_newformat(content: bytes) -> str`
2. Update `SUPPORTED_EXTENSIONS` set
3. Add case in `process_bytes()` method
4. Add tests in `tests/test_file_processor_formats.py`

## Important Notes

- **Code Style**: Minimal docstrings in internal methods. Type hints used throughout.
- **Free Translation**: DeepL, Google, and Yandex work without API keys. May have rate limits or break if APIs change.
- **Type Checking**: Mypy reports ~36 warnings mostly from CustomTkinter. Expected and acceptable.
- **NLTK Data**: Downloaded at runtime in `main.py` if missing. Tests handle missing NLTK gracefully.
- **API Key Security**: Never commit `config.json`. Keys stored locally only.
- **Logging**: `setup_logging()` called in `main.py` at startup. All modules use `logging.getLogger(__name__)`. Logs written to `polytranslate.log`.
- **Translation Cache**: `TranslationCache` in `Translator` caches raw translations (before glossary). Key = text + source + target + service. LRU eviction, thread-safe, persisted to `cache.json`.
- **Coverage Target**: 70% minimum (pyproject.toml), currently 91% (426 tests). GUI excluded.
- **Ruff Configuration**: Line length 100, ignores E501, uses modern Python features (UP rules).
- **Language Code Mappings**: Different services use different codes. See `app/config/languages.py`.
- **GUI Threading**: All long-running operations must use `threading.Thread` with `root.after()` callbacks.
- **Ren'Py Processing**: `read_rpy()` extracts dialogue using regex. `reconstruct_rpy()` uses default parameters in closures to avoid variable binding issues (B007).
- **Parallel Translation Errors**: If a service fails, error message stored in results dict instead of raising (allows partial success).

## Known Quirks

1. **Free API Reliability**: Unofficial, may have rate limits, change without notice, or be blocked in some regions.
2. **Chinese Language Detection**: Returns `zh`, `zh-cn`, or `zh-tw` depending on langdetect confidence.
3. **Retry Logic**: DeepL, Google, and Yandex free APIs retry up to 3 times with exponential backoff (2s, 4s, 8s) on network errors and HTTP 429.
4. **Rate Limiter**: `RateLimiter` is class-level (shared across all instances), so parallel translation via `ThreadPoolExecutor` is properly throttled per service.
