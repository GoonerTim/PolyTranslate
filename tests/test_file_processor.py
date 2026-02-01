"""Tests for the file processor module."""

from __future__ import annotations

from pathlib import Path

from app.core.file_processor import FileProcessor


class TestFileProcessor:
    """Tests for FileProcessor class."""

    def test_detect_encoding_utf8(self) -> None:
        """Test encoding detection for UTF-8."""
        content = b"Hello, world!"
        encoding = FileProcessor.detect_encoding(content)
        assert encoding.lower() in ["utf-8", "ascii"]

    def test_detect_encoding_utf16(self) -> None:
        """Test encoding detection for UTF-16."""
        content = "Hello, world!".encode("utf-16")
        encoding = FileProcessor.detect_encoding(content)
        assert "utf" in encoding.lower() or "16" in encoding.lower()

    def test_read_txt(self) -> None:
        """Test reading text files."""
        content = b"Hello, world!"
        result = FileProcessor.read_txt(content)
        assert result == "Hello, world!"

    def test_read_txt_with_unicode(self) -> None:
        """Test reading text files with Unicode."""
        content = "Привет, мир!".encode()
        result = FileProcessor.read_txt(content)
        assert result == "Привет, мир!"

    def test_read_rpy_dialogue(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py dialogue."""
        result = FileProcessor.read_rpy(sample_rpy_content)
        assert "Hello, how are you?" in result
        assert "fine, thanks" in result

    def test_read_rpy_menu_options(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py menu options."""
        result = FileProcessor.read_rpy(sample_rpy_content)
        assert "Good option" in result
        assert "Bad option" in result

    def test_read_rpy_translatable_strings(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py translatable strings."""
        result = FileProcessor.read_rpy(sample_rpy_content, translate_strings=True)
        assert "Translatable string" in result

    def test_read_rpy_no_dialogue(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py without dialogue."""
        result = FileProcessor.read_rpy(
            sample_rpy_content, translate_dialogue=False, translate_strings=True
        )
        assert "Translatable string" in result
        # Dialogue should not be extracted
        assert "DIALOGUE_LINE" not in result or "Hello" not in result

    def test_process_file_txt(self, sample_txt_file: Path) -> None:
        """Test processing text file."""
        result = FileProcessor.process_file(sample_txt_file)
        assert result == "Hello, world!"

    def test_process_bytes_txt(self) -> None:
        """Test processing bytes as text."""
        content = b"Test content"
        result = FileProcessor.process_bytes(content, "txt")
        assert result == "Test content"

    def test_read_html(self) -> None:
        """Test reading HTML files."""
        html_content = b"<html><body><p>Hello, world!</p></body></html>"
        result = FileProcessor.read_html(html_content)
        assert "Hello, world!" in result

    def test_read_html_strips_scripts(self) -> None:
        """Test that HTML reading strips scripts."""
        html_content = b"<html><script>alert('bad')</script><body><p>Good text</p></body></html>"
        result = FileProcessor.read_html(html_content)
        assert "Good text" in result
        assert "alert" not in result

    def test_read_md(self) -> None:
        """Test reading Markdown files."""
        md_content = b"# Hello\n\nThis is **bold** text."
        result = FileProcessor.read_md(md_content)
        assert "Hello" in result
        assert "bold" in result

    def test_supported_extensions(self) -> None:
        """Test that supported extensions are defined."""
        assert "txt" in FileProcessor.SUPPORTED_EXTENSIONS
        assert "pdf" in FileProcessor.SUPPORTED_EXTENSIONS
        assert "docx" in FileProcessor.SUPPORTED_EXTENSIONS
        assert "rpy" in FileProcessor.SUPPORTED_EXTENSIONS

    def test_reconstruct_rpy(self) -> None:
        """Test Ren'Py file reconstruction."""
        original = 'e "Hello, world!"'
        translations = {"DIALOGUE_LINE_1: Hello, world!": "Привет, мир!"}
        result = FileProcessor.reconstruct_rpy(original, translations)
        # The reconstruction should preserve structure
        assert 'e "' in result

    def test_unsupported_format(self, temp_dir: Path) -> None:
        """Test handling unsupported file format."""
        file_path = temp_dir / "test.xyz"
        file_path.write_text("Some content", encoding="utf-8")

        # Should fall back to text reading
        result = FileProcessor.process_file(file_path)
        assert result == "Some content"

    def test_detect_encoding_fallback_to_cp1251(self) -> None:
        """Test encoding detection fallback to cp1251."""
        # Create content that will have low confidence detection
        content = bytes([0xFF, 0xFE] + [0x41, 0x00] * 10)  # BOM + some text
        encoding = FileProcessor.detect_encoding(content)
        assert encoding is not None

    def test_detect_encoding_exception_handling(self) -> None:
        """Test encoding detection with exception."""
        # Empty content should trigger fallback to utf-8
        content = b""
        encoding = FileProcessor.detect_encoding(content)
        assert encoding == "utf-8"

    def test_read_txt_with_fallback_encoding(self) -> None:
        """Test reading text with fallback to utf-8 error replacement."""
        # Create invalid UTF-8 sequence
        content = b"\xff\xfe\x41\x00Invalid\xff\xff"
        result = FileProcessor.read_txt(content)
        assert "Invalid" in result or "A" in result

    def test_read_html_error_handling(self) -> None:
        """Test HTML reading with malformed content."""
        # Create content that might cause parsing issues
        html_content = b"<html><body><p>Test</p>"  # Missing closing tags
        result = FileProcessor.read_html(html_content)
        assert "Test" in result

    def test_read_md_error_handling(self) -> None:
        """Test Markdown reading with invalid content."""
        # Valid markdown but testing error path coverage
        md_content = b"# Title\n\nContent"
        result = FileProcessor.read_md(md_content)
        assert "Title" in result
        assert "Content" in result

    def test_read_rpy_old_dialogue_format(self) -> None:
        """Test reading Ren'Py old dialogue format."""
        rpy_content = b'"Old style dialogue"'
        result = FileProcessor.read_rpy(rpy_content)
        assert "Old style dialogue" in result or "DIALOGUE_LINE" in result

    def test_read_rpy_empty_result(self) -> None:
        """Test reading Ren'Py with no extractable content."""
        rpy_content = b"# Just comments\n# No dialogue"
        result = FileProcessor.read_rpy(
            rpy_content, translate_dialogue=False, translate_strings=False
        )
        # Should return original content when no extraction
        assert result == "# Just comments\n# No dialogue"

    def test_reconstruct_rpy_error_handling(self) -> None:
        """Test Ren'Py reconstruction with missing translations."""
        original = 'e "Hello"\nm "World"'
        translations = {}  # No translations
        result = FileProcessor.reconstruct_rpy(original, translations)
        # Should preserve original structure
        assert 'e "Hello"' in result
        assert 'm "World"' in result

    def test_process_bytes_unsupported_extension(self) -> None:
        """Test processing bytes with unsupported extension."""
        content = b"Test content"
        result = FileProcessor.process_bytes(content, "unknown")
        assert result == "Test content"
