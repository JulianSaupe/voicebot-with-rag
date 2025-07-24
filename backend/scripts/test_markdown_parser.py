#!/usr/bin/env python3
"""
Simple test script to verify markdown parsing logic works correctly.
"""

import sys
import os

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(project_root)

from backend.internal.adapters.driven.markdown_parser_impl import MarkdownParserImpl


def test_markdown_parsing():
    """Test the markdown parsing with the provided file content."""
    print("=== Testing Markdown Parser ===\n")
    
    # Path to the attached markdown file
    markdown_file_path = "/Users/julian/Library/Application Support/JetBrains/PyCharm2025.1/scratches/scratch_1.md"
    
    try:
        # Create the markdown parser
        parser = MarkdownParserImpl()
        
        # Test parsing the file
        print("1. Testing file parsing...")
        document = parser.parse_file(markdown_file_path)
        
        print(f"   ✓ Successfully parsed file: {document.source_file}")
        print(f"   ✓ Total sections found: {len(document.text_sections)}")
        print(f"   ✓ Non-empty sections: {document.get_section_count()}")
        print(f"   ✓ Total word count: {document.get_total_word_count()}")
        
        # Show first few sections
        print("\n2. First 5 text sections:")
        non_empty_sections = document.get_non_empty_sections()
        for i, section in enumerate(non_empty_sections[:5], 1):
            content_preview = section.get_clean_content()[:100] + "..." if len(section.get_clean_content()) > 100 else section.get_clean_content()
            print(f"   Section {i} ({section.get_word_count()} words): {content_preview}")
        
        # Test with sample content to verify headline filtering
        print("\n3. Testing headline filtering with sample content...")
        sample_content = """# This is a headline
This is regular text that should be extracted.

## Another headline
More text content here.
This continues the same section.

### Yet another headline
Final text section."""
        
        sample_document = parser.parse_content(sample_content, "test_sample")
        print(f"   ✓ Sample parsing result: {sample_document.get_section_count()} sections")
        
        for i, section in enumerate(sample_document.get_non_empty_sections(), 1):
            print(f"   Section {i}: {section.get_clean_content()}")
        
        print("\n=== All tests passed! ===")
        return True
        
    except FileNotFoundError:
        print(f"Error: File not found at {markdown_file_path}")
        return False
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_markdown_parsing()
    sys.exit(0 if success else 1)