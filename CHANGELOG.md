# Changelog

All notable changes to PolyTranslate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2026-03-12

### Added

#### Batch Folder Translation
- **Batch folder translation**: Translate all files in a directory at once — GUI, CLI, and core API
  - Point to a game folder and translate every `.rpy` file automatically
  - Output naming: `script.rpy` → `script_ru.rpy` (language suffix added before extension)
  - Ren'Py reconstruction: `.rpy` files keep their dialogue structure (labels, characters, code)
  - Error resilience: failed files are skipped, remaining files continue translating
  - Progress tracking: per-file progress callback with file index, name, and completion status

- **New module** `app/core/batch_translator.py`:
  - `BatchTranslator`: Orchestrates file discovery and per-file translation
  - `find_files()`: Discovers files by extensions (default `.rpy`), recursive or non-recursive
  - `translate_file()`: Translates single file, saves with language suffix
  - `translate_folder()`: Translates all matching files with progress callback
  - `BatchFileResult`: Dataclass (source_path, output_path, success, error, services_used)
  - `BatchProgress`: Dataclass (current_file_index, total_files, current_file_name, file_completed)
  - Output directory support with relative subdirectory structure preservation

- **CLI batch mode** (`-d` / `--directory` flag):
  - `python main.py translate -d /path/to/game/ -t ru` — translate all `.rpy` files
  - `--output-dir`: Save translated files to a separate directory
  - `--extensions`: Filter by file extensions (e.g., `--extensions .rpy .txt`)
  - `--no-recursive`: Only process top-level files (skip subdirectories)
  - `--service`: Choose which service's output to save (when using multiple services)
  - `--format json`: JSON report with source/output paths and success status
  - Per-file progress display: `[3/15] chapter1.rpy ✓ Done`

- **GUI "📁 Translate Folder" button**:
  - New button in menu bar (next to "📂 Open")
  - Folder picker → confirmation dialog showing file count, extensions, and services
  - Threaded execution with per-file progress bar: `[3/15] script.rpy ✓`
  - Results summary view with success/failure cards for each file
  - Auto-fallback: tries `.rpy` first, then all supported extensions

#### Translation Cache
- **Translation cache**: `app/utils/cache.py` — avoids redundant API calls for previously translated text
  - Cache key: text + source language + target language + service name (SHA-256 hashed)
  - In-memory dict with JSON persistence (`cache.json`)
  - LRU eviction when cache exceeds `cache_max_size` (default 10,000 entries)
  - Thread-safe via `threading.Lock` (works with parallel translation)
  - Caches raw translations before glossary application
  - Configurable via `config.json`: `cache_enabled`, `cache_max_size`

#### Rate Limiter
- **Unified rate limiter**: `app/utils/rate_limiter.py` — thread-safe throttling for all free translation APIs
  - Reusable `RateLimiter` class with configurable `min_interval` between requests
  - Thread-safe via `threading.Lock` (works with `ThreadPoolExecutor` parallel translation)
  - Class-level instance per service: DeepL (1.0s), Google (0.5s), Yandex (0.5s)
  - `wait()` blocks until enough time has passed since the last request
  - `reset()` method for clearing rate limit state
  - Replaces DeepL's manual lock+timestamp implementation; adds rate limiting to Google and Yandex

#### Structured Logging
- **Logging system**: `app/utils/logging.py` with `setup_logging()` — file handler (`polytranslate.log`) + optional console handler
- **All modules instrumented**: `logging.getLogger(__name__)` in 16 modules (core, services, config, utils)
- **Key events logged**: service fallback (paid→free), API retries, rate limiting, translation errors, batch progress, config/glossary load errors
- **Called at startup** in `main.py` — logs written to `polytranslate.log` in format `2026-03-13 12:00:00 [INFO] app.core.translator: ...`

#### Diff View
- **VS Code-style diff tab**: New "🔀 Diff" tab showing line-by-line diff between original and translated text
  - Color-coded lines: red (`-`) for removed, green (`+`) for added, neutral for unchanged
  - **Per-line revert** (`↩` button): click to restore original line, diff re-renders instantly
  - Stats header: `+N -N =N` showing added/removed/unchanged line counts
  - Legend bar with color key
  - Single service: diff shown directly; multiple services: nested tabs with one diff per service
  - Revert updates `_translations` dict — changes persist across tabs
- **New widget** `app/gui/widgets/diff_view.py`: Reusable `DiffView` frame built on `difflib.SequenceMatcher`

#### Settings Validation & Model Updates
- **Settings validation**: `Settings.set()` now validates all known keys via declarative `VALIDATORS` table
  - Type checking: rejects wrong types (e.g. string for `cache_enabled`)
  - Choice validation: `theme`, `deepl_plan`, `renpy_processing_mode`
  - Range validation: `chunk_size` [100..5000], `max_workers` [1..10], `cache_max_size` [100..100000]
  - Model validation: `openai_model`, `claude_model`, `groq_model` checked against `AVAILABLE_MODELS`
  - Unknown keys pass through without validation (extensible)
- **Model lists updated** to current versions:
  - OpenAI: gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-4o-mini, o3-mini, gpt-4-turbo (default: `gpt-4o-mini`)
  - Claude: claude-sonnet-4-6, claude-haiku-4-5, claude-3-7-sonnet, claude-3-5-sonnet, claude-3-5-haiku (default: `claude-sonnet-4-6`)
  - Groq: llama-3.3-70b-versatile, llama-3.1-8b-instant, gemma2-9b-it, mixtral-8x7b (default: `llama-3.3-70b-versatile`)
  - OpenRouter default: `openai/gpt-4o-mini`
- **Canonical model lists**: `Settings.OPENAI_MODELS`, `Settings.CLAUDE_MODELS`, `Settings.GROQ_MODELS` — single source of truth used by services, settings, and GUI dialog
- Removed deprecated models: gpt-3.5-turbo, claude-2.x, claude-instant, llama2, gemma-7b

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
- All tests passing (457 tests, 91% coverage)
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

#### Core Dependencies
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
- Translation memory (TMX support)
- API usage statistics and cost tracking
- Custom translation engine plugins
- Export to various formats (XLIFF, TMX, etc.)
- Automated translation caching
- Integration with CAT tools

---

## Version History

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
