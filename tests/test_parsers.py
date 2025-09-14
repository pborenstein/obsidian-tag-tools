"""
Tests for the parsers module - frontmatter and inline tag parsing.
"""

import pytest
from pathlib import Path


class TestFrontmatterParser:
    """Tests for frontmatter YAML tag parsing."""
    
    def test_parse_yaml_tags_as_list(self):
        """Test parsing frontmatter with tags as a list."""
        content = """---
title: "Test File"
tags: [work, notes, ideas]
created: 2024-01-15
---

# Content here
"""
        # Import should work - this tests that the module exists and is importable
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert set(tags) == {"work", "notes", "ideas"}
    
    def test_parse_yaml_tags_as_multiline_list(self):
        """Test parsing frontmatter with tags as multiline YAML list."""
        content = """---
title: Test File
tags:
  - work
  - "project-management" 
  - ideas/brainstorming
  - 2024-goals
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert "work" in tags
        assert "project-management" in tags
        assert "ideas/brainstorming" in tags
        assert "2024-goals" in tags
    
    def test_parse_single_tag(self):
        """Test parsing frontmatter with single tag field."""
        content = """---
title: "Test File"
tag: work
category: reference
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert "work" in tags
        # Should not include 'reference' as it's in category field, not tags
        
    def test_parse_both_tag_and_tags_fields(self):
        """Test parsing when both 'tag' and 'tags' fields are present."""
        content = """---
title: Test
tag: single-tag
tags: [multiple, tags]
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        # Should include tags from both fields
        assert "single-tag" in tags
        assert "multiple" in tags 
        assert "tags" in tags
    
    def test_no_frontmatter(self):
        """Test file with no frontmatter returns empty list."""
        content = """# Just a title

No frontmatter here.
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert tags == []
    
    def test_empty_tags_field(self):
        """Test frontmatter with empty tags field."""
        content = """---
title: Test
tags: []
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert tags == []
    
    def test_malformed_yaml(self):
        """Test handling of malformed YAML frontmatter."""
        content = """---
title: Test
tags: [work, notes
invalid_yaml: [unclosed
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter

        # Should handle gracefully, possibly returning empty list or partial results
        frontmatter, _ = extract_frontmatter(content)
        if frontmatter:
            tags = extract_tags_from_frontmatter(frontmatter)
        else:
            tags = []
        # The implementation should be robust - exact behavior depends on implementation
        assert isinstance(tags, list)
    
    def test_quoted_tag_values(self):
        """Test handling of quoted tag values in YAML."""
        content = """---
tags: ["work-project", "notes & ideas", "special/category"]
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert "work-project" in tags
        assert "notes & ideas" in tags
        assert "special/category" in tags
    
    def test_mixed_tag_formats(self):
        """Test mixing different tag formats in YAML."""
        content = """---
tags: 
  - unquoted-tag
  - "quoted-tag"
  - 'single-quoted'
  - nested/hierarchical
---

Content
"""
        from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
        
        frontmatter, _ = extract_frontmatter(content)
        tags = extract_tags_from_frontmatter(frontmatter)
        assert "unquoted-tag" in tags
        assert "quoted-tag" in tags
        assert "single-quoted" in tags
        assert "nested/hierarchical" in tags


class TestInlineParser:
    """Tests for inline hashtag parsing."""
    
    def test_basic_hashtag_extraction(self):
        """Test extracting basic hashtags from content."""
        content = """# Title

This content has #work and #notes tags.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert set(tags) == {"work", "notes"}
    
    def test_hashtags_with_special_characters(self):
        """Test hashtags with dashes, underscores, numbers."""
        content = """
Content with #project-ideas #work_notes #tech-stack and #2024-goals.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "project-ideas" in tags
        assert "work_notes" in tags
        assert "tech-stack" in tags
        assert "2024-goals" in tags
    
    def test_hierarchical_hashtags(self):
        """Test nested/hierarchical hashtags with slashes."""
        content = """
Tags like #category/subcategory and #work/project/planning.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "category/subcategory" in tags
        assert "work/project/planning" in tags
    
    def test_ignore_url_fragments(self):
        """Test that URL fragments are not extracted as tags."""
        content = """
Links like https://example.com/#section and http://site.com/#anchor should be ignored.
But #real-tag should be extracted.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "real-tag" in tags
        # Should not include 'section' or 'anchor' from URLs
        assert "section" not in tags
        assert "anchor" not in tags
    
    def test_hashtags_in_code_blocks(self):
        """Test that hashtags inside code blocks are ignored."""
        content = """
Regular #tag should be extracted.

```python
# This is a comment with #code-tag
print("Hello #world")
```

`inline code with #inline-code-tag`

Another #normal-tag here.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "tag" in tags
        assert "normal-tag" in tags
        # Should not extract tags from code blocks
        assert "code-tag" not in tags
        assert "world" not in tags
        assert "inline-code-tag" not in tags
    
    def test_hashtags_at_word_boundaries(self):
        """Test that hashtags are only extracted at word boundaries."""
        content = """
Valid #tag and #another-tag.
But not in email@domain.com#fragment or word#notag.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "tag" in tags
        assert "another-tag" in tags
        assert "fragment" not in tags
        assert "notag" not in tags
    
    def test_international_characters(self):
        """Test hashtags with international/unicode characters."""
        content = """
Tags with #français #日本語 #español characters.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "français" in tags
        assert "日本語" in tags
        assert "español" in tags
    
    def test_empty_content(self):
        """Test handling of empty content."""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags("")
        assert tags == []
    
    def test_no_hashtags(self):
        """Test content with no hashtags."""
        content = """
This is just regular content without any tags.
No hashtags here at all.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert tags == []
    
    def test_duplicate_hashtags(self):
        """Test that duplicate hashtags are handled correctly."""
        content = """
This has #work multiple times. Another #work tag here.
And one more #work for good measure.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        # Should handle duplicates appropriately (either deduplicated or counted)
        assert "work" in tags
    
    def test_hashtags_with_punctuation(self):
        """Test hashtags followed by punctuation."""
        content = """
Tags like #work, #notes. #ideas! #project? #research; should all work.
"""
        from parsers.inline_parser import extract_inline_tags
        
        tags = extract_inline_tags(content)
        assert "work" in tags
        assert "notes" in tags
        assert "ideas" in tags
        assert "project" in tags
        assert "research" in tags


class TestParserIntegration:
    """Integration tests for both parsers working together."""
    
    def test_both_frontmatter_and_inline_tags(self):
        """Test extracting tags from both frontmatter and inline content."""
        content = """---
tags: [work, notes]
---

# File with both types

This content has #ideas and #project inline tags.
"""
        from parsers.frontmatter_parser import extract_frontmatter_tags
        from parsers.inline_parser import extract_inline_tags
        
        frontmatter, _ = extract_frontmatter(content)
        frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
        inline_tags = extract_inline_tags(content)
        
        assert "work" in frontmatter_tags
        assert "notes" in frontmatter_tags
        assert "ideas" in inline_tags
        assert "project" in inline_tags
    
    def test_overlapping_tags_from_both_sources(self):
        """Test when same tags appear in both frontmatter and inline."""
        content = """---
tags: [work, notes]
---

# Content

More content with #work and #research tags.
"""
        from parsers.frontmatter_parser import extract_frontmatter_tags
        from parsers.inline_parser import extract_inline_tags
        
        frontmatter, _ = extract_frontmatter(content)
        frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
        inline_tags = extract_inline_tags(content)
        
        assert "work" in frontmatter_tags
        assert "work" in inline_tags
        assert "notes" in frontmatter_tags
        assert "research" in inline_tags
    
    def test_file_processing_with_complex_structure(self, complex_vault):
        """Test parsing files from the complex vault fixture."""
        complex_file = complex_vault / "complex.md"
        content = complex_file.read_text()
        
        from parsers.frontmatter_parser import extract_frontmatter_tags
        from parsers.inline_parser import extract_inline_tags
        
        frontmatter, _ = extract_frontmatter(content)
        frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
        inline_tags = extract_inline_tags(content)
        
        # Should extract from complex frontmatter
        assert len(frontmatter_tags) > 0
        # Should extract inline tags but not URL fragments
        assert len(inline_tags) > 0