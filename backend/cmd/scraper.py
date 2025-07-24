import sys
import os

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(project_root)

from backend.internal.adapters.driven.all_mpnet_base_v2 import AllMPNetBaseV2
from backend.internal.adapters.driven.postgres_db import PostgresVectorDB
from backend.internal.adapters.driven.markdown_parser_impl import MarkdownParserImpl
from backend.internal.application.markdown_scraper_service import MarkdownScraperService


def main():
    """Main demonstration function."""
    print("=== Markdown Scraper Demonstration ===\n")

    # Path to the attached markdown file
    markdown_file_path = "/Users/julian/Library/Application Support/JetBrains/PyCharm2025.1/scratches/scratch_1.md"

    try:
        # Set up dependencies following the same pattern as the container
        print("1. Setting up dependencies...")
        embedding_calculator = AllMPNetBaseV2()
        vector_db = PostgresVectorDB(embedding_calculator)
        markdown_parser = MarkdownParserImpl()

        # Create the markdown scraper service
        scraper_service = MarkdownScraperService(markdown_parser, vector_db)
        print("   ✓ Dependencies initialized successfully\n")

        # Get document statistics first
        print("2. Analyzing markdown document...")
        stats = scraper_service.get_document_stats(markdown_file_path)
        print(f"   Source file: {stats['source_file']}")
        print(f"   Total sections found: {stats['total_sections']}")
        print(f"   Non-empty sections: {stats['non_empty_sections']}")
        print(f"   Total word count: {stats['total_word_count']}")
        print(f"   Average words per section: {stats['average_words_per_section']:.1f}\n")

        # Get a preview of text sections
        print("3. Preview of text sections (first 3):")
        preview_sections = scraper_service.get_text_sections_preview(markdown_file_path, max_sections=3)
        for i, section in enumerate(preview_sections, 1):
            content_preview = section.get_clean_content()[:200] + "..." if len(
                section.get_clean_content()) > 200 else section.get_clean_content()
            print(f"   Section {i} ({section.get_word_count()} words):")
            print(f"   {content_preview}\n")

        # Ask for confirmation before storing
        response = input("4. Do you want to proceed with storing all text sections in the vector database? (y/N): ")
        if response.lower() != 'y':
            print("   Operation cancelled by user.")
            return

        # Scrape and store the markdown file
        print("\n5. Scraping and storing text sections...")
        document = scraper_service.scrape_and_store_file(markdown_file_path)
        print("   ✓ All text sections have been stored in the vector database\n")

        # Demonstrate search functionality
        print("6. Testing search functionality...")
        test_query = "Täuschung"  # German word for "deception" from the document
        print(f"   Searching for: '{test_query}'")

        # Get embeddings for the query and search
        query_embeddings = embedding_calculator.calculate_embeddings(test_query)
        search_results = vector_db.search(query_embeddings, top_k=3)

        print(f"   Found {len(search_results)} relevant sections:")
        for i, result in enumerate(search_results, 1):
            result_preview = result[:150] + "..." if len(result) > 150 else result
            print(f"   Result {i}: {result_preview}\n")

        print("=== Demonstration completed successfully! ===")

    except FileNotFoundError:
        print(f"Error: Markdown file not found at {markdown_file_path}")
        print("Please ensure the file exists and the path is correct.")
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        print("Please check your database connection and dependencies.")


if __name__ == "__main__":
    main()
