"""Additional tests for file processor formats."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pptx
import PyPDF2
from docx import Document

from app.core.file_processor import FileProcessor


class TestFileProcessorPDF:
    """Tests for PDF file processing."""

    def test_read_pdf_simple(self) -> None:
        """Test reading a simple PDF file."""
        # Create a simple PDF in memory
        pdf_writer = PyPDF2.PdfWriter()
        pdf_writer.add_blank_page(width=200, height=200)

        # Add text to the page
        output = io.BytesIO()
        pdf_writer.write(output)
        pdf_content = output.getvalue()

        # Should not raise an error
        result = FileProcessor.read_pdf(pdf_content)
        assert isinstance(result, str)

    def test_read_pdf_empty(self) -> None:
        """Test reading an empty PDF."""
        pdf_writer = PyPDF2.PdfWriter()
        pdf_writer.add_blank_page(width=200, height=200)

        output = io.BytesIO()
        pdf_writer.write(output)
        pdf_content = output.getvalue()

        result = FileProcessor.read_pdf(pdf_content)
        assert isinstance(result, str)

    def test_read_pdf_invalid(self) -> None:
        """Test reading invalid PDF content."""
        invalid_content = b"Not a PDF file"
        try:
            FileProcessor.read_pdf(invalid_content)
        except ValueError as e:
            assert "PDF reading error" in str(e)


class TestFileProcessorDOCX:
    """Tests for DOCX file processing."""

    def test_read_docx_simple(self) -> None:
        """Test reading a simple DOCX file."""
        # Create a simple DOCX in memory
        doc = Document()
        doc.add_paragraph("Hello, world!")
        doc.add_paragraph("This is a test document.")

        output = io.BytesIO()
        doc.save(output)
        docx_content = output.getvalue()

        result = FileProcessor.read_docx(docx_content)
        assert "Hello, world!" in result
        assert "This is a test document." in result

    def test_read_docx_empty(self) -> None:
        """Test reading an empty DOCX file."""
        doc = Document()
        output = io.BytesIO()
        doc.save(output)
        docx_content = output.getvalue()

        result = FileProcessor.read_docx(docx_content)
        assert isinstance(result, str)

    def test_read_docx_multiple_paragraphs(self) -> None:
        """Test reading DOCX with multiple paragraphs."""
        doc = Document()
        for i in range(5):
            doc.add_paragraph(f"Paragraph {i}")

        output = io.BytesIO()
        doc.save(output)
        docx_content = output.getvalue()

        result = FileProcessor.read_docx(docx_content)
        for i in range(5):
            assert f"Paragraph {i}" in result

    def test_read_docx_invalid(self) -> None:
        """Test reading invalid DOCX content."""
        invalid_content = b"Not a DOCX file"
        try:
            FileProcessor.read_docx(invalid_content)
        except ValueError as e:
            assert "DOCX reading error" in str(e)


class TestFileProcessorPPTX:
    """Tests for PPTX file processing."""

    def test_read_pptx_simple(self) -> None:
        """Test reading a simple PPTX file."""
        # Create a simple PPTX in memory
        presentation = pptx.Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[0])
        title = slide.shapes.title
        title.text = "Test Presentation"

        output = io.BytesIO()
        presentation.save(output)
        pptx_content = output.getvalue()

        result = FileProcessor.read_pptx(pptx_content)
        assert "Test Presentation" in result

    def test_read_pptx_multiple_slides(self) -> None:
        """Test reading PPTX with multiple slides."""
        presentation = pptx.Presentation()

        for i in range(3):
            slide = presentation.slides.add_slide(presentation.slide_layouts[0])
            title = slide.shapes.title
            title.text = f"Slide {i}"

        output = io.BytesIO()
        presentation.save(output)
        pptx_content = output.getvalue()

        result = FileProcessor.read_pptx(pptx_content)
        for i in range(3):
            assert f"Slide {i}" in result

    def test_read_pptx_empty(self) -> None:
        """Test reading an empty PPTX file."""
        presentation = pptx.Presentation()
        output = io.BytesIO()
        presentation.save(output)
        pptx_content = output.getvalue()

        result = FileProcessor.read_pptx(pptx_content)
        assert isinstance(result, str)

    def test_read_pptx_invalid(self) -> None:
        """Test reading invalid PPTX content."""
        invalid_content = b"Not a PPTX file"
        try:
            FileProcessor.read_pptx(invalid_content)
        except ValueError as e:
            assert "PPTX reading error" in str(e)


class TestFileProcessorXLSX:
    """Tests for XLSX file processing."""

    def test_read_xlsx_simple(self) -> None:
        """Test reading a simple XLSX file."""
        # Create a simple XLSX in memory
        df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})

        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Sheet1", engine="openpyxl")
        xlsx_content = output.getvalue()

        result = FileProcessor.read_xlsx(xlsx_content)
        assert "1" in result or "x" in result

    def test_read_xlsx_multiple_sheets(self) -> None:
        """Test reading XLSX with multiple sheets."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df1 = pd.DataFrame({"A": [1, 2]})
            df2 = pd.DataFrame({"B": [3, 4]})
            df1.to_excel(writer, sheet_name="Sheet1", index=False)
            df2.to_excel(writer, sheet_name="Sheet2", index=False)

        xlsx_content = output.getvalue()
        result = FileProcessor.read_xlsx(xlsx_content)
        assert "Sheet1" in result
        assert "Sheet2" in result

    def test_read_xlsx_empty(self) -> None:
        """Test reading an empty XLSX file."""
        df = pd.DataFrame()
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        xlsx_content = output.getvalue()

        result = FileProcessor.read_xlsx(xlsx_content)
        assert isinstance(result, str)

    def test_read_xlsx_invalid(self) -> None:
        """Test reading invalid XLSX content."""
        invalid_content = b"Not an XLSX file"
        try:
            FileProcessor.read_xlsx(invalid_content)
        except ValueError as e:
            assert "XLSX reading error" in str(e)


class TestFileProcessorCSV:
    """Tests for CSV file processing."""

    def test_read_csv_simple(self) -> None:
        """Test reading a simple CSV file."""
        csv_content = b"Name,Age\nAlice,30\nBob,25"
        result = FileProcessor.read_csv(csv_content)
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result
        assert "25" in result

    def test_read_csv_with_encoding(self) -> None:
        """Test reading CSV with specific encoding."""
        csv_content = "Имя,Возраст\nАлиса,30\nБоб,25".encode()
        result = FileProcessor.read_csv(csv_content)
        assert "Алиса" in result or "30" in result

    def test_read_csv_empty(self) -> None:
        """Test reading an empty CSV file."""
        csv_content = b""
        try:
            result = FileProcessor.read_csv(csv_content)
            # May succeed with empty string or raise error
            assert isinstance(result, str)
        except ValueError:
            # Empty CSV may cause error
            pass

    def test_read_csv_invalid(self) -> None:
        """Test reading invalid CSV content."""
        invalid_content = b"\x00\x01\x02\x03"  # Binary garbage
        try:
            FileProcessor.read_csv(invalid_content)
        except ValueError as e:
            assert "CSV reading error" in str(e)


class TestFileProcessorIntegration:
    """Integration tests for file processor."""

    def test_process_file_auto_detect(self, temp_dir: Path) -> None:
        """Test processing file with automatic format detection."""
        # Create a test file
        file_path = temp_dir / "test.txt"
        file_path.write_text("Hello, world!", encoding="utf-8")

        result = FileProcessor.process_file(file_path)
        assert result == "Hello, world!"

    def test_process_bytes_auto_detect(self) -> None:
        """Test processing bytes with format specification."""
        content = b"Test content"
        result = FileProcessor.process_bytes(content, "txt")
        assert result == "Test content"

    def test_process_bytes_rpy(self) -> None:
        """Test processing RPY bytes with options."""
        content = b'e "Hello"\nmc "World"'
        result = FileProcessor.process_bytes(
            content, "rpy", translate_dialogue=True, translate_strings=False
        )
        assert "Hello" in result

    def test_process_file_unsupported_extension(self, temp_dir: Path) -> None:
        """Test processing file with unsupported extension."""
        file_path = temp_dir / "test.unknown"
        file_path.write_text("Some content", encoding="utf-8")

        # Should fall back to text reading
        result = FileProcessor.process_file(file_path)
        assert result == "Some content"

    def test_supported_extensions_complete(self) -> None:
        """Test that all expected extensions are supported."""
        expected = {
            "txt",
            "pdf",
            "docx",
            "doc",
            "pptx",
            "xlsx",
            "xls",
            "csv",
            "html",
            "htm",
            "md",
            "markdown",
            "rpy",
        }
        assert expected == FileProcessor.SUPPORTED_EXTENSIONS
