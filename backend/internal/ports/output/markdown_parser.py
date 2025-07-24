from abc import ABC, abstractmethod
from typing import List

from backend.internal.domain.models.markdown_document import MarkdownDocument, MarkdownTextSection


class MarkdownParser(ABC):
    """Output port for parsing markdown files and extracting text sections."""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> MarkdownDocument:
        """
        Parse a markdown file and extract text sections, ignoring headlines.
        
        Args:
            file_path: Path to the markdown file to parse
            
        Returns:
            MarkdownDocument containing extracted text sections
        """
        pass
    
    @abstractmethod
    def parse_content(self, content: str, source_file: str = "unknown") -> MarkdownDocument:
        """
        Parse markdown content and extract text sections, ignoring headlines.
        
        Args:
            content: Markdown content as string
            source_file: Optional source file name for reference
            
        Returns:
            MarkdownDocument containing extracted text sections
        """
        pass
    
    @abstractmethod
    def extract_text_sections(self, content: str) -> List[str]:
        """
        Extract only the text sections from markdown content, ignoring headlines.
        
        Args:
            content: Markdown content as string
            
        Returns:
            List of text sections as strings
        """
        pass