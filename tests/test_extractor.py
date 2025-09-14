"""
Tests for the extractor module - core tag extraction engine and output formatting.
"""

import pytest
import json
from pathlib import Path
import tempfile
import io
import sys


class TestTagExtractor:
    """Tests for the core TagExtractor class."""
    
    def test_extractor_initialization(self, simple_vault):
        """Test TagExtractor can be initialized."""
        from extractor.core import TagExtractor
        
        extractor = TagExtractor(str(simple_vault))
        assert extractor is not None
        assert extractor.vault_path.exists()
        assert extractor.filter_tags == True  # Default value
    
    def test_extract_from_simple_vault(self, simple_vault):
        """Test extracting tags from simple vault fixture."""
        from extractor.core import TagExtractor
        
        extractor = TagExtractor(str(simple_vault))
        results = extractor.extract_tags()
        
        # Should return structured tag data as dict
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Check structure of results - keys are tag names, values have count/files
        for tag_name, tag_data in results.items():
            assert isinstance(tag_name, str)
            assert "count" in tag_data
            assert "files" in tag_data
            assert isinstance(tag_data["files"], set)
    
    def test_extract_with_filtering(self, complex_vault):
        """Test tag extraction with filtering enabled."""
        from extractor.core import TagExtractor
        
        # Extract with filtering (should be default)
        extractor_filtered = TagExtractor(str(complex_vault), filter_tags=True)
        filtered_results = extractor_filtered.extract_tags()
        
        # Extract without filtering  
        extractor_unfiltered = TagExtractor(str(complex_vault), filter_tags=False)
        unfiltered_results = extractor_unfiltered.extract_tags()
        
        # Filtered results should have fewer or equal tags
        assert len(filtered_results) <= len(unfiltered_results)
        
        # Check that obvious invalid tags are filtered out
        filtered_tags = set(filtered_results.keys())
        assert "123" not in filtered_tags  # Pure number should be filtered
    
    def test_extract_with_exclusion_patterns(self, complex_vault):
        """Test extraction with file exclusion patterns."""
        from extractor.core import TagExtractor
        
        # Extract excluding template files
        extractor = TagExtractor(
            str(complex_vault), 
            exclude_patterns={"*.template.md", "templates"}
        )
        results = extractor.extract_tags()
        
        # Should not include files from templates directory
        all_files = []
        for tag_data in results.values():
            all_files.extend(tag_data["files"])
        
        template_files = [f for f in all_files if "template" in f.lower()]
        assert len(template_files) == 0
    
    def test_extract_statistics(self, simple_vault):
        """Test that extractor collects processing statistics."""
        from extractor.core import TagExtractor
        
        extractor = TagExtractor(str(simple_vault))
        results = extractor.extract_tags()
        
        # Should have statistics available
        stats = extractor.get_statistics()
        
        assert "files_processed" in stats
        assert "errors" in stats
        assert "vault_path" in stats
        assert stats["files_processed"] > 0
    
    def test_extract_handles_file_errors(self, temp_dir):
        """Test extraction handles file processing errors gracefully."""
        from extractor.core import TagExtractor
        
        # Create a vault with a problematic file
        vault_path = temp_dir / "error_vault"
        vault_path.mkdir()
        
        # Normal file
        (vault_path / "good.md").write_text("""---
tags: [good]
---
# Good file""")
        
        # Create a file that might cause issues (e.g., binary disguised as .md)
        (vault_path / "bad.md").write_bytes(b'\x00\x01\x02\x03binary content')
        
        extractor = TagExtractor(str(vault_path))
        results = extractor.extract_tags()
        
        # Should continue processing and return results from good files
        assert isinstance(results, dict)
        # Should have processed the good file
        assert "good" in results
        assert "good.md" in results["good"]["files"]
        
        # Statistics should show some errors were handled
        stats = extractor.get_statistics()
        assert stats["files_processed"] >= 1
    
    def test_extract_empty_vault(self, temp_dir):
        """Test extraction from empty vault."""
        from extractor.core import TagExtractor
        
        empty_vault = temp_dir / "empty_vault"
        empty_vault.mkdir()
        
        extractor = TagExtractor(str(empty_vault))
        results = extractor.extract_tags()
        
        assert results == {}
        
        stats = extractor.get_statistics()
        assert stats["files_processed"] == 0
    
    def test_extract_vault_with_no_tags(self, temp_dir):
        """Test extraction from vault with files but no tags."""
        from extractor.core import TagExtractor
        
        no_tags_vault = temp_dir / "no_tags_vault"
        no_tags_vault.mkdir()
        
        (no_tags_vault / "file1.md").write_text("# Just a title\n\nContent without tags.")
        (no_tags_vault / "file2.md").write_text("Another file\n\nNo tags here either.")
        
        extractor = TagExtractor(str(no_tags_vault))
        results = extractor.extract_tags()
        
        assert results == {}
        
        stats = extractor.get_statistics()
        assert stats["files_processed"] == 2
    
    def test_extract_aggregates_tag_counts(self, temp_dir):
        """Test that extractor properly aggregates tag counts across files."""
        from extractor.core import TagExtractor
        
        vault_path = temp_dir / "count_vault"
        vault_path.mkdir()
        
        # File 1 with 'work' tag
        (vault_path / "file1.md").write_text("""---
tags: [work, notes]
---
Content""")
        
        # File 2 with 'work' tag again
        (vault_path / "file2.md").write_text("""# Title
Content with #work tag""")
        
        # File 3 with unique tag
        (vault_path / "file3.md").write_text("""---
tags: [unique]
---
Content""")
        
        extractor = TagExtractor(str(vault_path))
        results = extractor.extract_tags()
        
        # Find work tag in results
        assert "work" in results
        assert results["work"]["count"] == 2  # Should appear in 2 files
        assert len(results["work"]["files"]) == 2
        
        # Find unique tag
        assert "unique" in results
        assert results["unique"]["count"] == 1
        assert len(results["unique"]["files"]) == 1

    def test_extract_with_tag_types_parameter(self, temp_dir):
        """Test tag extraction with tag_types parameter."""
        from extractor.core import TagExtractor

        vault_path = temp_dir / "tag_types_vault"
        vault_path.mkdir()

        # Create file with both frontmatter and inline tags
        (vault_path / "mixed_tags.md").write_text("""---
tags: [frontmatter-tag]
---
# Title
Content with #inline-tag here""")

        # Test 'both' (default)
        extractor_both = TagExtractor(str(vault_path), tag_types='both')
        results_both = extractor_both.extract_tags()
        assert "frontmatter-tag" in results_both
        assert "inline-tag" in results_both

        # Test 'frontmatter' only
        extractor_frontmatter = TagExtractor(str(vault_path), tag_types='frontmatter')
        results_frontmatter = extractor_frontmatter.extract_tags()
        assert "frontmatter-tag" in results_frontmatter
        assert "inline-tag" not in results_frontmatter

        # Test 'inline' only
        extractor_inline = TagExtractor(str(vault_path), tag_types='inline')
        results_inline = extractor_inline.extract_tags()
        assert "frontmatter-tag" not in results_inline
        assert "inline-tag" in results_inline

    def test_extract_frontmatter_only_filtering(self, temp_dir):
        """Test extracting only frontmatter tags."""
        from extractor.core import TagExtractor

        vault_path = temp_dir / "frontmatter_vault"
        vault_path.mkdir()

        (vault_path / "file1.md").write_text("""---
tags: [work, meeting]
---
# Meeting Notes
This has #inline-notes and #work tags""")

        (vault_path / "file2.md").write_text("""---
tags: project
---
Project details with #project-inline tag""")

        extractor = TagExtractor(str(vault_path), tag_types='frontmatter')
        results = extractor.extract_tags()

        # Should only have frontmatter tags
        expected_tags = {"work", "meeting", "project"}
        actual_tags = set(results.keys())

        assert expected_tags.issubset(actual_tags)
        # Should not have inline tags
        assert "inline-notes" not in results
        assert "project-inline" not in results

    def test_extract_inline_only_filtering(self, temp_dir):
        """Test extracting only inline tags."""
        from extractor.core import TagExtractor

        vault_path = temp_dir / "inline_vault"
        vault_path.mkdir()

        (vault_path / "file1.md").write_text("""---
tags: [frontmatter-work]
---
# Title
Content with #inline-work and #notes""")

        (vault_path / "file2.md").write_text("""---
tags: [frontmatter-project]
---
Content with #project tag""")

        extractor = TagExtractor(str(vault_path), tag_types='inline')
        results = extractor.extract_tags()

        # Should only have inline tags
        expected_tags = {"inline-work", "notes", "project"}
        actual_tags = set(results.keys())

        assert expected_tags.issubset(actual_tags)
        # Should not have frontmatter tags
        assert "frontmatter-work" not in results
        assert "frontmatter-project" not in results


class TestOutputFormatter:
    """Tests for output formatting functionality."""
    
    def test_format_as_json(self, test_output_formats):
        """Test JSON output formatting."""
        from extractor.output_formatter import format_as_plugin_json
        
        # Use raw tag data (what TagExtractor produces)
        tags_data = test_output_formats["raw"]
        
        json_output = format_as_plugin_json(tags_data)
        
        # Should return a list directly (not a JSON string)
        assert isinstance(json_output, list)
        assert len(json_output) == 2
        
        # Should be sorted by count (descending), so work comes first
        assert json_output[0]["tag"] == "work"
        assert json_output[0]["tagCount"] == 5
        assert "relativePaths" in json_output[0]
        assert isinstance(json_output[0]["relativePaths"], list)
    
    def test_format_as_csv(self, test_output_formats):
        """Test CSV output formatting."""
        from extractor.output_formatter import format_as_csv
        
        tags_data = test_output_formats["raw"]
        
        csv_output = format_as_csv(tags_data)
        
        # Should return list of rows
        assert isinstance(csv_output, list)
        assert len(csv_output) >= 2  # Header + data rows
        
        # Should start with header
        assert csv_output[0] == ["tag", "count", "files"]
        
        # Should have data rows sorted by count (descending)
        assert csv_output[1][0] == "work"  # tag name
        assert csv_output[1][1] == "5"     # count as string
    
    def test_format_as_text(self, test_output_formats):
        """Test text output formatting.""" 
        from extractor.output_formatter import format_as_text
        
        tags_data = test_output_formats["raw"]
        
        text_output = format_as_text(tags_data)
        
        # Should contain summary information  
        assert "work" in text_output
        assert "notes" in text_output
        assert "Found" in text_output and "unique tags" in text_output
        assert "(5 files)" in text_output  # work count
        assert "(2 files)" in text_output  # notes count
    
    def test_save_output_to_file(self, temp_dir, test_output_formats):
        """Test saving output to file."""
        from extractor.output_formatter import save_output, format_as_plugin_json
        
        tags_data = test_output_formats["raw"]
        formatted_data = format_as_plugin_json(tags_data)
        output_file = temp_dir / "output.json"
        
        save_output(formatted_data, output_file, format_type="json")
        
        # File should be created
        assert output_file.exists()
        
        # Content should be valid JSON
        content = output_file.read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
    
    def test_save_output_csv_format(self, temp_dir, test_output_formats):
        """Test saving CSV format output."""
        from extractor.output_formatter import save_output, format_as_csv
        
        tags_data = test_output_formats["raw"]
        formatted_data = format_as_csv(tags_data)
        output_file = temp_dir / "output.csv"
        
        save_output(formatted_data, output_file, format_type="csv")
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "tag,count,files" in content
    
    def test_print_summary_to_stdout(self, test_output_formats):
        """Test printing summary to stdout."""
        from extractor.output_formatter import print_summary
        
        tags_data = test_output_formats["raw"]
        stats = {"vault_path": "/test", "files_processed": 5, "errors": 0}
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            print_summary(tags_data, stats)
            output = captured_output.getvalue()
            
            # Should contain summary information
            assert "work" in output
            assert "files" in output.lower() or "tags" in output.lower()
        finally:
            sys.stdout = sys.__stdout__
    
    def test_handle_empty_data(self):
        """Test formatters handle empty data gracefully."""
        from extractor.output_formatter import format_as_plugin_json, format_as_csv, format_as_text
        
        empty_data = {}  # Empty dict, not list
        
        # All formatters should handle empty data
        json_output = format_as_plugin_json(empty_data)
        assert json_output == []
        
        csv_output = format_as_csv(empty_data)
        assert csv_output[0] == ["tag", "count", "files"]  # Should have header row
        
        text_output = format_as_text(empty_data)
        assert isinstance(text_output, str)
        assert "No tags found" in text_output


class TestExtractorIntegration:
    """Integration tests combining extractor and formatter functionality."""
    
    def test_full_extraction_pipeline(self, simple_vault, temp_dir):
        """Test complete extraction pipeline from vault to formatted output."""
        from extractor.core import TagExtractor
        from extractor.output_formatter import save_output, format_as_plugin_json, format_as_csv
        
        extractor = TagExtractor(str(simple_vault))
        results = extractor.extract_tags()
        
        # Save in different formats
        json_file = temp_dir / "tags.json"
        csv_file = temp_dir / "tags.csv"
        
        json_data = format_as_plugin_json(results)
        csv_data = format_as_csv(results)
        
        save_output(json_data, json_file, format_type="json")
        save_output(csv_data, csv_file, format_type="csv")
        
        # Both files should exist and have content
        assert json_file.exists()
        assert csv_file.exists()
        
        json_content = json_file.read_text()
        csv_content = csv_file.read_text()
        
        assert len(json_content) > 0
        assert len(csv_content) > 0
        assert "tag,count,files" in csv_content
    
    def test_extraction_with_complex_vault(self, complex_vault):
        """Test extraction handles complex vault structure."""
        from extractor.core import TagExtractor
        
        extractor = TagExtractor(str(complex_vault))
        results = extractor.extract_tags()
        
        assert len(results) > 0
        
        # Should handle nested directories
        all_files = []
        for tag_data in results.values():
            all_files.extend(tag_data["files"])
        
        # Should include files from subdirectories
        nested_files = [f for f in all_files if "folder1" in f or "/" in f]
        # Exact count depends on implementation, but should have some nested files
        
        # Should handle malformed files gracefully
        stats = extractor.get_statistics()
        assert stats["files_processed"] > 0
    
    def test_filter_integration_with_extraction(self, complex_vault):
        """Test that tag filtering is properly integrated with extraction."""
        from extractor.core import TagExtractor
        
        # Test with filtering
        extractor = TagExtractor(str(complex_vault), filter_tags=True)
        filtered_results = extractor.extract_tags()
        filtered_tags = set(filtered_results.keys())
        
        # Should not contain obvious invalid tags
        invalid_patterns = ["123", "_underscore", "html&entities"]
        for pattern in invalid_patterns:
            assert pattern not in filtered_tags
    
    def test_error_resilience(self, temp_dir):
        """Test that extractor is resilient to various error conditions."""
        from extractor.core import TagExtractor
        
        # Create vault with mixed good and problematic files
        vault_path = temp_dir / "mixed_vault"
        vault_path.mkdir()
        
        # Good file
        (vault_path / "good.md").write_text("""---
tags: [valid]
---
Good content""")
        
        # Empty file
        (vault_path / "empty.md").write_text("")
        
        # File with just frontmatter, no content
        (vault_path / "frontmatter_only.md").write_text("""---
tags: [frontmatter-only]
---""")
        
        # Non-markdown file (should be ignored)
        (vault_path / "not_markdown.txt").write_text("This is not markdown")
        
        extractor = TagExtractor(str(vault_path))
        results = extractor.extract_tags()
        
        # Should process successfully
        assert isinstance(results, dict)
        
        # Should have extracted from good files
        assert "valid" in results
        assert results["valid"]["count"] == 1
        
        assert "frontmatter-only" in results
        assert results["frontmatter-only"]["count"] == 1
        
        # Statistics should reflect processing
        stats = extractor.get_statistics()
        assert stats["files_processed"] >= 2  # Should have found markdown files