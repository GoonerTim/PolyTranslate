# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PolyTranslate** - Modern translation application with beautiful GUI and full CLI mode. Supports 9 translation services (DeepL FREE, Google FREE, Yandex FREE, OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI) and 11 file formats (TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py, SRT, ASS/SSA). Built with Python 3.10+ and CustomTkinter GUI.

### Key Features (v3.0)
- **🆓 FREE Translation**: DeepL, Google, and Yandex work without API keys using unofficial public APIs
- **🎨 Modern UI**: Redesigned interface with gradients, icons, animations, card-based layout, tabbed interface
- **📤 Export Results**: Save translations to DOCX, PDF, or XLIFF with original text formatting (v3.0)
- **🔄 TMX Exchange**: Export/import translation cache in standard TMX 1.4b format for CAT tools (v3.0)
- **🏗️ Modular GUI**: Mixin-based architecture — main_window.py split into 10 focused modules (v3.0)
- **📁 Batch Folder Translation**: Translate all files in a directory at once — GUI, CLI, and core API
- **⌨️ CLI Mode**: Full command-line interface for scripting, automation, and terminal workflows
- **🤖 AI-Powered Evaluation**: Rate translation quality with scores (0-10), explanations, and AI-generated improvements
- **🗳️ Multi-Agent Voting**: Multiple AI agents (local + cloud) independently evaluate and vote on best translations
- **🎮 Ren'Py Context Awareness**: Game context extraction (characters, scenes, dialogue) for smarter translation of visual novels

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

# Translation cache TMX exchange
python main.py cache export-tmx memory.tmx
python main.py cache import-tmx memory.tmx
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
  → Translator.translate_parallel() [Uses asyncio.gather + asyncio.to_thread]
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

**LLM Base Class**: `app/services/llm_base.py::LLMTranslationService` — shared base for OpenAI-compatible services (OpenAI, Groq, OpenRouter, LocalAI). Claude overrides `_call_llm()` for Anthropic's API. Subclasses only define `_create_client()` and `_is_available()`.

Services are **dynamically initialized** in `Translator._initialize_services()`.

**Plugin System** (v3.0): External packages can register services via the `polytranslate.services` entry point group. `app/core/plugin_loader.py::discover_plugins()` scans `importlib.metadata.entry_points`, calls each factory with `Settings`, validates the result is a `TranslationService`, and returns `PluginInfo` objects. Plugins are loaded after built-in services; built-in IDs always take precedence. Broken plugins are logged and skipped.

**Important:** DeepL, Google, and Yandex services are **always initialized** (even without API keys) because they support free unofficial APIs as fallback:
- If API key exists: tries paid API first, falls back to free API on failure
- If no API key: uses free API directly
- `is_configured()` always returns `True` for these services
- **Rate Limiting**: All free services use `RateLimiter` (class-level, thread-safe) to enforce minimum interval between requests (DeepL: 1.0s, Google: 0.5s, Yandex: 0.5s); automatically retries with exponential backoff (2s, 4s, 8s) on HTTP 429 errors

### Key Architectural Decisions

1. **Parallel Processing**: `Translator.translate_parallel()` uses `asyncio.gather()` with `asyncio.to_thread()` to translate multiple chunks across multiple services concurrently. Configurable via `max_workers` (semaphore) and `chunk_size`. Falls back to synchronous execution if already inside a running event loop.

2. **Sentence Tokenization**: Uses NLTK's `sent_tokenize()` with `SimpleTokenizer` fallback if NLTK data unavailable.

3. **Language Detection**: `LanguageDetector.detect()` wraps `langdetect` library with graceful degradation (returns None if unavailable or text too short).

4. **Settings Persistence**: `Settings` class manages JSON-based config in `config.json`. Uses deep merge strategy for updates (`_deep_merge()` method).

5. **GUI-Core Separation**: GUI (`app/gui/`) is completely decoupled from core logic (`app/core/`). Communication via callbacks and threading to prevent UI freezing.

6. **GUI Mixin Architecture** (v3.0): `MainWindow` uses **mixin classes** to split responsibilities across files. Tab rendering (`app/gui/tabs/`) and workflow logic (`app/gui/workflows/`) are separate mixins that share `self` (the MainWindow instance). This avoids passing dozens of widget/state references while keeping files under ~300 lines.

7. **Free API Fallback**: DeepL, Google, and Yandex services implement automatic fallback to unofficial free APIs when API key is missing or paid API fails.

### File Processing Strategy

`FileProcessor` uses a **strategy pattern** with a class-level `_PROCESSORS` dict mapping extensions to method names:
- `process_file()` and `process_bytes()` dispatch via `_PROCESSORS` (no duplication)
- Document formats (TXT, PDF, DOCX, etc.) handled directly in `file_processor.py`
- **Subtitle formats** delegated to `app/core/subtitle_processor.py::SubtitleProcessor` (SRT/ASS read+reconstruct)
- **Ren'Py formats** delegated to `app/core/renpy_processor.py::RenpyProcessor` (RPY read+reconstruct+split_by_scenes)
- `FileProcessor` delegates transparently — public API unchanged, callers don't break
- **SRT subtitles**: `SRT_{index}:` markers, preserves timecodes and multiline text
- **ASS/SSA subtitles**: `ASS_{index}:` markers, handles override tags (`{\b1}`), commas in text, skips Comment lines

### Module Responsibilities

**CLI**:
- **`app/cli.py`**: Command-line interface with 6 commands (translate, services, languages, detect, cache, config)
  - `cmd_translate()`: Translates text/file with progress bar and file info header (name, languages, services), supports stdin pipe, JSON output
  - `_cmd_translate_directory()`: Batch folder translation with per-file progress  - CLI flags for batch: `-d`/`--directory`, `--output-dir`, `--extensions`, `--no-recursive`, `--service`
  - `--export`: Export results to DOCX/PDF/XLIFF (e.g. `--export results.docx`)
  - `cmd_cache()`: Export/import translation cache in TMX format — `cache export-tmx path.tmx`, `cache import-tmx path.tmx`
  - Smart dispatch in `main.py`: CLI commands auto-detected from `sys.argv[1]`, falls back to GUI

**Core Logic**:
- **`app/core/translator.py`**: Orchestrates entire translation workflow, manages service lifecycle
- **`app/core/batch_translator.py`**: Batch folder translation  - `BatchTranslator`: Orchestrates file discovery and per-file translation
  - `find_files()`: Discovers files by extensions, recursive or not (default: `.rpy`)
  - `translate_file()`: Translates single file, saves with language suffix (`script.rpy` → `script_ru.rpy`)
  - `translate_folder()`: Translates all matching files with progress callback
  - `BatchFileResult` / `BatchProgress`: Dataclasses for results and progress tracking
  - For `.rpy` files: extracts dialogue, translates, reconstructs via `FileProcessor.reconstruct_rpy()`
  - Output directory support with relative path preservation; failed files skipped
- **`app/core/exporter.py`**: Export translations to DOCX (python-docx), PDF (reportlab), XLIFF 1.2 (xml.etree) with original text + per-service translations
- **`app/core/file_processor.py`**: File format handling (11 formats), encoding detection, dispatch via `_PROCESSORS` dict
- **`app/core/subtitle_processor.py`**: SRT/ASS subtitle read/reconstruct (extracted from file_processor)
- **`app/core/renpy_processor.py`**: Ren'Py RPY read/reconstruct/split_by_scenes (extracted from file_processor)
- **`app/core/language_detector.py`**: Wrapper around langdetect with availability checks
- **`app/core/renpy_context.py`**: Ren'Py game context extractor — parses characters, scenes, dialogue from `.rpy` files

**Configuration**:
- **`app/config/settings.py`**: JSON persistence, API key management, config deep merge, settings validation
  - `OPENAI_MODELS`, `CLAUDE_MODELS`, `GROQ_MODELS`: Canonical model lists (single source of truth for services, settings, and GUI)
  - `VALIDATORS`: Declarative validation rules (type, choices, min/max) for known keys
  - `validate()` called by `set()` — enforces types, ranges, allowed values, and model names
- **`app/config/languages.py`**: Language code mappings for different services

**Services** (with FREE API support):
- **`app/services/llm_base.py`**: `LLMTranslationService` — shared base for all LLM services (prompt, chat completions, error handling)
- **`app/services/deepl.py`**, **`google.py`**, **`yandex.py`**: Free API services with paid fallback, use `retry_with_backoff()` from rate_limiter
- **`app/services/openai_service.py`**, **`groq_service.py`**, **`openrouter.py`**, **`localai.py`**: Thin subclasses of `LLMTranslationService`
- **`app/services/claude.py`**: `LLMTranslationService` subclass, overrides `_call_llm()` for Anthropic API
- **`app/services/chatgpt_proxy.py`**: ChatGPT Proxy (no key required, standalone implementation)
- **`app/services/ai_evaluator.py`**: AI-powered translation evaluation — scores (0-10), explanations, improved translations
- **`app/services/agent_voting.py`**: Multi-agent voting system — async parallel voting, weighted consensus

**Modern UI** (excluded from test coverage, mixin-based architecture since v3.0):
- **`app/gui/main_window.py`**: Main window orchestrator (~600 lines) — inherits from 9 mixins, handles window setup, menu, controls panel, status bar, settings/navigation, state management
- **`app/gui/tabs/`**: Tab rendering mixins (6 modules):
  - `results_tab.py` (`ResultsTabMixin`): Results tab with service tabs, stats, copy/save, editable text; also defines `SERVICE_ICONS` class constant used by other tabs
  - `comparison_tab.py` (`ComparisonTabMixin`): Side-by-side comparison grid (original + translations)
  - `diff_tab.py` (`DiffTabMixin`): VS Code-style diff view with per-line revert
  - `evaluation_tab.py` (`EvaluationTabMixin`): AI evaluation report — summary, agent votes, detailed scores, improved translation; also defines `_get_rating_color()` and `_get_score_text_color()`
  - `history_tab.py` (`HistoryTabMixin`): History cards with timestamp, languages, preview, delete
  - `glossary_tab.py` (`GlossaryTabMixin`): Glossary editor with add/delete/save/clear entries
- **`app/gui/workflows/`**: Translation workflow mixins (3 modules):
  - `translation_workflow.py` (`TranslationWorkflowMixin`): Start → run (threaded) → complete/error
  - `evaluation_workflow.py` (`EvaluationWorkflowMixin`): Single AI evaluation and multi-agent voting
  - `batch_workflow.py` (`BatchWorkflowMixin`): Batch folder translation with progress and results summary
- **`app/gui/widgets/diff_view.py`**: VS Code-style line-by-line diff with per-line revert buttons (`↩`), color-coded `+`/`-` lines, stats
- **`app/gui/widgets/file_drop.py`**: Drag-drop zone
- **`app/gui/widgets/progress.py`**: Progress bar
- **`app/gui/settings_dialog.py`**: Settings dialog with AI Agents and Ren'Py sections
- **`app/gui/history_view.py`**: TranslationHistory class for persistence

**Utilities**:
- **`app/utils/glossary.py`**: Term dictionary with post-processing replacement, JSON persistence
- **`app/utils/logging.py`**: Structured logging setup — file handler (`polytranslate.log`) + optional console handler
- **`app/utils/cache.py`**: Translation cache — in-memory + JSON persistence, LRU eviction, thread-safe, TMX export/import for CAT tools
- **`app/utils/rate_limiter.py`**: Thread-safe rate limiter + `retry_with_backoff()` utility for free API retry logic (used by DeepL, Google, Yandex)
- **`app/utils/json_helpers.py`**: `parse_json_response()` — strips markdown fences from LLM responses and parses JSON

### Testing Strategy

**641 tests, 94% coverage** (GUI excluded)

- **Service Tests**: Mock HTTP with `respx` library (httpx-compatible)
- **Free API Tests**: Test fallback mechanism for DeepL, Google, and Yandex
- **LLM Base Tests** (`tests/test_llm_base.py`): 11 tests, 100% coverage — translate, caching, error wrapping, auto source lang
- **Diff View Tests** (`tests/test_diff_view.py`): 10 tests (diff logic, revert, edge cases)
- **Settings Tests** (`tests/test_settings.py`): 43 tests (includes validation for types, ranges, models)
- **Rate Limiter Tests** (`tests/test_rate_limiter.py`): 14 tests, 98% coverage — includes `retry_with_backoff()` retry/429/error tests
- **AI Evaluator Tests** (`tests/test_ai_evaluator.py`): 19 tests, 98% coverage
- **Agent Voting Tests** (`tests/test_agent_voting.py`): 25 tests, 89% coverage
- **Ren'Py Context Tests** (`tests/test_renpy_context.py`): 13 tests, 92% coverage
- **Ren'Py Processor Tests** (`tests/test_renpy_processor.py`): 11 tests, 100% coverage — read/reconstruct, error wrapping
- **Ren'Py Scene Splitting Tests** (`tests/test_file_processor_renpy_scenes.py`): 6 tests
- **Subtitle Processor Tests** (`tests/test_subtitle_processor.py`): 14 tests, 100% coverage — SRT/ASS read/reconstruct, edge cases
- **CLI Tests** (`tests/test_cli.py` + `tests/test_cli_extended.py`): 65 tests — translate, batch, cache, config, detect, services, helpers
- **Export Tests** (`tests/test_exporter.py`): 23 tests (DOCX content, PDF validity, XLIFF structure)
- **Cache TMX Tests** (`tests/test_cache_tmx.py`): 17 tests (export structure, import parsing, round-trip, Unicode, edge cases)
- **Batch Translator Tests** (`tests/test_batch_translator.py` + `tests/test_batch_extended.py`): 35 tests, 80% coverage — output paths, empty files, progress, errors
- **Translator Tests** (`tests/test_translator.py` + `tests/test_translator_extended.py`): 30 tests, 98% coverage — init, cache hit, parallel sync fallback, error capture, reload
- **JSON Helpers Tests** (`tests/test_json_helpers.py`): 9 tests, 100% coverage — markdown fence stripping, error handling
- **Language Tests** (`tests/test_languages.py`): 12 tests — language maps, code lookups, source/target filtering
- **Integration Tests** (`tests/test_integration.py`): End-to-end workflows
- **File Format Tests** (`tests/test_file_processor_formats.py`): Actual file creation and extraction, SRT/ASS subtitle parsing and reconstruction
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

**Plugin Service (external package, no code changes)**:
1. Create a package with a class implementing `TranslationService`
2. Constructor must accept a single `Settings` argument
3. Register entry point in the package's `pyproject.toml`:
   ```toml
   [project.entry-points."polytranslate.services"]
   myservice = "my_package.module:MyServiceClass"
   ```
4. Install the package — PolyTranslate discovers it automatically via `discover_plugins()`

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
- **Translation Cache**: `TranslationCache` in `Translator` caches raw translations (before glossary). Key = text + source + target + service. LRU eviction, thread-safe, persisted to `cache.json`. Supports TMX 1.4b export/import for interoperability with CAT tools.
- **Coverage Target**: 70% minimum (pyproject.toml), currently 94% (641 tests). GUI excluded.
- **Ruff Configuration**: Line length 100, ignores E501, uses modern Python features (UP rules).
- **Language Code Mappings**: Different services use different codes. See `app/config/languages.py`. `get_language_name()` uses `LANGUAGES` dict directly (no separate `LANGUAGE_NAMES` dict).
- **GUI Threading**: All long-running operations must use `threading.Thread` with `root.after()` callbacks.
- **Ren'Py Processing**: `read_rpy()` extracts dialogue using regex. `reconstruct_rpy()` uses default parameters in closures to avoid variable binding issues (B007).
- **Subtitle Processing**: `read_srt()` / `read_ass()` extract subtitle text with indexed markers for reconstruction. ASS parser handles the Format line to correctly split fields (Text is always last and may contain commas). Override tags (e.g. `{\b1}`) are preserved in keys for round-trip fidelity.
- **Parallel Translation Errors**: If a service fails, error message stored in results dict instead of raising (allows partial success).

## Known Quirks

1. **Free API Reliability**: Unofficial, may have rate limits, change without notice, or be blocked in some regions.
2. **Chinese Language Detection**: Returns `zh`, `zh-cn`, or `zh-tw` depending on langdetect confidence.
3. **Retry Logic**: DeepL, Google, and Yandex free APIs retry up to 3 times with exponential backoff (2s, 4s, 8s) on network errors and HTTP 429.
4. **Rate Limiter**: `RateLimiter` is class-level (shared across all instances), so parallel translation via `asyncio.to_thread()` is properly throttled per service.
5. **HTTP Client**: Uses `httpx` (not `requests`) for all HTTP calls. Services using SDK clients (OpenAI, Anthropic, Groq) use their own HTTP handling.
6. **Async Orchestration**: `translate_parallel()` and `vote_on_translations()` use `asyncio.run()` internally. Falls back to sync if already inside a running event loop.
