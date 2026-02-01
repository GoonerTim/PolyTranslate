# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PolyTranslate** - Modern desktop translation application with beautiful UI and support for 9 translation services (Google FREE, Yandex FREE, DeepL, OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI) and 9 file formats (TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py). Built with Python 3.10+ and CustomTkinter GUI.

### Key Features (v2.1)
- **🆓 FREE Translation**: Google and Yandex work without API keys using unofficial public APIs
- **🎨 Modern UI**: Completely redesigned interface with gradients, icons, animations, and card-based layout
- **📑 Tabbed Interface**: All features in one window - Results, Comparison, History, Glossary tabs
- **🚀 Fast & Parallel**: Multi-threaded translation with real-time progress tracking
- **📊 Service Comparison**: Compare translations from multiple services side-by-side in grid layout

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

Services are **dynamically initialized** in `Translator._initialize_services()`.

**Important:** Google and Yandex services are **always initialized** (even without API keys) because they support free unofficial APIs as fallback:
- If API key exists: tries paid API first, falls back to free API on failure
- If no API key: uses free API directly
- `is_configured()` always returns `True` for these services

### Key Architectural Decisions

1. **Parallel Processing**: `Translator.translate_parallel()` uses `ThreadPoolExecutor` to translate multiple chunks across multiple services concurrently. Configurable via `max_workers` and `chunk_size`.

2. **Sentence Tokenization**: Uses NLTK's `sent_tokenize()` with `SimpleTokenizer` fallback if NLTK data unavailable. This ensures chunks break on sentence boundaries.

3. **Language Detection**: `LanguageDetector.detect()` wraps `langdetect` library with graceful degradation (returns None if unavailable or text too short).

4. **Settings Persistence**: `Settings` class manages JSON-based config in `config.json`. Uses deep merge strategy for updates (`_deep_merge()` method).

5. **GUI-Core Separation**: GUI (`app/gui/`) is completely decoupled from core logic (`app/core/`). Communication via callbacks and threading to prevent UI freezing.

6. **Free API Fallback**: Google and Yandex services implement automatic fallback to unofficial free APIs when API key is missing or paid API fails. This provides zero-configuration translation capability.

### Modern UI Design (v2.1)

**Design Philosophy**: Clean, minimal code with modern visual design. Docstrings removed from internal methods for brevity.

**Tabbed Interface Architecture (v2.1)**:
- **Single Window Design**: All features accessible from main window - no popup dialogs
- **4 Main Tabs**:
  - 📝 **Results**: Individual translations from each service (with nested service tabs)
  - 📊 **Comparison**: Side-by-side grid view of all translations (up to 3 columns)
  - 📜 **History**: Translation history with beautiful card layout
  - 📚 **Glossary**: Integrated glossary editor with real-time updates
- **Seamless Navigation**: One-click switching between all features
- **State Preservation**: Each tab maintains its state when switching

**Key UI Components**:
- **Card-based Layout**: Modern rounded corners, shadows, and spacing
- **Icon System**: Emoji-based service icons (🔷 DeepL, 🟣 Yandex, 🔴 Google, etc.)
- **Color Palette**:
  - Primary: `#2563eb` (blue)
  - Success: `#10b981` (green)
  - Error: `#ef4444` (red)
- **Interactive Feedback**: Hover effects, drag-drop visual states, smooth transitions
- **Progress Visualization**: Modern horizontal progress bar with percentage and status
- **Empty States**: Beautiful placeholders with helpful messages and large icons

**UI Architecture**:
- `MainWindow`: Main application window with integrated tabbed interface
  - `results_tabview`: CTkTabview containing all 4 main tabs
  - Manages tab content creation and updates
  - Handles switching between tabs programmatically
- `FileDropZone`: Modern drag-drop widget with visual feedback
- `ProgressBar`: Horizontal progress indicator with status and percentage
- **Removed**: `ComparisonView`, `HistoryView`, `GlossaryView` popup windows (now integrated tabs)
- All widgets use minimal docstrings, clean code structure

### File Processing Strategy

`FileProcessor` uses a **strategy pattern** with format-specific static methods:
- `read_txt()`, `read_pdf()`, `read_docx()`, etc.
- `process_file()` dispatches based on file extension
- `process_bytes()` for in-memory processing
- Special handling for Ren'Py (`.rpy`) with dialogue extraction and reconstruction

### Module Responsibilities

**Core Logic**:
- **`app/core/translator.py`**: Orchestrates entire translation workflow, manages service lifecycle
- **`app/core/file_processor.py`**: File format handling (9 formats), encoding detection, content extraction
- **`app/core/language_detector.py`**: Wrapper around langdetect with availability checks

**Configuration**:
- **`app/config/settings.py`**: JSON persistence, API key management, config deep merge
- **`app/config/languages.py`**: Language code mappings for different services (DeepL uses uppercase codes, ChatGPT Proxy has special mappings)

**Services** (with FREE API support):
- **`app/services/google.py`**: Google Translate - **FREE mode** (unofficial API) + paid API with fallback
- **`app/services/yandex.py`**: Yandex Translate - **FREE mode** (unofficial API) + paid API with fallback
- **`app/services/deepl.py`**: DeepL (requires API key)
- **`app/services/openai_service.py`**: OpenAI GPT (requires API key)
- **`app/services/claude.py`**: Claude AI (requires API key)
- **`app/services/groq_service.py`**: Groq (requires API key)
- **`app/services/openrouter.py`**: OpenRouter (requires API key)
- **`app/services/chatgpt_proxy.py`**: ChatGPT Proxy (no key required)
- **`app/services/localai.py`**: LocalAI (self-hosted)

**Modern UI** (excluded from test coverage):
- **`app/gui/main_window.py`**: Main window with integrated tabbed interface
  - 4 main tabs: Results, Comparison, History, Glossary
  - Manages all UI content and tab switching
  - Modern card-based layout, icon system, minimal docstrings
- **`app/gui/widgets/file_drop.py`**: Modern drag-drop zone with visual feedback
- **`app/gui/widgets/progress.py`**: Modern horizontal progress bar
- **`app/gui/settings_dialog.py`**: Settings dialog with API key configuration (still a popup for focused configuration)
- **`app/gui/history_view.py`**: TranslationHistory class for history persistence (UI now in main_window.py)
- **Note**: Comparison, History, and Glossary UI are now integrated tabs in `main_window.py` (not separate popup windows)

**Utilities**:
- **`app/utils/glossary.py`**: Term dictionary with post-processing replacement, JSON persistence

### Testing Strategy

**230 tests, 89% coverage** (GUI excluded)

- **Service Tests**: Mock HTTP with `responses` library. Example pattern:
  ```python
  @responses.activate
  def test_service(mock_response):
      responses.add(responses.POST, "https://api.url", json={...})
      result = service.translate("text", "en", "ru")
  ```

- **Free API Tests**: Test fallback mechanism for Google and Yandex
  - Test free API when no key provided
  - Test fallback from paid to free API on error
  - Mock both paid and free API endpoints

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

**Standard Service (requires API key)**:
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

**Service with Free API Fallback** (like Google/Yandex):
1. Implement `_translate_with_api_key()` and `_translate_free()` methods
2. `translate()` tries paid API first, falls back to free on error
3. `is_configured()` always returns `True`
4. `get_name()` returns service name + " (Free)" suffix when no API key

2. Register in `app/services/__init__.py`

3. Add initialization in `Translator._initialize_services()`:
   - For standard services: only initialize if API key exists
   - For free-capable services: always initialize

4. Create `tests/services/test_newservice.py` with mocked HTTP for both APIs

### Add File Format

1. Add method in `FileProcessor`: `read_newformat(content: bytes) -> str`

2. Update `SUPPORTED_EXTENSIONS` set

3. Add case in `process_bytes()` method

4. Add tests in `tests/test_file_processor_formats.py`

## Important Notes

- **Code Style**: Minimal docstrings in internal methods. Public APIs have brief docstrings. Comments removed for clean code. Type hints used throughout.

- **Free Translation**: Google and Yandex work immediately without API keys. Uses unofficial public APIs. May have rate limits or break if APIs change.

- **Type Checking**: Mypy reports ~36 warnings mostly from CustomTkinter (uses `Any` types). This is expected and acceptable.

- **NLTK Data**: Downloaded at runtime in `main.py` if missing. Tests handle missing NLTK gracefully.

- **API Key Security**: Never commit `config.json`. Keys stored locally only.

- **Coverage Target**: 70% minimum (pyproject.toml), currently 89%. GUI excluded from coverage (`app/gui/*` omitted).

- **Ruff Configuration**: Line length 100, ignores E501 (line too long), uses modern Python features (UP rules).

- **Language Code Mappings**: Different services use different codes (e.g., DeepL uses "EN" uppercase, ChatGPT Proxy uses "zh-CN"). See `app/config/languages.py` for mappings.

- **UI Design**: Modern card-based layout with emoji icons. Color scheme uses blue (#2563eb) for primary, green (#10b981) for success, red (#ef4444) for errors.

## UI Workflow (v2.1)

### Navigation Flow
1. User clicks menu button (📜 History, 📚 Glossary) → switches to that tab
2. "📊 Compare Results" button → switches to Comparison tab
3. Clicking history card → loads translation and switches to Results tab
4. All tabs accessible via direct clicking on tab headers

### Tab Content Management
- **Results Tab**: Dynamically creates service subtabs when translations complete
- **Comparison Tab**: Regenerates grid layout when translations update
- **History Tab**: Refreshes card list when history changes
- **Glossary Tab**: Maintains entry widgets state, saves on button click

### State Synchronization
- Translation results (`_translations` dict) shared across Results and Comparison tabs
- History loads translations into Results tab on selection
- Glossary saves trigger translator reload for immediate effect
- Clear button resets translations and switches back to Results tab

## Known Quirks

1. **Free API Reliability**: Google and Yandex free APIs are unofficial and may:
   - Have undocumented rate limits
   - Change without notice (breaking compatibility)
   - Be blocked in some regions
   - Paid API keys recommended for production use

2. **Ren'Py Processing**: `read_rpy()` extracts dialogue using regex. Reconstruction in `reconstruct_rpy()` uses default parameters in closures to avoid variable binding issues (B007 lint rule).

3. **Chinese Language Detection**: Returns `zh`, `zh-cn`, or `zh-tw` depending on langdetect confidence. Services handle mapping.

4. **Parallel Translation Errors**: If a service fails during parallel translation, error message stored in results dict instead of raising exception (allows partial success).

5. **GUI Threading**: All long-running operations must use `threading.Thread` with `root.after()` callbacks to update UI from main thread.

6. **PyPDF2 Deprecation**: Uses PyPDF2 (deprecated) but functional. Warning suppressed in tests. Migration to pypdf planned but not urgent.

7. **Minimal Docstrings**: Internal methods have no docstrings for clean code. Only public APIs documented. Use type hints and clear method names for self-documentation.

## UI Development Guidelines

### Modern Design Principles

**Color System**:
```python
# Primary colors
PRIMARY = ("#2563eb", "#1e40af")  # Blue (light, dark)
SUCCESS = ("#10b981", "#34d399")  # Green
ERROR = ("#ef4444", "#dc2626")    # Red
NEUTRAL = ("gray70", "gray30")    # Gray

# Usage
button = ctk.CTkButton(fg_color=PRIMARY, hover_color=("#1d4ed8", "#1e3a8a"))
```

**Icon System**:
- Use emoji icons for visual appeal
- Each service has unique icon: 🔷 DeepL, 🟣 Yandex, 🔴 Google, 🤖 OpenAI, etc.
- Functional icons: 📂 Open, ⚙️ Settings, 🚀 Translate, etc.

**Layout Patterns**:
- **Card-based**: Use `CTkFrame` with `corner_radius=12` for content grouping
- **Spacing**: Consistent padding (15-20px for cards, 5-10px for elements)
- **Typography**: Bold titles (size 14-16), regular text (size 12-13), small labels (size 11)

**Interactive Feedback**:
- Hover effects on buttons
- Color changes on drag-drop (green for valid, red for error)
- Progress indicators with percentage
- Empty states with helpful messages

### Adding UI Components

When adding new UI widgets:
1. Keep code clean - no verbose docstrings
2. Use type hints for parameters
3. Follow the color system and icon patterns
4. Ensure responsive layout (fill="both", expand=True)
5. Add visual feedback for user actions
6. Use `corner_radius` for modern look (8-15px)

Example:
```python
def _create_modern_button(self) -> None:
    button = ctk.CTkButton(
        self.parent,
        text="🚀 Action",
        command=self._on_action,
        width=150,
        height=40,
        corner_radius=10,
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color=("#2563eb", "#1e40af"),
        hover_color=("#1d4ed8", "#1e3a8a"),
    )
    button.pack(padx=10, pady=10)
```
