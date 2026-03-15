# Changelog

All notable changes to PolyTranslate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-03-15

### Changed

#### Pydantic Settings Schema
- **Config validation via Pydantic**: Replaced hand-rolled `VALIDATORS` dict with Pydantic `SettingsSchema` model (`app/config/schema.py`)
- `SettingsSchema` with `@field_validator` for all validated fields (theme, chunk_size, max_workers, cache_max_size, cache_enabled, deepl_plan, renpy_processing_mode, ai_evaluation_auto, openai_model, claude_model, groq_model)
- `ApiKeysSchema` for nested api_keys with `extra="allow"` for plugin/custom keys
- Canonical model lists (`OPENAI_MODELS`, `CLAUDE_MODELS`, `GROQ_MODELS`) moved to `schema.py` as single source of truth
- `Settings` internally stores `self._schema: SettingsSchema` instead of raw `dict[str, Any]`
- Public API fully preserved — all getters/setters, `get()`, `set()`, `validate()`, `to_dict()` unchanged
- Backward-compatible error messages (same `ValueError` text as before)

#### Click CLI
- **CLI rewritten with Click**: Replaced `argparse` with `click.group` + `click.command` decorators (`app/cli.py`)
- Auto-generated `--help` for all commands and subcommands
- `click.Choice` for `--format` validation, `multiple=True` for `--services` and `--extensions`
- `cache` implemented as Click subgroup (`cache export-tmx`, `cache import-tmx`)
- Command aliases (t, s, l, d, c) preserved via `run_cli()` resolution
- Added `"cache"` to CLI dispatch list in `main.py`
- New dependency: `click>=8.0.0` (already a transitive dependency)

### Added

#### Chunk Deduplication
- **Request deduplication in parallel translation**: Identical chunks translated only once per service
- `_translate_parallel_async()` and `_translate_parallel_sync()` deduplicate via `dict.fromkeys()`
- Results mapped back to original chunk positions after translation
- Progress callback `total_tasks` reflects unique tasks, not original count
- Significant performance improvement for repetitive content (e.g. Ren'Py menus, UI strings)

#### Language Detection Cache
- **LRU cache for language detection**: `LanguageDetector._cache` — `OrderedDict` with max 256 entries
- Cache key: first 200 characters of stripped text (sufficient for accurate detection)
- `None` results cached too (avoids retrying texts that fail detection)
- `clear_cache()` classmethod for testing; autouse fixture in `conftest.py`

#### Streaming Translation
- **Token-by-token streaming for LLM services**: OpenAI, Claude, Groq, OpenRouter, LocalAI now stream tokens as they generate
- `LLMTranslationService.translate_stream()` and `_call_llm_stream()` — base class methods for OpenAI-compatible streaming (`stream=True`)
- `ClaudeService._call_llm_stream()` — Anthropic-specific override using `client.messages.stream()` context manager
- `Translator.translate()` accepts optional `on_token: Callable[[str], None]` — routes to streaming or non-streaming path
- `Translator.translate_parallel()` accepts `on_token: dict[str, Callable]` — per-service streaming callbacks
- **GUI streaming**: Tabs created before translation starts, tokens appended live via `root.after()`; full results rebuilt on completion
- **CLI `--stream` flag**: Prints tokens to stderr as they arrive (disables progress bar)
- Non-LLM services (DeepL, Google, Yandex) and cache hits emit full result as single callback
- No changes to `TranslationService` abstract base — streaming is opt-in on `LLMTranslationService` subclasses

#### CI/CD (GitHub Actions)
- **CI pipeline** (`.github/workflows/ci.yml`): Lint (Ruff), type check (Mypy), tests (pytest) on Python 3.10, 3.11, 3.12 matrix — runs on push/PR to `main`
- **Release pipeline** (`.github/workflows/release.yml`): Builds PyInstaller executables for Windows, Linux, macOS; packages as zip; creates GitHub Release with auto-generated notes — triggered on `v*` tags
- Concurrency control: in-progress CI runs cancelled when new commits pushed

#### Rotating Log File
- **Log rotation**: Replaced `FileHandler` with `RotatingFileHandler` — 10 MB max size, 3 backup files (`polytranslate.log.1`, `.2`, `.3`)
- Prevents `polytranslate.log` from growing indefinitely

#### Dependency Updates
- **SDK version bumps**: `anthropic` 0.18→≥0.70, `openai` 1.0→≥2.0, `groq` 0.4→≥1.0
- **All pins relaxed**: Exact version pins (`==`) replaced with minimum version ranges (`>=`) across all dependencies
- **Reproducibility**: Added `requirements.lock` (full `pip freeze` snapshot) for deterministic installs
- Updated: `Pillow` ≥12, `python-docx` ≥1.0, `python-pptx` ≥1.0, `pypdf` ≥6, `pydantic` ≥2, `nltk` ≥3.8, `pyinstaller` ≥6

### Technical
- Updated `app/services/llm_base.py` — `translate_stream()`, `_call_llm_stream()`, `supports_streaming()`, `_build_messages()` helper
- Updated `app/services/claude.py` — `_call_llm_stream()` override for Anthropic streaming API
- Updated `app/core/translator.py` — `on_token` parameter in `translate()` and `translate_parallel()`
- Updated `app/cli.py` — `--stream` flag on `cmd_translate`
- Updated `app/gui/workflows/translation_workflow.py` — per-service streaming callbacks via `root.after()`
- Updated `app/gui/tabs/results_tab.py` — `_prepare_streaming_tabs()` and `_append_stream_token()`
- New file: `requirements.lock` — pinned transitive dependency snapshot for reproducible builds
- New file: `app/config/schema.py` — Pydantic models for settings validation
- Updated `app/config/settings.py` — wraps `SettingsSchema` internally
- Updated `app/cli.py` — full Click rewrite (465 → 505 lines)
- Updated `app/core/translator.py` — chunk deduplication in both async and sync paths
- Updated `app/core/language_detector.py` — LRU cache with `OrderedDict`
- Updated `tests/conftest.py` — autouse `_clear_lang_cache` fixture
- Updated `tests/test_translator_extended.py` — `_make_settings()` uses `SettingsSchema`, 4 new deduplication tests
- Updated `tests/test_language_detector.py` — 5 new cache tests (hit, miss, eviction, None caching)
- Updated `tests/test_cli.py` and `tests/test_cli_extended.py` — Click `CliRunner` + `run_cli()` tests
- Updated `requirements.txt` — relaxed pins, added `click>=8.0.0`
- Updated `app/utils/logging.py` — `RotatingFileHandler` (10 MB, 3 backups) instead of `FileHandler`
- Updated `tests/test_logging.py` — assertions use `RotatingFileHandler` type
- New file: `.github/workflows/ci.yml` — CI pipeline (lint, typecheck, test matrix)
- New file: `.github/workflows/release.yml` — Release pipeline (build + GitHub Release)
- All 652 tests passing, 93% coverage
- Ruff lint and format clean

---

## [3.0.0] - 2026-03-14

### Added

#### Export Results (DOCX / PDF / XLIFF)
- **Translation export**: Save original + translations to DOCX, PDF, or XLIFF 1.2 via `TranslationExporter.export()` — auto-detects format from extension
- GUI "Export" button and CLI `--export` flag (`python main.py translate "text" -t ru --export results.docx`)
- New dependency: `reportlab>=4.0.0` (for PDF export)

#### TMX Cache Export/Import
- **TMX export/import**: Exchange translation memory with CAT tools in standard TMX 1.4b format
- CLI: `cache export-tmx memory.tmx` / `cache import-tmx memory.tmx`
- Round-trip safe: export → import preserves text, languages, service, and translation

#### SRT/ASS Subtitle Support
- **SRT/ASS subtitles**: Parse and reconstruct `.srt`, `.ass`/`.ssa` files with indexed markers, preserving timecodes, override tags, and metadata
- Supported in both `process_file()` and `process_bytes()` pipelines

#### Plugin System (Entry Points)
- **Service plugins**: Add new translation services via `polytranslate.services` entry point — no code changes needed
- `app/core/plugin_loader.py`: Scans entry points, validates `TranslationService` instances, skips broken plugins gracefully

### Changed

#### GUI Architecture Refactoring (Breaking)
- **Modular GUI**: Refactored monolithic `main_window.py` (2218 lines) into 10 focused modules (~200 lines each)
  - `MainWindow` now uses **mixin classes** for clean separation of concerns
  - Extracted 6 **tab mixins** into `app/gui/tabs/`:
    - `ResultsTabMixin` — results rendering, save/copy actions
    - `ComparisonTabMixin` — side-by-side comparison grid
    - `DiffTabMixin` — VS Code-style diff view
    - `EvaluationTabMixin` — AI evaluation report, agent votes, improved translation
    - `HistoryTabMixin` — history cards, delete/clear
    - `GlossaryTabMixin` — glossary editor, add/delete/save entries
  - Extracted 3 **workflow mixins** into `app/gui/workflows/`:
    - `TranslationWorkflowMixin` — translation start/run/complete/error
    - `EvaluationWorkflowMixin` — single evaluation and multi-agent voting
    - `BatchWorkflowMixin` — batch folder translation with progress
  - `MainWindow` reduced from 2218 to **592 lines** (orchestrator + UI setup only)
  - Shared constants (`SERVICE_ICONS`) moved to `ResultsTabMixin` as class attribute
  - Empty state creation consolidated into `_create_empty_placeholder()` helper
  - Controls panel split into `_create_language_card()`, `_create_services_card()`, `_create_action_buttons()`
  - Menu bar simplified with data-driven button creation loop

### Technical
- New directories: `app/gui/tabs/`, `app/gui/workflows/`
- New files: 6 tab modules + 3 workflow modules + 2 `__init__.py`
- New test files: `tests/test_exporter.py` — 23 tests (DOCX content, PDF validity, XLIFF structure, edge cases), `tests/test_cache_tmx.py` — 17 tests (export structure, import parsing, round-trip, Unicode)
- All 534 tests passing, 90% coverage

---

## [2.6.0] - 2026-03-12

### Added

#### Batch Folder Translation
- **Batch folder translation**: Translate all files in a directory at once — GUI, CLI, and core API
- `app/core/batch_translator.py`: File discovery, per-file translation with language suffix naming, progress callbacks
- CLI batch mode: `-d`/`--directory`, `--output-dir`, `--extensions`, `--no-recursive`, `--service`, `--format json`
- GUI "Translate Folder" button with folder picker, threaded execution, and results summary

#### Translation Cache
- **Translation cache**: `app/utils/cache.py` — SHA-256 keyed, LRU eviction, thread-safe, JSON-persisted
- Configurable via `config.json`: `cache_enabled`, `cache_max_size` (default 10,000)

#### Rate Limiter
- **Unified rate limiter**: `app/utils/rate_limiter.py` — thread-safe throttling per service (DeepL 1.0s, Google/Yandex 0.5s)

#### Structured Logging
- **Logging system**: `app/utils/logging.py` — file handler (`polytranslate.log`) + optional console, all 16 modules instrumented

#### Diff View
- **VS Code-style diff tab**: Line-by-line diff with color-coded +/- lines, per-line revert buttons, stats header
- `app/gui/widgets/diff_view.py`: Reusable `DiffView` frame built on `difflib.SequenceMatcher`

#### Settings Validation & Model Updates
- **Settings validation**: Declarative `VALIDATORS` table — type checking, choice/range/model validation
- Model lists updated: OpenAI (gpt-4.1 family), Claude (claude-sonnet-4-6), Groq (llama-3.3-70b), OpenRouter (gpt-4o-mini)
- Canonical model lists as single source of truth; removed deprecated models

#### httpx + asyncio Migration
- Replaced `requests` with `httpx`, `ThreadPoolExecutor` with `asyncio.gather()` + `asyncio.to_thread()`
- `respx` for HTTP mocking in tests; graceful sync fallback when inside running event loop

### Improved
- **CLI file progress**: Single file translation now shows file name, language pair, and services before progress bar, with "Done." on completion
- **PyPDF2 → pypdf**: Migrated from deprecated PyPDF2 to maintained `pypdf` library
- **Retry for Google/Yandex**: Free APIs now retry up to 3 times with exponential backoff (2s, 4s, 8s) on network errors and HTTP 429, matching DeepL behavior
- **Cache in CLI**: `cache.save()` called after single and batch translations in CLI mode
- **Cache in GUI Settings**: "Cache Settings" section with enable/disable toggle, "Clear Cache" button, and max size slider

### Technical
- New test files: `tests/test_batch_translator.py` (25 tests), `tests/test_cache.py` (19 tests), `tests/test_logging.py` (8 tests), `tests/test_rate_limiter.py` (8 tests)
- Extended `tests/test_cli.py` with 9 batch directory tests (parser flags, execution, errors, JSON)
- Extended service tests: Google retry/429 (8 tests), Yandex retry/429 (7 tests), OpenRouter (3 tests)
- Test isolation: `conftest.py` autouse fixture redirects `TranslationCache` to temp directory
- Extended `tests/test_settings.py` with 21 validation tests (types, ranges, models, edge cases)
- Updated exports in `app/core/__init__.py`
- New test file: `tests/test_diff_view.py` (10 tests — diff logic, revert, edge cases)
- Dependencies: `requests` → `httpx`, `responses` → `respx`, removed `types-requests`
- All tests passing (464 tests, 90% coverage)
- Ruff lint and format clean

---

## [2.5.0] - 2026-03-12

### Added

#### Command-Line Interface (CLI)
- **Full CLI mode**: Translate text and files directly from the terminal without launching the GUI
  - `translate` (alias `t`): Translate text or file with progress bar and multi-service support
  - `services` (alias `s`): List all configured translation services with availability status
  - `languages` (alias `l`): List all supported language codes and names
  - `detect` (alias `d`): Detect language of text or file content
  - `config` (alias `c`): View config (API keys masked), set values, or manage API keys

- **CLI translation features**:
  - Translate text from argument, file (`--file`), or stdin pipe
  - Select specific services (`--services deepl google`) or all (`--all-services`)
  - Auto language detection with `--source auto` (default)
  - Output to stdout or file (`--output result.txt`)
  - Text or JSON output format (`--format json`) for scripting/pipelines
  - Configurable chunk size and max workers from CLI flags
  - Progress bar displayed on stderr (keeps stdout clean for piping)
  - Uses same `config.json` as GUI, or custom config path (`--config`)

- **New module** `app/cli.py`:
  - `create_parser()`: Builds argparse parser with all commands and options
  - `run_cli()`: Main CLI entry point dispatching to command handlers
  - `cmd_translate()`, `cmd_services()`, `cmd_languages()`, `cmd_detect()`, `cmd_config()`

- **Smart entry point dispatch** in `main.py`:
  - CLI commands auto-detected from `sys.argv[1]` (translate, services, etc.)
  - Falls back to GUI mode when no CLI command given
  - `python main.py` launches GUI, `python main.py translate ...` uses CLI

### Technical
- New test file: `tests/test_cli.py` — 33 tests covering all CLI commands
- All tests passing (350 tests, 91% coverage)
- Ruff lint and format clean

---

## [2.4.0] - 2026-03-12

### Added

#### Multi-Agent Voting System
- **Agent Voting**: Multiple AI agents independently evaluate translations and vote on the best one
  - Supports unlimited agents: mix local LLMs (LM Studio, Ollama) and cloud APIs (OpenAI, Claude, Groq)
  - Weighted voting: assign different weights (0.5-2.0) to trusted agents
  - Parallel execution via ThreadPoolExecutor for all agents simultaneously
  - Weighted consensus scoring: `score = Σ(vote * weight) / Σ(weight)`
  - Agreement tracking: shows how many agents agree on the best translation
  - Merged/improved translation selected from highest-weight agent
  - Graceful degradation: failed agents are skipped, voting continues with the rest
  - 1 LLM call per agent (scores + merge in single prompt) for token efficiency

- **New module** `app/services/agent_voting.py`:
  - `AgentConfig`: Dataclass for agent definition (name, base_url, model, api_key, agent_type, weight)
  - `AgentVote`: Single agent's response (scores, best pick, explanations, merged translation)
  - `VotingResult`: Aggregated result (consensus scores, consensus best, agreement ratio)
  - `AgentVoting`: Orchestrator class with parallel voting and consensus computation
  - Reuses existing service classes (`LocalAIService`, `OpenAIService`, `ClaudeService`, `GroqService`)

#### Ren'Py Context Awareness
- **Game context extraction**: Automatically parse Ren'Py project folders for translation context
  - Character parsing: finds all `define ... = Character(...)` declarations with names and colors
  - Scene detection: identifies `label` blocks and which characters appear in each scene
  - Dialogue preview: extracts first 5 lines of dialogue per scene
  - Nearby dialogue: provides surrounding lines for better AI understanding
  - Context string generation with configurable max_tokens truncation (default 1500)

- **New module** `app/core/renpy_context.py`:
  - `RenpyCharacter`: Dataclass (variable, name, color)
  - `RenpyScene`: Dataclass (label, characters_present, dialogue_preview)
  - `RenpyContext`: Dataclass (characters, scenes, current_scene, nearby_dialogue)
  - `RenpyContextExtractor`: Main parser class scanning all `.rpy` files in game folder

- **Scene-based Ren'Py processing**: New `FileProcessor.split_rpy_by_scenes()` method
  - Splits `.rpy` files by `label` blocks into `(label_name, scene_content)` tuples
  - Handles preamble content before first label
  - Falls back to single chunk when no labels found
  - Three processing modes configurable via settings: "scenes", "chunks", "full"

#### Settings & UI
- **AI Agents settings section** in Settings dialog:
  - Dynamic agent rows with Name, Type (dropdown), URL, Model, API Key, Weight (slider)
  - "+ Add Agent" button and "X" Remove button per row
  - URL field auto-disabled for non-localai agent types

- **Ren'Py Settings section** in Settings dialog:
  - Game Folder: text field with "Browse" button (folder picker)
  - Processing Mode: dropdown (By Scenes / By Chunks / Full File)

- **Agent Votes section** in AI Evaluation tab:
  - Table showing each agent's name, best pick, and scores
  - Agreement indicator: "3/3 agents agree" or "2/3 majority"
  - Color-coded: green for full agreement, yellow for partial

- **Dynamic evaluate button text**:
  - "🤖 Agent Vote" when agents are configured
  - "🤖 Evaluate All" when using single AI evaluator

- **New settings keys** in `config.json`:
  - `agents`: list of agent configurations (name, base_url, model, api_key, agent_type, weight)
  - `renpy_game_folder`: path to Ren'Py game folder
  - `renpy_processing_mode`: "scenes" | "chunks" | "full" (default: "scenes")

- Settings dialog window enlarged to 550x1050 to accommodate new sections

### Technical
- New test files:
  - `tests/test_agent_voting.py` — 25 tests, 95% coverage
  - `tests/test_renpy_context.py` — 13 tests, 92% coverage
  - `tests/test_file_processor_renpy_scenes.py` — 6 tests
  - `tests/test_settings.py` — 4 new tests for agent/ren'py defaults
- Updated exports in `app/services/__init__.py` and `app/core/__init__.py`
- All tests passing (317 tests, 91% coverage)
- Ruff lint and format clean

## [2.2.0] - 2026-02-01

### Added

#### Translation Editing & Comparison
- **Editable Translations**: All translation text areas are now fully editable
  - Edit translations directly in both Results and Comparison tabs
  - Changes automatically saved in memory
  - Copy button uses current edited content
  - Save button preserves edited translations to file

- **Original Text Comparison**: Compare translations with source text
  - Original text displayed as first panel in Comparison tab
  - Marked with 📄 icon and green color for easy identification
  - Side-by-side view: Original → Translation 1 → Translation 2 → ...
  - Original text is read-only (protected from accidental editing)
  - Grid layout automatically adapts to show original + all translations

### Improved
- Enhanced Comparison tab with better visual hierarchy
- Original text loaded from history when viewing past translations
- Better user feedback with color-coded panels (green for original, blue for translations)

### Technical
- Added `_original_text` field to store source text for comparison
- Text modification tracking with `<<Modified>>` event bindings
- Automatic translation dictionary updates on edit
- All tests passing (249 tests, 89% coverage)

## [2.1.0] - 2026-02-01

### Changed

#### User Interface Improvements
- **Tabbed Interface**: Redesigned UI to use integrated tabs instead of popup windows
  - All features now accessible from main window
  - 4 main tabs: 📝 Results, 📊 Comparison, 📜 History, 📚 Glossary
  - No more popup windows - everything in one place

#### Translation Results
- Results tab now contains nested service tabs for cleaner organization
- Comparison view integrated as a permanent tab (not a popup window)
- Grid layout for comparison view (up to 3 columns)
- Instant switching between results and comparison views

#### History View
- History now displayed as a tab in main window instead of popup
- Beautiful card-based layout for history entries
- Click any history card to instantly load translation
- Shows timestamp, languages, file name, and services used
- Individual entry deletion with visual feedback

#### Glossary Editor
- Glossary editor now integrated as a tab in main window
- Real-time editing without closing dialogs
- Save button with immediate application
- Clear visual feedback for add/delete operations
- Case sensitivity toggle easily accessible

### Improved
- Better navigation flow - all features one click away
- Reduced window management overhead
- Consistent UI experience across all features
- Faster workflow with tabbed interface

### Technical
- Removed dependencies on popup window classes for Comparison, History, and Glossary
- Simplified state management with integrated tabs
- Better memory management (no orphaned popup windows)
- All tests still passing (230 tests, 89% coverage)

## [1.0.0] - 2026-02-01

### Added

#### Core Features
- Desktop GUI application built with CustomTkinter
- Support for 9 translation services (DeepL, Google, Yandex, OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI)
- Support for 9 file formats (TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, Markdown, Ren'Py)
- Parallel translation processing with configurable workers
- Automatic language detection using langdetect
- Translation comparison view for multiple services

#### Translation Services
- **DeepL**: High-quality translation with free/pro tier support
- **Google Translate**: Comprehensive language support (100+ languages)
- **Yandex Translate**: Excellent Cyrillic language support
- **OpenAI GPT**: Context-aware translation with multiple models
- **Claude AI**: High-quality translation using Anthropic API
- **Groq**: Fast inference with open-source models
- **OpenRouter**: Access to multiple LLM providers
- **ChatGPT Proxy**: Free translation without API key
- **LocalAI**: Self-hosted translation for privacy

#### File Processing
- Text files (TXT, MD, HTML)
- PDF document extraction
- Microsoft Office formats (DOCX, PPTX, XLSX)
- CSV data files with encoding detection
- Ren'Py game script translation

#### User Interface
- Modern CustomTkinter-based GUI
- Dark and Light theme support
- Drag & Drop file interface
- Multi-tab result display
- Real-time progress tracking
- Settings dialog for API key management

#### Management Features
- **Glossary**: Custom terminology dictionary with JSON export/import
- **History**: Translation history tracking
- **Settings**: Persistent configuration storage
- **Batch Processing**: Process large texts in chunks

#### Developer Tools
- Comprehensive test suite (230 tests)
- 89% code coverage
- Type hints throughout codebase
- Automated linting with Ruff
- Pre-commit hooks for code quality
- CI/CD ready test infrastructure

### Technical Details

#### Architecture
- Modular service architecture with abstract base class
- Separate GUI, core logic, and service layers
- Configuration management with JSON persistence
- Parallel processing using ThreadPoolExecutor
- NLTK-based sentence tokenization with fallback

#### Testing
- Unit tests for all core modules
- Integration tests for end-to-end workflows
- Service mocking using responses library
- Pytest fixtures for common test scenarios
- Coverage reporting with HTML output

#### Code Quality
- Ruff for linting and formatting
- MyPy for static type checking
- Pre-commit hooks for automated checks
- PEP 8 compliant code style
- Google-style docstrings

### Dependencies

#### Core Dependencies (at time of v1.0 release)
- customtkinter >= 5.2.0
- PyPDF2 >= 3.0.0
- python-docx >= 0.8.11
- python-pptx >= 0.6.21
- pandas >= 2.0.0
- requests >= 2.31.0
- openai >= 1.0.0
- anthropic >= 0.18.0
- groq >= 0.4.0
- langdetect >= 1.0.9
- nltk >= 3.8.0

*Note: Since v3.1, dependencies updated — see `requirements.txt` for current versions.*

#### Development Dependencies
- pytest >= 8.0.0
- pytest-cov >= 4.1.0
- ruff >= 0.2.0
- mypy >= 1.8.0
- pre-commit >= 3.6.0

### Documentation
- Comprehensive README with installation and usage instructions
- Contributing guidelines (CONTRIBUTING.md)
- MIT License
- Code of Conduct
- Architecture documentation in CLAUDE.md

### Build & Distribution
- PyInstaller configuration for .exe creation
- Requirements files for production and development
- Project configuration in pyproject.toml

---

## [Unreleased]

### Planned Features
- Cloud sync for glossary and settings
- API usage statistics and cost tracking

---

## Version History

- **3.1.0** (2026-03-15) - Streaming translation, Pydantic settings, Click CLI, chunk deduplication, language detection cache, CI/CD, log rotation, dependency updates
- **3.0.0** (2026-03-14) - Export results (DOCX/PDF/XLIFF), TMX cache exchange, plugin system, SRT/ASS subtitles, GUI refactoring
- **2.6.0** (2026-03-12) - Batch Folder Translation (GUI + CLI + API)
- **2.5.0** (2026-03-12) - Command-Line Interface (CLI) mode
- **2.4.0** (2026-03-12) - Multi-Agent Voting System + Ren'Py Context Awareness
- **2.2.0** (2026-02-01) - Editable translations + original text comparison
- **2.1.0** (2026-02-01) - Tabbed interface redesign
- **1.0.0** (2026-02-01) - Initial release

---

## Migration Guides

### From Streamlit Version

If migrating from the original Streamlit-based application:

1. Export your existing glossary and settings
2. Install PolyTranslate using the instructions above
3. Import your glossary via the GUI
4. Re-configure API keys in Settings
5. Translation history is not compatible - fresh start required

---

## Support

For bug reports and feature requests, please use [GitHub Issues](https://github.com/yourusername/polytranslate/issues).

For questions and discussions, use [GitHub Discussions](https://github.com/yourusername/polytranslate/discussions).
