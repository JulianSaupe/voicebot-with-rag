from typing import List

from backend.internal.domain.models.markdown_document import MarkdownDocument, MarkdownTextSection
from backend.internal.ports.output.markdown_parser import MarkdownParser
from backend.internal.ports.output.vector_database import VectorDatabase


class MarkdownScraperService:
    """Application service for scraping markdown files and storing text sections in vector database."""

    def __init__(self, markdown_parser: MarkdownParser, vector_database: VectorDatabase):
        self.markdown_parser = markdown_parser
        self.vector_database = vector_database

    def scrape_and_store_file(self, file_path: str) -> MarkdownDocument:
        """
        Scrape a markdown file and store all text sections in the vector database.
        
        Args:
            file_path: Path to the markdown file to scrape
            
        Returns:
            MarkdownDocument containing the parsed text sections
            
        Raises:
            FileNotFoundError: If the markdown file is not found
            Exception: If there's an error processing the file
        """
        try:
            # Parse the markdown file
            document = self.markdown_parser.parse_file(file_path)

            # Store each non-empty text section in the vector database
            stored_count = 0
            for section in document.get_non_empty_sections():
                self.vector_database.insert_document(section.get_clean_content())
                stored_count += 1

            print(f"Successfully scraped and stored {stored_count} text sections from {file_path}")
            print(f"Total word count: {document.get_total_word_count()}")

            return document

        except FileNotFoundError:
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error scraping markdown file {file_path}: {str(e)}")

    def get_text_sections_preview(self, file_path: str, max_sections: int = 5) -> List[MarkdownTextSection]:
        """
        Get a preview of text sections from a markdown file without storing them.
        
        Args:
            file_path: Path to the markdown file
            max_sections: Maximum number of sections to return for preview
            
        Returns:
            List of MarkdownTextSection objects (up to max_sections)
        """
        try:
            document = self.markdown_parser.parse_file(file_path)
            non_empty_sections = document.get_non_empty_sections()
            return non_empty_sections[:max_sections]
        except Exception as e:
            raise Exception(f"Error getting preview from {file_path}: {str(e)}")

    def get_document_stats(self, file_path: str) -> dict:
        """
        Get statistics about a markdown document without storing it.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Dictionary containing document statistics
        """
        try:
            document = self.markdown_parser.parse_file(file_path)
            return {
                "source_file": document.source_file,
                "total_sections": len(document.text_sections),
                "non_empty_sections": document.get_section_count(),
                "total_word_count": document.get_total_word_count(),
                "average_words_per_section": (
                    document.get_total_word_count() / document.get_section_count()
                    if document.get_section_count() > 0 else 0
                )
            }
        except Exception as e:
            raise Exception(f"Error getting stats from {file_path}: {str(e)}")
