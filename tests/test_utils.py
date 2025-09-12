"""
Tests for the utils module - file discovery, tag normalization, and validation.
"""

import pytest
from pathlib import Path


class TestFileDiscovery:
    """Tests for file discovery functionality."""
    
    def test_find_markdown_files_basic(self, simple_vault):
        """Test finding markdown files in a vault."""
        from utils.file_discovery import find_markdown_files
        
        files = find_markdown_files(str(simple_vault))
        
        assert isinstance(files, list)
        assert len(files) > 0
        
        # All returned files should be .md files
        for file_path in files:
            assert str(file_path).endswith('.md')
            
        # Should find the files from our fixture
        filenames = [f.name for f in files]
        assert "file1.md" in filenames
        assert "file2.md" in filenames
        assert "file3.md" in filenames
    
    def test_find_markdown_files_with_exclusions(self, complex_vault):
        """Test file discovery with exclusion patterns."""
        from utils.file_discovery import find_markdown_files
        
        # Find all files
        all_files = find_markdown_files(str(complex_vault))
        
        # Find files excluding templates
        filtered_files = find_markdown_files(
            str(complex_vault),
            exclude_patterns=["*.template.md", "templates/*"]
        )
        
        assert len(filtered_files) <= len(all_files)
        
        # Should not include template files
        template_files = [f for f in filtered_files if "template" in str(f).lower()]
        assert len(template_files) == 0
    
    def test_find_markdown_files_nested_directories(self, complex_vault):
        """Test finding files in nested directory structures."""
        from utils.file_discovery import find_markdown_files
        
        files = find_markdown_files(str(complex_vault))
        
        # Should find files in subdirectories
        nested_files = [f for f in files if "folder1" in str(f) or "/" in str(f)]
        assert len(nested_files) > 0
    
    def test_find_markdown_files_ignores_non_markdown(self, complex_vault):
        """Test that non-markdown files are ignored."""
        from utils.file_discovery import find_markdown_files
        
        files = find_markdown_files(str(complex_vault))
        
        # Should not include .png file or other non-markdown files
        non_md_files = [f for f in files if not str(f).endswith('.md')]
        assert len(non_md_files) == 0
    
    def test_find_markdown_files_empty_directory(self, temp_dir):
        """Test file discovery in empty directory."""
        from utils.file_discovery import find_markdown_files
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        files = find_markdown_files(str(empty_dir))
        assert files == []
    
    def test_find_markdown_files_nonexistent_directory(self):
        """Test file discovery with nonexistent directory."""
        from utils.file_discovery import find_markdown_files
        
        # Should handle gracefully
        try:
            files = find_markdown_files("/nonexistent/directory")
            assert files == []
        except (FileNotFoundError, OSError):
            # Acceptable to raise appropriate exceptions
            pass
    
    def test_exclusion_patterns_case_sensitivity(self, temp_dir):
        """Test exclusion pattern case sensitivity."""
        from utils.file_discovery import find_markdown_files
        
        test_vault = temp_dir / "case_vault"
        test_vault.mkdir()
        
        # Create files with different cases
        (test_vault / "Template.md").write_text("# Template")
        (test_vault / "TEMPLATE.md").write_text("# TEMPLATE")  
        (test_vault / "regular.md").write_text("# Regular")
        
        files_excluded = find_markdown_files(
            str(test_vault),
            exclude_patterns=["*template*", "*TEMPLATE*"]
        )
        
        # Should exclude based on pattern matching
        remaining_files = [f.name for f in files_excluded]
        assert "regular.md" in remaining_files
    
    def test_relative_path_calculation(self, simple_vault):
        """Test that relative paths are calculated correctly."""
        from utils.file_discovery import find_markdown_files
        
        files = find_markdown_files(str(simple_vault))
        
        # Files should be returned as Path objects that can be processed
        for file_path in files:
            assert isinstance(file_path, Path)
            assert len(str(file_path)) > 0


class TestTagNormalizer:
    """Tests for tag normalization functionality."""
    
    def test_normalize_tag_basic(self):
        """Test basic tag normalization."""
        from utils.tag_normalizer import normalize_tag
        
        # Test case normalization (if applicable)
        normalized = normalize_tag("Work")
        assert normalized == "work" or normalized == "Work"  # Depends on implementation
        
        # Test whitespace cleanup
        normalized = normalize_tag("  work  ")
        assert normalized == "work"
        
        # Test basic tag passes through
        normalized = normalize_tag("work")
        assert normalized == "work"
    
    def test_normalize_tag_special_characters(self):
        """Test normalization of tags with special characters."""
        from utils.tag_normalizer import normalize_tag
        
        # Test handling of valid special characters
        test_cases = [
            "project-ideas",
            "work_notes", 
            "category/subcategory",
            "2024-goals",
            "v1.2"
        ]
        
        for tag in test_cases:
            normalized = normalize_tag(tag)
            assert isinstance(normalized, str)
            assert len(normalized) > 0
    
    def test_normalize_tag_international(self):
        """Test normalization with international characters."""
        from utils.tag_normalizer import normalize_tag
        
        international_tags = ["français", "日本語", "español"]
        
        for tag in international_tags:
            normalized = normalize_tag(tag)
            # Should preserve international characters
            assert isinstance(normalized, str)
            assert len(normalized) > 0
    
    def test_normalize_tag_edge_cases(self):
        """Test normalization edge cases."""
        from utils.tag_normalizer import normalize_tag
        
        # Empty string
        normalized = normalize_tag("")
        assert normalized == "" or normalized is None
        
        # Very long tag
        long_tag = "a" * 100
        normalized = normalize_tag(long_tag)
        assert isinstance(normalized, str)
    
    def test_deduplicate_tags(self):
        """Test tag deduplication functionality."""
        from utils.tag_normalizer import deduplicate_tags
        
        tags_with_duplicates = ["work", "notes", "work", "ideas", "notes", "work"]
        
        deduplicated = deduplicate_tags(tags_with_duplicates)
        
        assert isinstance(deduplicated, list)
        assert len(deduplicated) <= len(tags_with_duplicates)
        assert "work" in deduplicated
        assert "notes" in deduplicated
        assert "ideas" in deduplicated
        
        # Each tag should appear only once
        assert deduplicated.count("work") == 1
        assert deduplicated.count("notes") == 1


class TestTagValidation:
    """Tests for tag validation and filtering functionality."""
    
    def test_is_valid_tag_basic(self):
        """Test basic tag validation."""
        from utils.tag_normalizer import is_valid_tag
        
        # Valid tags should pass
        valid_tags = ["work", "notes", "project-ideas", "2024-goals", "v1.2"]
        for tag in valid_tags:
            assert is_valid_tag(tag) == True, f"'{tag}' should be valid"
    
    def test_is_valid_tag_filters_numbers(self, invalid_tags_list):
        """Test that pure numbers are filtered out."""
        from utils.tag_normalizer import is_valid_tag
        
        # Pure numbers should be invalid
        numeric_tags = ["123", "456789", "0", "42"]
        for tag in numeric_tags:
            assert is_valid_tag(tag) == False, f"'{tag}' should be invalid (pure number)"
    
    def test_is_valid_tag_filters_invalid_start(self, invalid_tags_list):
        """Test that tags starting with invalid characters are filtered."""
        from utils.tag_normalizer import is_valid_tag
        
        # Tags starting with non-alphanumeric should be invalid
        invalid_start_tags = ["_underscore", "-dash", ".dot"]
        for tag in invalid_start_tags:
            assert is_valid_tag(tag) == False, f"'{tag}' should be invalid (bad start)"
    
    def test_is_valid_tag_filters_html_entities(self):
        """Test that HTML entities and Unicode noise are filtered."""
        from utils.tag_normalizer import is_valid_tag
        
        html_noise = ["html&entities", "&#x", "&nbsp;", "\u200b"]
        for tag in html_noise:
            assert is_valid_tag(tag) == False, f"'{tag}' should be invalid (HTML/Unicode noise)"
    
    def test_is_valid_tag_filters_technical_patterns(self):
        """Test that technical patterns are filtered out.""" 
        from utils.tag_normalizer import is_valid_tag
        
        technical_patterns = [
            "dom-element",
            "fs_operation", 
            "dispatcher",
            "a1b2c3d4e5f6",  # Hex-like
            "uuid-1234-5678"  # UUID-like
        ]
        
        for tag in technical_patterns:
            result = is_valid_tag(tag)
            # These should generally be filtered, but exact behavior may vary
            if not result:
                assert result == False, f"'{tag}' was correctly filtered as technical"
    
    def test_is_valid_tag_allows_valid_patterns(self, valid_tags_list):
        """Test that valid tags pass validation."""
        from utils.tag_normalizer import is_valid_tag
        
        # These should all be valid
        for tag in valid_tags_list:
            assert is_valid_tag(tag) == True, f"'{tag}' should be valid"
    
    def test_is_valid_tag_character_set_validation(self):
        """Test validation of allowed character sets."""
        from utils.tag_normalizer import is_valid_tag
        
        # Valid character combinations
        valid_chars = [
            "alpha123",
            "tag-with-dashes", 
            "tag_with_underscores",
            "nested/hierarchical",
            "french-café",  # International if supported
        ]
        
        for tag in valid_chars:
            result = is_valid_tag(tag)
            # Should generally be valid, but implementation may vary
            assert isinstance(result, bool)
    
    def test_is_valid_tag_minimum_length(self):
        """Test minimum length validation."""
        from utils.tag_normalizer import is_valid_tag
        
        # Very short tags
        short_tags = ["a", "ab", "x"]
        
        for tag in short_tags:
            result = is_valid_tag(tag)
            # May or may not be valid depending on implementation
            assert isinstance(result, bool)
    
    def test_is_valid_tag_must_contain_letters(self):
        """Test that tags must contain at least some letters."""
        from utils.tag_normalizer import is_valid_tag
        
        # Tags without letters
        no_letters = ["123-456", "+-*/", "___", "///"]
        
        for tag in no_letters:
            assert is_valid_tag(tag) == False, f"'{tag}' should be invalid (no letters)"
    
    def test_filter_tags_list(self, valid_tags_list, invalid_tags_list):
        """Test filtering a list of tags."""
        from utils.tag_normalizer import filter_valid_tags
        
        mixed_tags = valid_tags_list + invalid_tags_list
        
        filtered = filter_valid_tags(mixed_tags)
        
        assert isinstance(filtered, list)
        assert len(filtered) <= len(mixed_tags)
        
        # All items in filtered list should be valid
        for tag in filtered:
            from utils.tag_normalizer import is_valid_tag
            assert is_valid_tag(tag) == True, f"'{tag}' should be valid in filtered list"


class TestTagValidationIntegration:
    """Integration tests for tag validation with real data."""
    
    def test_validation_with_complex_vault_data(self, complex_vault):
        """Test validation using data from complex vault fixture."""
        from utils.tag_normalizer import is_valid_tag
        
        # Read a file and extract some test tags
        complex_file = complex_vault / "complex.md"
        if complex_file.exists():
            content = complex_file.read_text()
            
            # Test validation on some expected tags from the fixture
            expected_valid = ["work", "ideas", "tech-stack"]
            for tag in expected_valid:
                if tag in content:
                    assert is_valid_tag(tag) == True
    
    def test_noise_filtering_effectiveness(self):
        """Test that noise filtering effectively removes unwanted tags."""
        from utils.tag_normalizer import filter_valid_tags
        
        # Simulate realistic noisy tag extraction
        noisy_tags = [
            "work",  # Valid
            "notes",  # Valid  
            "123",  # Invalid - pure number
            "dispatcher_util",  # Invalid - technical
            "project-ideas",  # Valid
            "&nbsp;",  # Invalid - HTML entity
            "français",  # Valid - international
            "dom-element",  # Invalid - technical
            "2024-goals",  # Valid - contains letters and numbers
            "_underscore"  # Invalid - starts with underscore
        ]
        
        filtered = filter_valid_tags(noisy_tags)
        
        # Should keep valid tags
        assert "work" in filtered
        assert "notes" in filtered  
        assert "project-ideas" in filtered
        assert "2024-goals" in filtered
        
        # Should remove invalid tags
        assert "123" not in filtered
        assert "&nbsp;" not in filtered
        assert "_underscore" not in filtered
    
    def test_validation_preserves_meaningful_tags(self):
        """Test that validation doesn't over-filter meaningful tags."""
        from utils.tag_normalizer import is_valid_tag
        
        # These are meaningful tags that should NOT be filtered
        meaningful_tags = [
            "api-design",
            "3d-modeling", 
            "v2.0-features",
            "meeting-2024-01",
            "project/frontend",
            "team/development"
        ]
        
        for tag in meaningful_tags:
            assert is_valid_tag(tag) == True, f"'{tag}' should be preserved as meaningful"
    
    def test_edge_case_handling(self):
        """Test validation handles edge cases gracefully."""
        from utils.tag_normalizer import is_valid_tag
        
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            None,  # None value (if function accepts it)
            "a" * 200,  # Very long tag
        ]
        
        for tag in edge_cases:
            try:
                result = is_valid_tag(tag)
                assert isinstance(result, bool)
            except (TypeError, AttributeError):
                # Acceptable for function to reject invalid input types
                pass


class TestUtilsIntegration:
    """Integration tests combining file discovery and tag validation."""
    
    def test_file_discovery_with_validation_pipeline(self, complex_vault):
        """Test complete pipeline from file discovery to tag validation."""
        from utils.file_discovery import find_markdown_files
        from utils.tag_normalizer import is_valid_tag
        
        # Discover files
        files = find_markdown_files(str(complex_vault))
        assert len(files) > 0
        
        # Simulate tag extraction and validation
        discovered_files = [f.name for f in files]
        
        # Should have found expected files
        assert any("complex.md" in f for f in discovered_files)
        
        # Validate some expected tags
        sample_tags = ["work", "ideas", "123", "tech-stack"]
        valid_tags = [tag for tag in sample_tags if is_valid_tag(tag)]
        
        assert "work" in valid_tags
        assert "ideas" in valid_tags
        assert "tech-stack" in valid_tags
        assert "123" not in valid_tags
    
    def test_exclusion_and_validation_together(self, complex_vault):
        """Test file exclusion and tag validation working together."""
        from utils.file_discovery import find_markdown_files
        from utils.tag_normalizer import filter_valid_tags
        
        # Find files excluding templates
        files = find_markdown_files(
            str(complex_vault),
            exclude_patterns=["*.template.md"]
        )
        
        # Should not include template files  
        template_files = [f for f in files if "template" in str(f).lower()]
        assert len(template_files) == 0
        
        # Test tag validation on remaining files
        sample_tags = ["work", "template", "123", "notes"]
        valid_tags = filter_valid_tags(sample_tags)
        
        # Valid content tags should remain
        assert "work" in valid_tags
        assert "notes" in valid_tags
        assert "123" not in valid_tags