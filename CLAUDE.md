# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PolyTranslate** - Modern translation application with beautiful GUI and full CLI mode. Supports 9 translation services (DeepL FREE, Google FREE, Yandex FREE, OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI) and 9 file formats (TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, Ren'Py). Built with Python 3.10+ and CustomTkinter GUI.

### Key Features (v2.5)
- **🆓 FREE Translation**: DeepL, Google, and Yandex work without API keys using unofficial public APIs
- **🎨 Modern UI**: Completely redesigned interface with gradients, icons, animations, and card-based layout
- **📑 Tabbed Interface**: All features in one window - Results, Comparison, AI Evaluation, History, Glossary tabs
- **✏️ Editable Translations**: All translation text areas are fully editable with auto-save
- **📄 Original Comparison**: View source text alongside translations in comparison tab
- **🚀 Fast & Parallel**: Multi-threaded translation with real-time progress tracking
- **📊 Service Comparison**: Compare original + translations from multiple services side-by-side in grid layout
- **🤖 AI-Powered Evaluation**: Rate translation quality with scores (0-10), explanations, and AI-generated improvements
- **⌨️ CLI Mode**: Full command-line interface for scripting, automation, and terminal workflows (v2.5)
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

### AI Evaluation Flow (v2.3+)
```
User clicks "🤖 Evaluate All" / "🤖 Agent Vote"
  → If agents configured (v2.4):
      → AgentVoting.vote_on_translations()
          → Build Ren'Py context (if .rpy file + game folder set)
          → For each agent in parallel (ThreadPoolExecutor):
              → Create LLM client (reuses existing services)
              → Send voting prompt (scores + merged in 1 call)
              → Parse JSON response → AgentVote
          → Compute weighted consensus scores
          → Determine majority best service
          → Select merged translation from highest-weight agent
      → Convert VotingResult → EvaluationResult for UI compatibility
  → Else (single evaluator, v2.3):
      → AIEvaluator.evaluate_translations()
          → LLM Service generates evaluation for each translation
              → Returns: scores (0-10), explanations, strengths/weaknesses
          → LLM Service generates improved translation
              → Combines best aspects of all translations
              → Preserves Ren'Py structure if applicable
  → Store evaluations in _evaluations dict
  → Identify best service by highest score
  → Update UI:
      → Results tab: Show rating frames with scores/explanations/badges
      → Comparison tab: Show score badges and highlight best with border
      → AI Evaluation tab: Show detailed report + agent votes table (if voting)
  → Save to history with evaluation data
```

**Key Components:**
- **AIEvaluator** (`app/services/ai_evaluator.py`): Single-service translation quality evaluation
- **AgentVoting** (`app/services/agent_voting.py`): Multi-agent voting system with weighted consensus (v2.4)
- **RenpyContextExtractor** (`app/core/renpy_context.py`): Game context parser for Ren'Py files (v2.4)
- **EvaluationResult**: Dataclass storing score, explanation, timestamp, strengths/weaknesses
- **AgentConfig/AgentVote/VotingResult**: Dataclasses for agent voting workflow (v2.4)
- **LLM Backend**: User-configurable (OpenAI/Claude/Groq/LocalAI) via Settings
- **Ren'Py Preservation**: Special handling to maintain game file structure in improved translations
- **UI Integration**: Ratings displayed in Results, Comparison, and dedicated AI Evaluation tabs

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
- **DeepL Rate Limiting**: Uses class-level lock and timestamp to enforce 1-second minimum interval between free API requests; automatically retries with exponential backoff (2s, 4s, 8s) on HTTP 429 errors

### Key Architectural Decisions

1. **Parallel Processing**: `Translator.translate_parallel()` uses `ThreadPoolExecutor` to translate multiple chunks across multiple services concurrently. Configurable via `max_workers` and `chunk_size`.

2. **Sentence Tokenization**: Uses NLTK's `sent_tokenize()` with `SimpleTokenizer` fallback if NLTK data unavailable. This ensures chunks break on sentence boundaries.

3. **Language Detection**: `LanguageDetector.detect()` wraps `langdetect` library with graceful degradation (returns None if unavailable or text too short).

4. **Settings Persistence**: `Settings` class manages JSON-based config in `config.json`. Uses deep merge strategy for updates (`_deep_merge()` method).

5. **GUI-Core Separation**: GUI (`app/gui/`) is completely decoupled from core logic (`app/core/`). Communication via callbacks and threading to prevent UI freezing.

6. **Free API Fallback**: DeepL, Google, and Yandex services implement automatic fallback to unofficial free APIs when API key is missing or paid API fails. This provides zero-configuration translation capability.

### Modern UI Design (v2.2)

**Design Philosophy**: Clean, minimal code with modern visual design. Docstrings removed from internal methods for brevity.

**Tabbed Interface Architecture (v2.2)**:
- **Single Window Design**: All features accessible from main window - no popup dialogs
- **4 Main Tabs**:
  - 📝 **Results**: Individual translations from each service (with nested service tabs)
    - **Editable**: All text areas fully editable with auto-save on modification
    - Changes synchronized via `<<Modified>>` event binding
  - 📊 **Comparison**: Side-by-side grid view with original text + translations (up to 3 columns)
    - **Original Text Panel**: First panel shows source text (📄 icon, green color, read-only)
    - **Editable Translations**: Edit any translation directly in comparison view
    - Grid layout adapts dynamically (original + N translations)
  - 📜 **History**: Translation history with beautiful card layout
    - Loads both translations and original text when selected
  - 📚 **Glossary**: Integrated glossary editor with real-time updates
- **Seamless Navigation**: One-click switching between all features
- **State Preservation**: Each tab maintains its state when switching
- **Edit Tracking**: Text modifications automatically update translation dictionary

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
- `split_rpy_by_scenes()`: Splits `.rpy` content by `label` blocks into `(label_name, scene_content)` tuples (v2.4)
  - Handles preamble content before first label
  - Falls back to single `("_full", content)` when no labels found

### Module Responsibilities

**CLI** (v2.5):
- **`app/cli.py`**: Command-line interface with 5 commands (translate, services, languages, detect, config)
  - `create_parser()`: Builds argparse parser with all commands, aliases, and options
  - `run_cli()`: Entry point — parses args and dispatches to command handlers
  - `cmd_translate()`: Translates text/file with progress bar, supports stdin pipe, JSON output
  - `cmd_services()`: Lists all services with availability and selection status
  - `cmd_languages()`: Lists all supported language codes
  - `cmd_detect()`: Detects language of text/file
  - `cmd_config()`: Shows config (keys masked), sets values, manages API keys
  - Smart dispatch in `main.py`: CLI commands auto-detected from `sys.argv[1]`, falls back to GUI

**Core Logic**:
- **`app/core/translator.py`**: Orchestrates entire translation workflow, manages service lifecycle
- **`app/core/file_processor.py`**: File format handling (9 formats), encoding detection, content extraction
  - `split_rpy_by_scenes()`: Splits `.rpy` files by `label` blocks for scene-based processing (v2.4)
- **`app/core/language_detector.py`**: Wrapper around langdetect with availability checks
- **`app/core/renpy_context.py`**: Ren'Py game context extractor (v2.4)
  - Parses `define ... = Character(...)` declarations from all `.rpy` files
  - Extracts scene labels, characters present per scene, dialogue previews
  - Generates compact context strings for LLM prompts (truncated by max_tokens)

**Configuration**:
- **`app/config/settings.py`**: JSON persistence, API key management, config deep merge
  - Includes AI evaluator settings: `ai_evaluator_service`, `ai_evaluator_model`, `ai_evaluation_auto`
  - Agent voting settings: `agents` (list of agent configs), `renpy_game_folder`, `renpy_processing_mode` (v2.4)
- **`app/config/languages.py`**: Language code mappings for different services (DeepL uses uppercase codes, ChatGPT Proxy has special mappings)

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
- **`app/services/ai_evaluator.py`**: AI-powered translation evaluation (v2.3)
  - Uses any LLM service (OpenAI/Claude/Groq/LocalAI) as backend
  - Generates scores (0-10), explanations, and improved translations
  - Preserves Ren'Py structure in improved translations
- **`app/services/agent_voting.py`**: Multi-agent voting system (v2.4)
  - `AgentConfig`: Dataclass for agent definition (name, base_url, model, api_key, agent_type, weight)
  - `AgentVoting`: Orchestrates parallel voting across multiple LLM agents
  - `_create_agent_client()`: Reuses existing service classes (LocalAI/OpenAI/Claude/Groq) by agent_type
  - `_compute_consensus()`: Weighted average scores, majority vote for best, highest-weight merged translation
  - Graceful degradation: failed agents are skipped, continues with remaining
  - 1 LLM call per agent (scores + merge in single prompt) for token efficiency

**Modern UI** (excluded from test coverage):
- **`app/gui/main_window.py`**: Main window with integrated tabbed interface
  - 5 main tabs: Results, Comparison, AI Evaluation, History, Glossary
  - Manages all UI content and tab switching
  - Modern card-based layout, icon system, minimal docstrings
  - AI Evaluation tab shows detailed ratings and improved translation
  - Agent voting integration: auto-detects agents config, builds Ren'Py context, shows vote table (v2.4)
  - Button text dynamically switches: "🤖 Agent Vote" (with agents) / "🤖 Evaluate All" (without)
- **`app/gui/widgets/file_drop.py`**: Modern drag-drop zone with visual feedback
- **`app/gui/widgets/progress.py`**: Modern horizontal progress bar
- **`app/gui/settings_dialog.py`**: Settings dialog with API key configuration (still a popup for focused configuration)
  - "AI Agents" section: dynamic agent rows (name, type, URL, model, API key, weight slider) with add/remove (v2.4)
  - "Ren'Py Settings" section: game folder browse + processing mode dropdown (v2.4)
- **`app/gui/history_view.py`**: TranslationHistory class for history persistence (UI now in main_window.py)
- **Note**: Comparison, History, and Glossary UI are now integrated tabs in `main_window.py` (not separate popup windows)

**Utilities**:
- **`app/utils/glossary.py`**: Term dictionary with post-processing replacement, JSON persistence

### Testing Strategy

**350 tests, 91% coverage** (GUI excluded)

- **Service Tests**: Mock HTTP with `responses` library. Example pattern:
  ```python
  @responses.activate
  def test_service(mock_response):
      responses.add(responses.POST, "https://api.url", json={...})
      result = service.translate("text", "en", "ru")
  ```

- **Free API Tests**: Test fallback mechanism for DeepL, Google, and Yandex
  - Test free API when no key provided
  - Test fallback from paid to free API on error
  - Mock both paid and free API endpoints

- **AI Evaluator Tests** (`tests/test_ai_evaluator.py`): Comprehensive evaluation testing
  - Test evaluation result dataclass creation
  - Test evaluation with various LLM responses (JSON, markdown code blocks)
  - Test score clamping (0-10 range)
  - Test Ren'Py structure preservation in improved translations
  - Test error handling (evaluation failures, improvement failures)
  - Test prompt generation for evaluation and improvement
  - 19 tests with 97% coverage of ai_evaluator.py

- **Agent Voting Tests** (`tests/test_agent_voting.py`): Multi-agent voting system testing (v2.4)
  - Dataclass creation, validation (empty translations, no agents)
  - Single and multi-agent voting with weighted consensus
  - Full and partial agreement ratio calculation
  - Graceful agent failure handling (skip failed, continue with rest)
  - Voting prompt generation (with/without Ren'Py context)
  - JSON response parsing (valid, code-block-wrapped, invalid)
  - Score clamping (0-10 range), auto-detect best from scores
  - Agent client creation for all 4 service types
  - 25 tests with 95% coverage of agent_voting.py

- **Ren'Py Context Tests** (`tests/test_renpy_context.py`): Context extraction testing (v2.4)
  - Character parsing from `define` statements (with/without color kwargs)
  - Scene extraction from `label` blocks
  - Characters-per-scene detection
  - Context string format and truncation by max_tokens
  - Edge cases: empty folder, nonexistent folder, dialogue preview limits
  - 13 tests with 92% coverage of renpy_context.py

- **Ren'Py Scene Splitting Tests** (`tests/test_file_processor_renpy_scenes.py`): Scene-based file splitting (v2.4)
  - Multi-label splitting with correct boundaries
  - No-label fallback, single-label, preamble handling
  - 6 tests

- **CLI Tests** (`tests/test_cli.py`): Command-line interface testing (v2.5)
  - Parser creation and argument parsing for all commands
  - Translate: text, file, stdin, JSON output, file output, all-services, auto-detect
  - Services listing, language listing, language detection
  - Config: show (masked keys), set values, set API keys
  - Error handling: missing input, invalid services, file not found
  - 33 tests

- **Integration Tests** (`tests/test_integration.py`): End-to-end workflows including file→process→translate→save, parallel processing, error handling, progress callbacks.

- **File Format Tests** (`tests/test_file_processor_formats.py`): Create actual files in-memory (PyPDF2, python-docx, python-pptx, pandas), test extraction.

- **Fixtures** (`tests/conftest.py`): `temp_dir`, `sample_txt_file`, `sample_rpy_content` used across tests.

### Configuration Files

Runtime config (gitignored):
- **`config.json`**: API keys, theme, chunk_size, max_workers, selected_services, ai_evaluator_service, agents, renpy_game_folder, renpy_processing_mode
- **`glossary.json`**: User term dictionary
- **`history.json`**: Translation history (v2.3: includes evaluation scores, explanations, ai_improved, best_service)

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

### Add Voting Agent Type

1. Implement a new `TranslationService` subclass (or reuse existing one)

2. Add case in `AgentVoting._create_agent_client()`:
   ```python
   elif agent.agent_type == "newtype":
       from app.services.newservice import NewService
       return NewService(api_key=agent.api_key, model=agent.model)
   ```

3. Add to `SettingsDialog.AGENT_TYPES` list

4. Add tests in `tests/test_agent_voting.py` for client creation

### Add File Format

1. Add method in `FileProcessor`: `read_newformat(content: bytes) -> str`

2. Update `SUPPORTED_EXTENSIONS` set

3. Add case in `process_bytes()` method

4. Add tests in `tests/test_file_processor_formats.py`

## Important Notes

- **Code Style**: Minimal docstrings in internal methods. Public APIs have brief docstrings. Comments removed for clean code. Type hints used throughout.

- **Free Translation**: DeepL, Google, and Yandex work immediately without API keys. Uses unofficial public APIs. May have rate limits or break if APIs change.

- **Type Checking**: Mypy reports ~36 warnings mostly from CustomTkinter (uses `Any` types). This is expected and acceptable.

- **NLTK Data**: Downloaded at runtime in `main.py` if missing. Tests handle missing NLTK gracefully.

- **API Key Security**: Never commit `config.json`. Keys stored locally only.

- **Coverage Target**: 70% minimum (pyproject.toml), currently 91%. GUI excluded from coverage (`app/gui/*` omitted).

- **Ruff Configuration**: Line length 100, ignores E501 (line too long), uses modern Python features (UP rules).

- **Language Code Mappings**: Different services use different codes (e.g., DeepL uses "EN" uppercase, ChatGPT Proxy uses "zh-CN"). See `app/config/languages.py` for mappings.

- **UI Design**: Modern card-based layout with emoji icons. Color scheme uses blue (#2563eb) for primary, green (#10b981) for success, red (#ef4444) for errors.

## AI Evaluation Feature (v2.3)

### Overview
AI-powered translation quality evaluation system that analyzes multiple translations, provides numerical scores (0-10) with explanations, highlights the best translation, and optionally generates an improved combined translation.

### Configuration

**Settings:**
1. Open Settings (⚙️ button in menu)
2. Navigate to "AI Evaluation Settings" section
3. Select AI Evaluator Service:
   - **OpenAI**: Uses GPT models (requires API key)
   - **Claude**: Uses Anthropic's Claude (requires API key)
   - **Groq**: Fast inference (requires API key)
   - **LocalAI**: Self-hosted, privacy-focused (requires server URL)
4. Leave empty to disable AI evaluation feature

**Required Setup:**
- At least one LLM service must be configured
- Service must have valid API key (except LocalAI which uses server URL)
- Evaluation uses the same API key as translation for that service

### Usage Workflow

1. **Translate Text**: Complete a translation with one or more services
2. **Click "🤖 Evaluate All"**: Button appears after translation (only if AI evaluator configured)
3. **Wait for Evaluation**: Progress bar shows "Evaluating translations..."
4. **View Results**: Automatically switches to AI Evaluation tab showing:
   - Summary statistics (number of translations, best service, average score)
   - Detailed evaluations for each service with scores and explanations
   - AI-generated improved translation (editable, copyable, saveable)

### UI Display

**Results Tab** (after evaluation):
- Each service tab shows rating frame with:
  - ⭐ Score (0-10)
  - Brief explanation of quality
  - 🏆 BEST badge for highest-rated translation
  - Color-coded background (green: 7+, yellow: 5-7, red: <5)

**Comparison Tab** (after evaluation):
- Score badges in panel headers
- 🏆 icon for best translation
- Green border highlighting best translation panel

**AI Evaluation Tab**:
- Summary statistics section
- Detailed evaluation cards (sorted by score, descending)
- Improved translation section with editable text area
- Copy and Save buttons for improved translation

### Evaluation Criteria

LLM evaluates each translation based on:
- **Accuracy**: Faithfulness to original meaning
- **Fluency**: Natural language flow
- **Naturalness**: Idiomatic expressions, cultural appropriateness

Scores are automatically clamped to 0-10 range.

### Ren'Py File Support

Special handling for Ren'Py game files (`.rpy`):
- AI evaluator detects Ren'Py dialogue patterns
- Improved translation preserves:
  - Label declarations (`label start:`)
  - Character names
  - Indentation levels
  - Dialogue quote markers (`"..."`)
- Ensures translated game files remain syntactically valid

### History Integration

Evaluations are automatically saved to history:
- Scores and explanations persist across sessions
- AI-improved translation stored separately
- Best service marked for quick reference
- Load from history restores all evaluation data

### Performance Notes

- Evaluation requires 2 LLM calls: one for ratings, one for improvement
- Expected time: 5-15 seconds depending on LLM service speed
- LocalAI typically slower but more private
- Costs token usage (see LLM service pricing)

## Multi-Agent Voting System (v2.4)

### Overview
Multi-agent voting system where multiple AI agents (local and cloud LLMs) independently evaluate translations, vote on the best one, and produce a merged/improved translation. Overrides single AI Evaluator when agents are configured.

### Architecture

**Key Classes** (`app/services/agent_voting.py`):
- `AgentConfig`: Defines an agent (name, base_url, model, api_key, agent_type, weight)
- `AgentVote`: Single agent's response (scores per service, best pick, explanations, merged translation)
- `VotingResult`: Aggregated result (consensus scores, consensus best, agreement ratio, merged translation)
- `AgentVoting`: Orchestrator — sends prompts in parallel, collects votes, computes consensus

**Flow:**
```
Settings: agents = [{name, base_url, model, api_key, agent_type, weight}, ...]
  → User clicks "🤖 Agent Vote"
  → MainWindow._start_agent_voting()
      → Build AgentConfig list from settings
      → If .rpy file + renpy_game_folder → RenpyContextExtractor.get_context_for_text()
      → Create AgentVoting(agents, context)
      → Thread: AgentVoting.vote_on_translations()
          → For each agent (parallel, ThreadPoolExecutor):
              → _create_agent_client() → reuses LocalAI/OpenAI/Claude/Groq service classes
              → client.translate(voting_prompt) → single LLM call with JSON response
              → _parse_agent_response() → AgentVote
          → _compute_consensus():
              → Weighted average scores per service
              → Consensus best = highest weighted average score
              → Agreement ratio = fraction of agents agreeing on best
              → Merged translation from highest-weight agent
      → Convert VotingResult → dict[str, EvaluationResult] for UI compatibility
      → _on_evaluation_complete() (same UI path as single evaluator)
```

**Agent Types:**
- `localai`: Uses `LocalAIService(base_url, model, api_key)` — for local LLMs (LM Studio, Ollama, etc.)
- `openai`: Uses `OpenAIService(api_key, model)` — GPT models
- `claude`: Uses `ClaudeService(api_key, model)` — Anthropic models
- `groq`: Uses `GroqService(api_key, model)` — fast inference

**Configuration** (`config.json`):
```json
{
  "agents": [
    {
      "name": "Mistral 7B",
      "base_url": "http://localhost:1234/v1",
      "model": "mistral-7b",
      "api_key": "not-needed",
      "agent_type": "localai",
      "weight": 1.0
    },
    {
      "name": "GPT-4o",
      "base_url": "",
      "model": "gpt-4o",
      "api_key": "sk-...",
      "agent_type": "openai",
      "weight": 1.5
    }
  ],
  "renpy_game_folder": "/path/to/game",
  "renpy_processing_mode": "scenes"
}
```

**Consensus Algorithm:**
- Weighted average: `score[service] = Σ(vote.scores[service] * agent.weight) / Σ(agent.weight)`
- Best service: highest weighted average score (not majority vote of best_service picks)
- Agreement ratio: `count(agents who picked consensus_best) / total_agents`
- Merged translation: from agent with highest weight that provided one

**Error Handling:**
- Failed agents are silently skipped (logged as warning)
- If all agents fail → `RuntimeError("All agents failed to respond")`
- 60s timeout per agent, 120s total for ThreadPoolExecutor
- Invalid JSON responses produce empty AgentVote (no scores)

### Settings UI

In Settings dialog → "AI Agents (Multi-Agent Voting)" section:
- Dynamic agent rows with: Name, Type (dropdown), URL (LocalAI only), Model, API Key, Weight (slider 0.5-2.0)
- "+ Add Agent" button, "X" Remove button per row
- URL field disabled for non-localai agent types

## Ren'Py Context Awareness (v2.4)

### Overview
Extracts structured game context from Ren'Py project folders and injects it into evaluation/voting prompts, giving LLMs awareness of characters, scenes, and dialogue flow.

### Architecture

**Key Classes** (`app/core/renpy_context.py`):
- `RenpyCharacter`: variable, name, color
- `RenpyScene`: label, characters_present, dialogue_preview (first 5 lines)
- `RenpyContext`: characters, scenes, current_scene, nearby_dialogue
- `RenpyContextExtractor`: Parses all `.rpy` files in game folder

**Parsing Regexes:**
- Characters: `^\s*define\s+(\w+)\s*=\s*Character\s*\(\s*["'](.+?)["']...`
- Scenes: `^\s*label\s+(\w+)\s*:`
- Dialogue: `^\s+(\w+)\s+["'](.*?)["']`

**Context String Format:**
```
== GAME CONTEXT ==
Characters: e=Eileen, mc=Main Character
Current Scene: start
Recent dialogue:
  e: "Hello!"
  mc: "Hi!"
== END CONTEXT ==
```

Truncated by `max_tokens` (default 1500, ~6000 chars) for small model compatibility.

### Ren'Py Processing Modes

Setting `renpy_processing_mode` controls how `.rpy` files are split for translation:
- `"scenes"` (default, recommended): `FileProcessor.split_rpy_by_scenes()` splits by `label` blocks
- `"chunks"`: Standard `split_text()` chunking with context in prompt
- `"full"`: Entire file as single chunk

### Integration Points

- `MainWindow._start_agent_voting()`: Creates `RenpyContextExtractor` if `.rpy` file and `renpy_game_folder` set
- `AgentVoting.__init__(agents, context)`: Receives context string, injects into voting prompt
- Settings dialog: "Ren'Py Game Folder" (browse) + "Processing Mode" (dropdown)

## UI Workflow (v2.3+)

### Navigation Flow
1. User clicks menu button (📜 History, 📚 Glossary) → switches to that tab
2. "📊 Compare" button → switches to Comparison tab
3. "🤖 Evaluate All" / "🤖 Agent Vote" button → evaluates translations and switches to AI Evaluation tab
4. Clicking history card → loads translation + original text + evaluations and switches to Results tab
5. All tabs accessible via direct clicking on tab headers

### Tab Content Management
- **Results Tab**: Dynamically creates service subtabs when translations complete
  - Text areas are editable with auto-save on modification
  - Edit tracking via `<<Modified>>` event binding
  - Shows rating frames with scores/explanations if evaluations exist
- **Comparison Tab**: Regenerates grid layout when translations update
  - Shows original text (if available) as first panel
  - Translation panels are editable
  - Grid adapts to N+1 panels (original + translations)
  - Displays score badges and best service highlighting
- **AI Evaluation Tab**: Shows detailed evaluation report
  - Summary statistics (evaluated count, best service, average score)
  - Agent votes table with agreement indicator (v2.4, shown when agents used)
  - Detailed evaluation cards sorted by score
  - AI-improved/merged translation with edit/copy/save capabilities
- **History Tab**: Refreshes card list when history changes
- **Glossary Tab**: Maintains entry widgets state, saves on button click

### State Synchronization
- Translation results (`_translations` dict) shared across Results and Comparison tabs
- Original text (`_original_text`) stored before translation and loaded from history
- History loads both translations and original text into Results tab on selection
- Text edits update `_translations` dictionary in real-time
- Glossary saves trigger translator reload for immediate effect
- Clear button resets translations, original text, and switches back to Results tab

### Edit Features
- **Editable Text Areas**: All translation textboxes in normal state (not read-only)
- **Auto-save**: Modifications tracked via Tkinter's `<<Modified>>` event
- **Original Protection**: Original text panel is disabled (read-only) in Comparison tab
- **Copy with Edits**: Copy button uses current content (including user edits)

## Known Quirks

1. **Free API Reliability**: DeepL, Google, and Yandex free APIs are unofficial and may:
   - Have undocumented rate limits (DeepL has built-in rate limiting and retry logic)
   - Change without notice (breaking compatibility)
   - Be blocked in some regions
   - Paid API keys recommended for production use
   - **DeepL Rate Limiting**: Automatically throttles requests (1 second minimum interval) and retries with exponential backoff (2s, 4s, 8s) on 429 errors

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
