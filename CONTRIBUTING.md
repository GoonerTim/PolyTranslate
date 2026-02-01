# Contributing to PolyTranslate

Thank you for your interest in contributing to PolyTranslate! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and beginners
- Focus on constructive feedback
- Keep discussions professional

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**Good bug reports include:**
- Clear, descriptive title
- Exact steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Screenshots if applicable
- Error messages/stack traces

**Template:**
```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Windows 11]
- Python version: [e.g., 3.11.0]
- PolyTranslate version: [e.g., 1.0.0]

**Additional context**
Any other information.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.

**Include:**
- Clear, descriptive title
- Detailed description of the proposed functionality
- Use cases and examples
- Why this enhancement would be useful

### Adding Translation Services

To add a new translation service:

1. Create a new file in `app/services/`
2. Implement the `TranslationService` interface:

```python
from app.services.base import TranslationService

class NewService(TranslationService):
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        # Implementation
        pass

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_name(self) -> str:
        return "New Service"
```

3. Add tests in `tests/services/test_newservice.py`
4. Register service in `app/services/__init__.py`
5. Update documentation

### Adding File Format Support

To support a new file format:

1. Add reader method in `app/core/file_processor.py`:

```python
@staticmethod
def read_newformat(content: bytes) -> str:
    """Read .newformat files."""
    # Implementation
    return extracted_text
```

2. Update `SUPPORTED_EXTENSIONS` set
3. Add to `process_bytes()` method
4. Write tests in `tests/test_file_processor_formats.py`

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment tool

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/polytranslate.git
cd polytranslate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add docstrings to functions/classes
- Add type hints

### 3. Write Tests

**Required for:**
- New features
- Bug fixes
- Code changes

**Guidelines:**
- Aim for 80%+ coverage for new code
- Use pytest fixtures
- Mock external API calls
- Test edge cases and errors

**Example:**
```python
def test_new_feature():
    """Test description."""
    # Arrange
    translator = Translator()

    # Act
    result = translator.new_feature("input")

    # Assert
    assert result == "expected"
```

### 4. Run Quality Checks

Before committing, ensure all checks pass:

```bash
# Run tests
pytest

# Linting
ruff check .

# Auto-fix lint issues
ruff check . --fix

# Format code
ruff format .

# Type checking
mypy app/

# Run all at once
pytest && ruff check . && ruff format . --check && mypy app/
```

### 5. Commit Changes

**Commit message format:**
```
type: brief description

Detailed explanation (if needed)

Fixes #issue_number
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add support for GPT-4 model"
git commit -m "fix: handle empty file input correctly"
git commit -m "test: add integration tests for parallel translation"
```

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows project style
- [ ] Docstrings added/updated
- [ ] README updated (if needed)
- [ ] CHANGELOG updated (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] Code formatted with ruff
- [ ] No linting errors
```

### Review Process

1. Automated CI checks run
2. Maintainer reviews code
3. Address feedback if requested
4. Approved PRs are merged

## Code Style Guide

### Python Style

- Follow PEP 8
- Use type hints
- Max line length: 100 characters
- Use f-strings for formatting
- Prefer explicit over implicit

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_`

### Docstrings

Use Google-style docstrings:

```python
def translate(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text from source to target language.

    Args:
        text: The text to translate.
        source_lang: Source language code (e.g., 'en').
        target_lang: Target language code (e.g., 'ru').

    Returns:
        The translated text.

    Raises:
        ValueError: If language codes are invalid.
    """
    pass
```

### Type Hints

Always use type hints:

```python
from typing import Any
from collections.abc import Callable

def process(
    data: list[str],
    callback: Callable[[int, int], None] | None = None
) -> dict[str, Any]:
    """Process data with optional callback."""
    pass
```

## Testing Guidelines

### Test Structure

```python
class TestFeature:
    """Tests for Feature class."""

    def test_basic_functionality(self) -> None:
        """Test basic use case."""
        # Arrange
        feature = Feature()

        # Act
        result = feature.do_something()

        # Assert
        assert result == expected
```

### Fixtures

Use pytest fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def sample_translator(temp_dir: Path) -> Translator:
    """Create a translator instance for testing."""
    settings = Settings(temp_dir / "config.json")
    return Translator(settings)
```

### Mocking External APIs

Always mock external API calls:

```python
import responses

@responses.activate
def test_api_call():
    """Test API interaction."""
    responses.add(
        responses.POST,
        "https://api.example.com/translate",
        json={"result": "translated"},
        status=200
    )

    service = TranslationService()
    result = service.translate("hello", "en", "ru")
    assert result == "translated"
```

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Document parameters, return values, exceptions
- Include usage examples for complex functions

### User Documentation

- Update README.md for user-facing changes
- Add examples for new features
- Update screenshots if UI changes

## Questions?

- Check existing issues and PRs
- Ask in issue comments
- Create a discussion on GitHub

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to PolyTranslate! 🎉
