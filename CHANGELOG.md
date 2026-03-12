# Changelog

All notable changes to PolyTranslate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Batch file processing
- API usage statistics and cost tracking
- Custom translation engine plugins
- Command-line interface (CLI) mode
- Export to various formats (XLIFF, TMX, etc.)
- Automated translation caching
- Integration with CAT tools

---

## Version History

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
