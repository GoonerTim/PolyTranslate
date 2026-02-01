# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PolyTranslate** - Desktop translation application with support for 9 translation services (DeepL, Google, Yandex, OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI) and 9 file formats (TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py). Built with Python 3.10+ and CustomTkinter GUI.

## Common Commands

### Running the Application
```bash
python main.py
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

# Run with verbose output and short traceback
pytest -v --tb=short
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

Services are **dynamically initialized** in `Translator._initialize_services()` based on API keys in settings. Only configured services are loaded.

### Key Architectural Decisions

1. **Parallel Processing**: `Translator.translate_parallel()` uses `ThreadPoolExecutor` to translate multiple chunks across multiple services concurrently. Configurable via `max_workers` and `chunk_size`.

2. **Sentence Tokenization**: Uses NLTK's `sent_tokenize()` with `SimpleTokenizer` fallback if NLTK data unavailable. This ensures chunks break on sentence boundaries.

3. **Language Detection**: `LanguageDetector.detect()` wraps `langdetect` library with graceful degradation (returns None if unavailable or text too short).

4. **Settings Persistence**: `Settings` class manages JSON-based config in `config.json`. Uses deep merge strategy for updates (`_deep_merge()` method).

5. **GUI-Core Separation**: GUI (`app/gui/`) is completely decoupled from core logic (`app/core/`). Communication via callbacks and threading to prevent UI freezing.

### File Processing Strategy

`FileProcessor` uses a **strategy pattern** with format-specific static methods:
- `read_txt()`, `read_pdf()`, `read_docx()`, etc.
- `process_file()` dispatches based on file extension
- `process_bytes()` for in-memory processing
- Special handling for Ren'Py (`.rpy`) with dialogue extraction and reconstruction

### Module Responsibilities

- **`app/core/translator.py`**: Orchestrates entire translation workflow, manages service lifecycle
- **`app/core/file_processor.py`**: File format handling (9 formats), encoding detection, content extraction
- **`app/core/language_detector.py`**: Wrapper around langdetect with availability checks
- **`app/config/settings.py`**: JSON persistence, API key management, config deep merge
- **`app/config/languages.py`**: Language code mappings for different services (DeepL uses uppercase codes, ChatGPT Proxy has special mappings)
- **`app/utils/glossary.py`**: Term dictionary with post-processing replacement, JSON persistence
- **`app/services/`**: 9 service implementations + base class
- **`app/gui/`**: CustomTkinter UI (excluded from test coverage)

### Testing Strategy

**226 tests, 90% coverage** (GUI excluded)

- **Service Tests**: Mock HTTP with `responses` library. Example pattern:
  ```python
  @responses.activate
  def test_service(mock_response):
      responses.add(responses.POST, "https://api.url", json={...})
      result = service.translate("text", "en", "ru")
  ```

- **Integration Tests** (`tests/test_integration.py`): End-to-end workflows including file→process→translate→save, parallel processing, error handling, progress callbacks.

- **File Format Tests** (`tests/test_file_processor_formats.py`): Create actual files in-memory (PyPDF2, python-docx, python-pptx, pandas), test extraction.

- **Fixtures** (`tests/conftest.py`): `temp_dir`, `sample_txt_file`, `sample_rpy_content` used across tests.

### Configuration Files

Runtime config (gitignored):
- **`config.json`**: API keys, theme, chunk_size, max_workers, selected_services
- **`glossary.json`**: User term dictionary
- **`history.json`**: Translation history

## Adding New Features

### Add Translation Service

1. Create `app/services/newservice.py`:
   ```python
   from app.services.base import TranslationService

   class NewService(TranslationService):
       def __init__(self, api_key: str = "") -> None:
           self.api_key = api_key

       def translate(self, text: str, source_lang: str, target_lang: str) -> str:
           # API call here
           pass

       def is_configured(self) -> bool:
           return bool(self.api_key)

       def get_name(self) -> str:
           return "New Service"
   ```

2. Register in `app/services/__init__.py`

3. Add initialization in `Translator._initialize_services()`

4. Create `tests/services/test_newservice.py` with mocked HTTP

### Add File Format

1. Add method in `FileProcessor`: `read_newformat(content: bytes) -> str`

2. Update `SUPPORTED_EXTENSIONS` set

3. Add case in `process_bytes()` method

4. Add tests in `tests/test_file_processor_formats.py`

## Important Notes

- **Type Checking**: Mypy reports ~36 warnings mostly from CustomTkinter (uses `Any` types). This is expected and acceptable.

- **NLTK Data**: Downloaded at runtime in `main.py` if missing. Tests handle missing NLTK gracefully.

- **API Key Security**: Never commit `config.json`. Keys stored locally only.

- **Coverage Target**: 70% minimum (pyproject.toml), currently 90%. GUI excluded from coverage (`app/gui/*` omitted).

- **Ruff Configuration**: Line length 100, ignores E501 (line too long), uses modern Python features (UP rules).

- **Language Code Mappings**: Different services use different codes (e.g., DeepL uses "EN" uppercase, ChatGPT Proxy uses "zh-CN"). See `app/config/languages.py` for mappings.

## Known Quirks

1. **Ren'Py Processing**: `read_rpy()` extracts dialogue using regex. Reconstruction in `reconstruct_rpy()` uses default parameters in closures to avoid variable binding issues (B007 lint rule).

2. **Chinese Language Detection**: Returns `zh`, `zh-cn`, or `zh-tw` depending on langdetect confidence. Services handle mapping.

3. **Parallel Translation Errors**: If a service fails during parallel translation, error message stored in results dict instead of raising exception (allows partial success).

4. **GUI Threading**: All long-running operations must use `threading.Thread` with `root.after()` callbacks to update UI from main thread.

5. **PyPDF2 Deprecation**: Uses PyPDF2 (deprecated) but functional. Warning suppressed in tests. Migration to pypdf planned but not urgent.
