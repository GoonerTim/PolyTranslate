"""File processor for reading various document formats."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import chardet
import pandas as pd
import pptx
import PyPDF2
from bs4 import BeautifulSoup
from docx import Document
from markdown import markdown

if TYPE_CHECKING:
    pass


class FileProcessor:
    """Handles reading and processing of various file formats."""

    SUPPORTED_EXTENSIONS = {
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

    @staticmethod
    def detect_encoding(file_content: bytes) -> str:
        """Detect the encoding of file content."""
        try:
            result = chardet.detect(file_content)
            detected = result.get("encoding")
            confidence = result.get("confidence", 0)

            # If confidence is low, try common encodings
            if not detected or confidence < 0.7:
                # Try UTF-8 first (most common)
                try:
                    file_content.decode("utf-8")
                    return "utf-8"
                except UnicodeDecodeError:
                    pass

                # Try UTF-8 with BOM
                if file_content.startswith(b"\xef\xbb\xbf"):
                    return "utf-8-sig"

                # Try common Windows encodings
                for enc in ["cp1251", "cp1252", "windows-1251", "windows-1252"]:
                    try:
                        file_content.decode(enc)
                        return enc
                    except (UnicodeDecodeError, LookupError):
                        continue

            return detected or "utf-8"
        except Exception:
            return "utf-8"

    @staticmethod
    def read_txt(file_content: bytes) -> str:
        """Read a text file."""
        # Try multiple encodings with priority
        encodings = [
            FileProcessor.detect_encoding(file_content),
            "utf-8",
            "utf-8-sig",
            "cp1251",
            "windows-1251",
            "cp1252",
            "windows-1252",
            "latin-1",
        ]

        for encoding in encodings:
            try:
                decoded = file_content.decode(encoding)
                # Check if decoded text looks reasonable (no excessive mojibake)
                if not all(ord(char) > 127 and ord(char) < 160 for char in decoded[:100]):
                    return decoded
            except (UnicodeDecodeError, LookupError, AttributeError):
                continue

        # Last resort: UTF-8 with error replacement
        return file_content.decode("utf-8", errors="replace")

    @staticmethod
    def read_pdf(file_content: bytes) -> str:
        """Read a PDF file."""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            raise ValueError(f"PDF reading error: {e}") from e

    @staticmethod
    def read_docx(file_content: bytes) -> str:
        """Read a DOCX file."""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"DOCX reading error: {e}") from e

    @staticmethod
    def read_pptx(file_content: bytes) -> str:
        """Read a PPTX file."""
        try:
            pptx_file = io.BytesIO(file_content)
            presentation = pptx.Presentation(pptx_file)
            text = ""
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"PPTX reading error: {e}") from e

    @staticmethod
    def read_xlsx(file_content: bytes) -> str:
        """Read an XLSX file."""
        try:
            xlsx_file = io.BytesIO(file_content)
            df = pd.read_excel(xlsx_file, sheet_name=None)
            text = ""
            for sheet_name, sheet_data in df.items():
                text += f"--- {sheet_name} ---\n"
                for _, row in sheet_data.iterrows():
                    row_text = " | ".join(str(cell) for cell in row if pd.notna(cell))
                    text += row_text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"XLSX reading error: {e}") from e

    @staticmethod
    def read_csv(file_content: bytes) -> str:
        """Read a CSV file."""
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            csv_file = io.BytesIO(file_content)
            df = pd.read_csv(csv_file, encoding=encoding)
            text = ""
            for _, row in df.iterrows():
                row_text = " | ".join(str(cell) for cell in row if pd.notna(cell))
                text += row_text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"CSV reading error: {e}") from e

    @staticmethod
    def read_html(file_content: bytes) -> str:
        """Read an HTML file."""
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            html_content = file_content.decode(encoding)
            soup = BeautifulSoup(html_content, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            raise ValueError(f"HTML reading error: {e}") from e

    @staticmethod
    def read_md(file_content: bytes) -> str:
        """Read a Markdown file."""
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            md_content = file_content.decode(encoding)
            html_content = markdown(md_content)
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text()
            return text
        except Exception as e:
            raise ValueError(f"Markdown reading error: {e}") from e

    @staticmethod
    def read_rpy(
        file_content: bytes,
        translate_dialogue: bool = True,
        translate_strings: bool = True,
        preserve_code: bool = True,
    ) -> str:
        """Read and parse Ren'Py .rpy files."""
        try:
            encoding = FileProcessor.detect_encoding(file_content)
            rpy_content = file_content.decode(encoding)

            patterns = {
                "dialogue": r'^\s*[^#\n]*["\'](.*?)["\']',
                "old_dialogue": r'^\s*[^#\n]*["\']{3}(.*?)["\']{3}',
                "string_translations": r'^\s*_\(["\'](.*?)["\']\)',
                "character_dialogue": r'^\s*(\w+)\s*["\'](.*?)["\']',
                "menu_options": r'^\s*["\'](.*?)["\']:',
            }

            extracted_text: list[str] = []
            lines = rpy_content.split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.rstrip()

                if line.strip().startswith("#"):
                    continue

                if translate_dialogue:
                    dialogue_matches = re.findall(patterns["dialogue"], line)
                    for match in dialogue_matches:
                        if match.strip() and len(match.strip()) > 1:
                            extracted_text.append(f"DIALOGUE_LINE_{line_num}: {match}")

                    old_dialogue_matches = re.findall(patterns["old_dialogue"], line, re.DOTALL)
                    for match in old_dialogue_matches:
                        if match.strip():
                            extracted_text.append(f"DIALOGUE_LINE_{line_num}: {match}")

                if translate_strings:
                    string_matches = re.findall(patterns["string_translations"], line)
                    for match in string_matches:
                        if match.strip():
                            extracted_text.append(f"TRANSLATABLE_STRING_{line_num}: {match}")

                if translate_dialogue:
                    char_matches = re.findall(patterns["character_dialogue"], line)
                    for char, dialogue in char_matches:
                        if dialogue.strip():
                            extracted_text.append(
                                f"CHARACTER_DIALOGUE_{line_num}_{char}: {dialogue}"
                            )

                    menu_matches = re.findall(patterns["menu_options"], line)
                    for match in menu_matches:
                        if match.strip():
                            extracted_text.append(f"MENU_OPTION_{line_num}: {match}")

            if not extracted_text:
                return rpy_content

            return "\n".join(extracted_text)

        except Exception as e:
            raise ValueError(f"RPY reading error: {e}") from e

    @staticmethod
    def reconstruct_rpy(
        original_content: str,
        translations: dict[str, str],
        translate_dialogue: bool = True,
        translate_strings: bool = True,
    ) -> str:
        """Reconstruct a .rpy file with translated text."""
        try:
            lines = original_content.split("\n")
            translated_lines: list[str] = []

            for line_num, line in enumerate(lines, 1):
                current_line = line

                if translate_dialogue:
                    dialogue_pattern = r'^(\s*[^#\n]*)(["\'])(.*?)(["\'])'

                    def replace_dialogue(match: re.Match[str], num: int = line_num) -> str:
                        prefix = match.group(1)
                        start_quote = match.group(2)
                        content = match.group(3)
                        end_quote = match.group(4)

                        key = f"DIALOGUE_LINE_{num}: {content}"
                        if key in translations:
                            return f"{prefix}{start_quote}{translations[key]}{end_quote}"
                        return match.group(0)

                    current_line = re.sub(dialogue_pattern, replace_dialogue, current_line)

                if translate_strings:
                    string_pattern = r'^(\s*_\()(["\'])(.*?)(["\']\))'

                    def replace_string(match: re.Match[str], num: int = line_num) -> str:
                        prefix = match.group(1)
                        start_quote = match.group(2)
                        content = match.group(3)
                        end_quote = match.group(4)

                        key = f"TRANSLATABLE_STRING_{num}: {content}"
                        if key in translations:
                            return f"{prefix}{start_quote}{translations[key]}{end_quote})"
                        return match.group(0)

                    current_line = re.sub(string_pattern, replace_string, current_line)

                translated_lines.append(current_line)

            return "\n".join(translated_lines)

        except Exception as e:
            raise ValueError(f"RPY reconstruction error: {e}") from e

    @classmethod
    def process_file(cls, file_path: str | Path, **kwargs: Any) -> str:
        """Process a file and extract text based on its extension."""
        path = Path(file_path)
        extension = path.suffix.lower().lstrip(".")

        if extension not in cls.SUPPORTED_EXTENSIONS:
            # Try to read as text
            try:
                content = path.read_bytes()
                return cls.read_txt(content)
            except Exception as e:
                raise ValueError(f"Unsupported file format: {extension}") from e

        content = path.read_bytes()

        processors: dict[str, Any] = {
            "txt": cls.read_txt,
            "pdf": cls.read_pdf,
            "docx": cls.read_docx,
            "doc": cls.read_docx,
            "pptx": cls.read_pptx,
            "xlsx": cls.read_xlsx,
            "xls": cls.read_xlsx,
            "csv": cls.read_csv,
            "html": cls.read_html,
            "htm": cls.read_html,
            "md": cls.read_md,
            "markdown": cls.read_md,
            "rpy": cls.read_rpy,
        }

        processor = processors.get(extension)
        if processor is None:
            return cls.read_txt(content)

        if extension == "rpy":
            return processor(content, **kwargs)
        return processor(content)

    @classmethod
    def process_bytes(cls, file_content: bytes, extension: str, **kwargs: Any) -> str:
        """Process file content bytes and extract text."""
        extension = extension.lower().lstrip(".")

        processors: dict[str, Any] = {
            "txt": cls.read_txt,
            "pdf": cls.read_pdf,
            "docx": cls.read_docx,
            "doc": cls.read_docx,
            "pptx": cls.read_pptx,
            "xlsx": cls.read_xlsx,
            "xls": cls.read_xlsx,
            "csv": cls.read_csv,
            "html": cls.read_html,
            "htm": cls.read_html,
            "md": cls.read_md,
            "markdown": cls.read_md,
            "rpy": cls.read_rpy,
        }

        processor = processors.get(extension, cls.read_txt)
        if extension == "rpy":
            return processor(file_content, **kwargs)
        return processor(file_content)
