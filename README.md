# PolyTranslate

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/tests-268%20passed-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Modern desktop translation application with beautiful UI and support for multiple translation services**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Supported Services](#supported-services) • [Development](#development)

</div>

---

## 📋 Overview

PolyTranslate is a feature-rich desktop translation application with a **stunning modern UI** built with Python and CustomTkinter. It allows you to translate text and documents using multiple translation APIs simultaneously, compare results, and manage terminology with a built-in glossary.

## 🆕 What's New in v2.3

**🤖 AI-Powered Translation Evaluation**

Analyze your translations with artificial intelligence! The new AI Evaluation feature:

- **Rates each translation** with numerical scores (0-10) and detailed explanations
- **Identifies the best translation** automatically with visual highlighting
- **Generates an improved translation** combining the best aspects of all versions
- **Works with any LLM** - OpenAI, Claude, Groq, or LocalAI
- **Preserves Ren'Py structure** for game translation workflows
- **Saves evaluations to history** for future reference

Simply complete a translation, click "🤖 Evaluate All", and get instant AI-powered quality analysis!

### ✨ Key Features

- **9 Translation Services**: DeepL (FREE), Google (FREE), Yandex (FREE), OpenAI, Claude AI, Groq, OpenRouter, ChatGPT Proxy, LocalAI
- **9 File Formats**: TXT, PDF, DOCX, PPTX, XLSX, CSV, HTML, Markdown, Ren'Py scripts
- **🆓 FREE Services**: DeepL, Google, and Yandex work without API keys using unofficial APIs
- **🎨 Modern UI**: Beautiful redesigned interface with gradients, icons, and smooth animations
- **📑 Tabbed Interface**: All features in one window - no popup dialogs
- **✏️ Editable Translations**: Edit translations directly in the interface - all text areas are fully editable
- **📄 Original Text Comparison**: Compare translations with source text side-by-side
- **🤖 AI-Powered Evaluation**: Rate translation quality with scores (0-10), explanations, and AI-generated improvements
- **Parallel Processing**: Translate large texts in chunks with multiple workers
- **Service Comparison**: Compare translations from different services side-by-side in grid layout
- **Glossary Management**: Built-in glossary editor with real-time updates
- **Translation History**: Track and review past translations with instant loading
- **Auto Language Detection**: Automatically detect source language
- **Dark/Light Themes**: Toggle between beautiful light and dark themes
- **Drag & Drop**: Easy file loading with visual feedback
- **Progress Tracking**: Real-time translation progress with modern progress bar

### 🎨 Modern Interface

PolyTranslate features a completely redesigned modern UI with:

- **Beautiful Design**: Card-based layout with gradients and smooth animations
- **Tabbed Navigation**: 5 main tabs - Results, Comparison, AI Evaluation, History, Glossary
- **Single Window**: Everything in one place - no popup windows or dialogs
- **Icon Navigation**: Emoji-based menu system for intuitive navigation
- **Visual Feedback**: Hover effects, color-coded states, and smooth transitions
- **Service Icons**: Each translation service has a unique emoji identifier (🔷 DeepL, 🟣 Yandex, 🔴 Google, 🤖 AI, etc.)
- **Modern Progress Bar**: Real-time progress with percentage and status
- **Drag & Drop**: Visual feedback when dragging files (green highlight, success/error states)
- **Empty States**: Beautiful placeholder screens with helpful messages
- **Responsive Layout**: Adapts to different window sizes
- **Instant Switching**: Navigate between translations, comparisons, evaluations, history, and glossary with one click

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/GoonerTim/PolyTranslate.git
cd PolyTranslate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Development Install

For development with testing and linting tools:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

---

## 📖 Usage

### Running the Application

```bash
python main.py
```

### Basic Translation

1. **Load Text**: Drag & drop a file or click "Open" to browse
2. **Select Languages**: Choose source (or Auto) and target languages
3. **Select Services**: Check one or more translation services
4. **Translate**: Click the "🚀 Translate" button
5. **View & Edit Results**:
   - **📝 Results tab**: View individual translations from each service
     - All translations are **fully editable** - click and type to modify
     - Changes saved automatically
     - Use 💾 Save button to export edited translation to file
   - **📊 Comparison tab**: See original text + all translations side-by-side
     - Original text shown in first panel (📄 icon, green color)
     - Edit any translation directly in the comparison view
     - Perfect for comparing quality and making adjustments
   - Click "📊 Compare" button to quickly switch to comparison view

### AI-Powered Evaluation (NEW in v2.3)

**Analyze translation quality using AI:**

1. **Complete a translation** with one or more services
2. **Click "🤖 Evaluate All"** button (appears after translation)
3. **View AI analysis** with:
   - **Numerical scores** (0-10) for each translation
   - **Detailed explanations** highlighting strengths and weaknesses
   - **Best translation** automatically identified with 🏆 badge
   - **AI-improved translation** combining the best aspects of all translations
   - **Color-coded ratings**: Green (7+), Yellow (5-7), Red (<5)

**Features:**
- Works with **any LLM backend** (OpenAI, Claude, Groq, LocalAI)
- **Ren'Py game files** supported with structure preservation
- **All ratings displayed** in Results, Comparison, and dedicated AI Evaluation tabs
- **Evaluations saved** to history for future reference
- **Improved translation** is fully editable and exportable

**Setup:**
1. Open **Settings** (⚙️ button)
2. Go to **AI Evaluation Settings** section
3. Select your preferred AI service (OpenAI, Claude, Groq, or LocalAI)
4. Must have valid API key configured for that service
5. Leave empty to disable AI evaluation

**Note:** AI evaluation requires API calls to the selected LLM service and may incur costs depending on your service provider.

### Configuration

**Start translating immediately** with DeepL, Google, and Yandex (no API keys required)!

For other services, configure API keys in **Settings**:

- **DeepL**: ✅ **Works FREE without API key** (or use official API key for higher limits)
- **Google Translate**: ✅ **Works FREE without API key** (or use Google Cloud API for higher limits)
- **Yandex Translate**: ✅ **Works FREE without API key** (or use Yandex Cloud API for higher limits)
- **ChatGPT Proxy**: ✅ **No API key required** (uses proxy service)
- **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com)
- **Claude AI**: Get API key from [console.anthropic.com](https://console.anthropic.com)
- **Groq**: Register at [groq.com](https://groq.com)
- **OpenRouter**: Get key from [openrouter.ai](https://openrouter.ai)
- **LocalAI**: Configure your local server URL

### File Translation

Supported formats:
- **Text**: .txt, .md, .html
- **Documents**: .pdf, .docx, .pptx
- **Data**: .xlsx, .csv
- **Game Scripts**: .rpy (Ren'Py)

### Glossary Management

1. Click **📚 Glossary** button in the menu (or switch to Glossary tab)
2. Add term pairs (original → replacement)
3. Toggle "Case Sensitive" option if needed
4. Click "💾 Save" to apply changes
5. Terms are automatically applied after translation
6. Glossary persists in glossary.json

### Translation History

1. Click **📜 History** button in the menu (or switch to History tab)
2. Browse past translations with timestamps and metadata
3. Click any history card to reload that translation
4. Delete individual entries or clear all history
5. History limited to last 100 translations (auto-pruned)

---

## 🔌 Supported Services

| Service | API Key Required | Features | Languages |
|---------|-----------------|----------|-----------|
| **DeepL** | 🆓 **Optional** | Free API, high quality, fast | 30+ |
| **Google Translate** | 🆓 **Optional** | Free API, comprehensive, reliable | 100+ |
| **Yandex Translate** | 🆓 **Optional** | Free API, good for Cyrillic | 90+ |
| **ChatGPT Proxy** | ❌ No | Free, no registration | 100+ |
| **OpenAI GPT** | ✅ Yes | Context-aware, natural | All major |
| **Claude AI** | ✅ Yes | High quality, detailed | All major |
| **Groq** | ✅ Yes | Fast inference | All major |
| **OpenRouter** | ✅ Yes | Multiple models | All major |
| **LocalAI** | ❌ No* | Self-hosted, private | Depends on model |

*Requires local server setup

### 🆓 Free Services

**DeepL**, **Google**, and **Yandex** now work without API keys! The application uses their unofficial public APIs when no API key is provided. If you have an API key, it will be used with automatic fallback to the free API if it fails.

**Note**: Free APIs are unofficial and may have rate limits or break if the APIs change. Official API keys are recommended for production use.

---

## 🛠️ Development

### Project Structure

```
PolyTranslate/
├── app/
│   ├── config/          # Configuration management
│   ├── core/            # Core translation logic
│   ├── gui/             # Modern CustomTkinter UI (5 tabs)
│   ├── services/        # Translation service implementations
│   │   ├── ai_evaluator.py  # AI-powered evaluation service
│   │   └── ...          # Translation services (DeepL, Google, etc.)
│   └── utils/           # Utilities (glossary, etc.)
├── tests/               # Test suite (268 tests, 90% coverage)
├── main.py              # Application entry point
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── pyproject.toml       # Project configuration
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_translator.py -v

# Generate HTML coverage report
pytest --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check .

# Auto-fix issues
ruff check . --fix

# Formatting
ruff format .

# Type checking
mypy app/
```

### Pre-commit Hooks

Automatically runs linting and formatting before commits:

```bash
pre-commit install       # One-time setup
pre-commit run --all-files  # Manual run
```

---

## 🏗️ Architecture

### Core Components

- **Translator**: Orchestrates translation workflow, manages services
- **AIEvaluator**: AI-powered translation quality analysis
- **FileProcessor**: Handles file format reading/writing
- **LanguageDetector**: Auto-detects source language
- **Settings**: Manages API keys and application configuration
- **Glossary**: Term replacement engine

### Translation Workflow

```
File/Text → Process → Split into chunks → Parallel translation →
Reassemble → Apply glossary → Display results → (Optional) AI Evaluation
```

### AI Evaluation Workflow

```
User clicks "Evaluate All" → AI Evaluator generates scores/explanations →
Identifies best translation → Creates improved translation →
Display in Results/Comparison/AI Evaluation tabs → Save to history
```

### Service Architecture

All translation services implement the `TranslationService` interface:

```python
class TranslationService(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source to target language."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if service has required credentials."""

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable service name."""
```

---

## 📊 Testing

- **Unit Tests**: 268 tests covering all core modules
- **Integration Tests**: End-to-end workflow testing
- **Coverage**: 90% code coverage
- **CI/CD Ready**: All tests automated with pytest

Test categories:
- Translation service mocking (using `responses` library)
- AI evaluation (prompt generation, score parsing, Ren'Py preservation)
- Free API fallback mechanisms
- File format processing
- Parallel translation
- Error handling
- Settings persistence
- Language detection

---

## 🌍 Supported Languages

The application supports 40+ languages including:

English, Russian, German, French, Spanish, Italian, Dutch, Polish, Portuguese, Chinese, Japanese, Korean, Arabic, Turkish, Ukrainian, Czech, Swedish, Danish, Finnish, Norwegian, Hungarian, Greek, Hebrew, Thai, Vietnamese, Indonesian, Malay, Romanian, Bulgarian, Slovak, Slovenian, Croatian, Serbian, Lithuanian, Latvian, Estonian

*Language availability depends on the selected translation service*

---

## ⚙️ Configuration Files

- **config.json**: API keys, application settings, and AI evaluator configuration
- **glossary.json**: Custom terminology dictionary
- **history.json**: Translation history with evaluation scores and AI improvements

All configuration files are stored in the application directory and are user-editable.

---

## 🔒 Privacy & Security

- **Local Processing**: Files are processed locally
- **Secure Storage**: API keys stored in local config file
- **No Tracking**: No analytics or user tracking
- **Data Control**: You control what gets sent to translation APIs
- **Self-Hosted Option**: Use LocalAI for complete privacy

---

## 📦 Building Executable

Create standalone .exe using PyInstaller:

```bash
# Build using spec file
pyinstaller build.spec

# Executable will be in dist/PolyTranslate/
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🐛 Bug Reports & Feature Requests

Please use [GitHub Issues](https://github.com/GoonerTim/PolyTranslate/issues) to report bugs or request features.

When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Error messages/logs

---

## 🙏 Acknowledgments

Built with:
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [PyPDF2](https://github.com/py-pdf/pypdf2) - PDF processing
- [python-docx](https://python-docx.readthedocs.io/) - DOCX processing
- [pandas](https://pandas.pydata.org/) - Data file processing
- [NLTK](https://www.nltk.org/) - Natural language processing
- [langdetect](https://github.com/Mimino666/langdetect) - Language detection

---

## 📮 Contact

Project Link: [https://github.com/GoonerTim/PolyTranslate](https://github.com/GoonerTim/polytranslate)

---

<div align="center">
Made with ❤️ by the GoonerTim
</div>
