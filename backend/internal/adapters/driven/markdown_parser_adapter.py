import re
from typing import List

from backend.internal.domain.models.markdown_document import MarkdownDocument, MarkdownTextSection
from backend.internal.ports.output.markdown_parser import MarkdownParser


class MarkdownParserAdapter(MarkdownParser):
    """Implementation of markdown parser that extracts text sections while ignoring headlines."""

    def parse_file(self, file_path: str) -> MarkdownDocument:
        """Parse a markdown file and extract text sections, ignoring headlines."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return self.parse_content(content, file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading markdown file {file_path}: {str(e)}")

    def parse_content(self, content: str, source_file: str = "unknown") -> MarkdownDocument:
        """Parse markdown content and extract text sections, ignoring headlines."""
        text_sections_content = self.extract_text_sections(content)

        text_sections = []
        for i, section_content in enumerate(text_sections_content):
            section = MarkdownTextSection(
                content=section_content,
                section_number=i + 1,
                source_file=source_file
            )
            text_sections.append(section)

        return MarkdownDocument(
            source_file=source_file,
            text_sections=text_sections
        )

    def extract_text_sections(self, content: str) -> List[str]:
        """Extract only the text sections from markdown content, ignoring headlines."""
        # Split content into lines
        lines = content.split('\n')

        text_sections = []
        current_section = []

        for line in lines:
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                # If we have accumulated text, add it as a section
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text:  # Only add non-empty sections
                        text_sections.append(section_text)
                    current_section = []
                continue

            # Check if line is a headline (starts with #)
            if self._is_headline(stripped_line):
                # If we have accumulated text, add it as a section before the headline
                if current_section:
                    section_text = '\n'.join(current_section).strip()
                    if section_text:  # Only add non-empty sections
                        text_sections.append(section_text)
                    current_section = []
                # Skip the headline itself
                continue

            # Check if line is a special markdown element to skip
            if self._should_skip_line(stripped_line):
                continue

            # This is regular text content, add to current section
            current_section.append(line)

        # Add any remaining text as the last section
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:  # Only add non-empty sections
                text_sections.append(section_text)

        return text_sections

    def _is_headline(self, line: str) -> bool:
        """Check if a line is a markdown headline."""
        # Headlines start with one or more # characters followed by a space
        return re.match(r'^#{1,6}\s+', line) is not None

    def _should_skip_line(self, line: str) -> bool:
        """Check if a line should be skipped (special markdown elements)."""
        # Skip lines that are:
        # - Image references: ![alt](url)
        # - Link-only lines: [text](url)
        # - HTML comments: <!-- -->
        # - Horizontal rules: --- or ***
        # - Code block markers: ```
        # - Table separators: |---|---|

        # Image references
        if re.match(r'^\!\[.*\]\(.*\)$', line):
            return True

        # Standalone links (entire line is just a link)
        if re.match(r'^\[.*\]\(.*\)$', line):
            return True

        # HTML comments
        if re.match(r'^<!--.*-->$', line):
            return True

        # Horizontal rules
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', line):
            return True

        # Code block markers
        if re.match(r'^```', line):
            return True

        # Table separators
        if re.match(r'^\|.*\|$', line) and '-' in line:
            return True

        return False
