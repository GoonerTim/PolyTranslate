# Changelog

All notable changes to PolyTranslate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Quality estimation scoring
- Batch file processing
- API usage statistics and cost tracking
- Custom translation engine plugins
- Command-line interface (CLI) mode
- Export to various formats (XLIFF, TMX, etc.)
- Automated translation caching
- Integration with CAT tools

---

## Version History

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
