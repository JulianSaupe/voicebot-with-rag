from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MarkdownTextSection:
    """Domain model representing a text section extracted from markdown."""
    content: str
    section_number: int
    source_file: Optional[str] = None
    
    def is_empty(self) -> bool:
        """Check if the text section is empty or contains only whitespace."""
        return not self.content or self.content.strip() == ""
    
    def get_clean_content(self) -> str:
        """Get the content with leading/trailing whitespace removed."""
        return self.content.strip()
    
    def get_word_count(self) -> int:
        """Get the number of words in the text section."""
        return len(self.get_clean_content().split())


@dataclass
class MarkdownDocument:
    """Domain model representing a parsed markdown document."""
    source_file: str
    text_sections: List[MarkdownTextSection]
    
    def get_non_empty_sections(self) -> List[MarkdownTextSection]:
        """Get all non-empty text sections."""
        return [section for section in self.text_sections if not section.is_empty()]
    
    def get_total_word_count(self) -> int:
        """Get the total word count across all text sections."""
        return sum(section.get_word_count() for section in self.get_non_empty_sections())
    
    def get_section_count(self) -> int:
        """Get the number of non-empty text sections."""
        return len(self.get_non_empty_sections())