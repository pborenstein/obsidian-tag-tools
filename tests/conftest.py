"""
Test fixtures for tagex test suite.

Creates mock Obsidian vaults and test data for comprehensive testing.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def simple_vault(temp_dir):
    """Create a simple mock Obsidian vault with basic markdown files."""
    vault_path = temp_dir / "simple_vault"
    vault_path.mkdir()
    
    # File with frontmatter tags as array
    (vault_path / "file1.md").write_text("""---
title: "Test File 1"
tags: [work, notes, ideas]
created: 2024-01-15
---

# Test File 1

This is content with #inline-tag and #another-tag.
""")
    
    # File with frontmatter tags as single string
    (vault_path / "file2.md").write_text("""---
title: "Test File 2"  
tag: work
category: reference
---

# Test File 2

Content with #reference and #work tags inline.
""")
    
    # File with only inline tags
    (vault_path / "file3.md").write_text("""# File without frontmatter

This file has #articles #research #tech tags inline.
Also has #work-notes and #project-ideas.
""")
    
    # File with no tags
    (vault_path / "no_tags.md").write_text("""# Clean File

This file has no tags at all.
""")
    
    return vault_path


@pytest.fixture
def complex_vault(temp_dir):
    """Create a complex mock vault with various edge cases and structures."""
    vault_path = temp_dir / "complex_vault"
    vault_path.mkdir()
    
    # Create subdirectories
    (vault_path / "folder1").mkdir()
    (vault_path / "folder2").mkdir()
    (vault_path / "templates").mkdir()
    
    # Complex frontmatter file
    (vault_path / "complex.md").write_text("""---
title: Complex Test File
tags:
  - work
  - "project-management"
  - ideas/brainstorming
  - 2024-goals
categories: [personal, work]
aliases: ["Complex File", "Test Document"]
---

# Complex File

Content with #work #ideas #tech-stack and nested/hierarchical tags.
URLs like https://example.com/#section shouldn't be extracted.
""")
    
    # File with malformed YAML
    (vault_path / "malformed.md").write_text("""---
title: Malformed YAML
tags: [work, notes
invalid_yaml: [unclosed
---

# Malformed File

This has #fallback-tags in content.
""")
    
    # File with edge case tags
    (vault_path / "edge_cases.md").write_text("""---
tags: ["123-numeric", "html&entities", "_underscore", "normal-tag"]
---

# Edge Cases

Content with #123 #valid-tag #_invalid and #normal tags.
Also #français #日本語 international tags.
""")
    
    # Template file (should be excluded by patterns)
    (vault_path / "templates" / "note.template.md").write_text("""---
tags: [template, do-not-extract]
---

# Template File
""")
    
    # File in subdirectory
    (vault_path / "folder1" / "nested.md").write_text("""---
tags: [nested, folder, organization]
---

# Nested File

Content with #folder1 #organization tags.
""")
    
    # Binary file (should be ignored)
    (vault_path / "image.png").write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01')
    
    # Empty file
    (vault_path / "empty.md").write_text("")
    
    return vault_path


@pytest.fixture
def expected_simple_tags():
    """Expected tag extraction results for simple_vault."""
    return [
        {
            "tag": "work",
            "tagCount": 3,
            "files": ["file1.md", "file2.md", "file3.md"]
        },
        {
            "tag": "notes", 
            "tagCount": 1,
            "files": ["file1.md"]
        },
        {
            "tag": "ideas",
            "tagCount": 1, 
            "files": ["file1.md"]
        },
        {
            "tag": "inline-tag",
            "tagCount": 1,
            "files": ["file1.md"]
        },
        {
            "tag": "another-tag", 
            "tagCount": 1,
            "files": ["file1.md"]
        },
        {
            "tag": "reference",
            "tagCount": 1,
            "files": ["file2.md"]
        },
        {
            "tag": "articles",
            "tagCount": 1,
            "files": ["file3.md"]
        },
        {
            "tag": "research", 
            "tagCount": 1,
            "files": ["file3.md"]
        },
        {
            "tag": "tech",
            "tagCount": 1,
            "files": ["file3.md"]
        },
        {
            "tag": "work-notes",
            "tagCount": 1,
            "files": ["file3.md"]
        },
        {
            "tag": "project-ideas",
            "tagCount": 1,
            "files": ["file3.md"]
        }
    ]


@pytest.fixture
def test_output_formats():
    """Sample output in different formats for testing output formatters."""
    # Format that matches TagExtractor output: {tag_name: {"count": N, "files": set()}}
    raw_tag_data = {
        "work": {"count": 5, "files": {"file1.md", "file2.md"}},
        "notes": {"count": 2, "files": {"file1.md"}}
    }
    
    # Expected formatted outputs
    formatted_json = [
        {"tag": "work", "tagCount": 5, "files": ["file1.md", "file2.md"]},
        {"tag": "notes", "tagCount": 2, "files": ["file1.md"]}
    ]
    
    return {
        "raw": raw_tag_data,  # What TagExtractor produces
        "json": formatted_json,  # What formatters should produce
        "csv": "tag,tagCount,files\nwork,5,\"file1.md,file2.md\"\nnotes,2,file1.md\n",
        "text": "Tag Summary:\n  work (5 files)\n  notes (2 files)\n\nTotal: 2 unique tags, 7 total usages\n"
    }


@pytest.fixture
def mock_operation_log():
    """Mock operation log data for testing operation logging."""
    return {
        "operation": "rename",
        "timestamp": "2024-01-15T10:30:00",
        "vault_path": "/test/vault",
        "old_tag": "old-name",
        "new_tag": "new-name", 
        "dry_run": False,
        "files_processed": 3,
        "modifications": [
            {
                "file": "file1.md",
                "original_hash": "abc123",
                "new_hash": "def456",
                "changes": ["frontmatter: old-name -> new-name"]
            }
        ],
        "statistics": {
            "total_files": 100,
            "files_with_target_tag": 3,
            "files_modified": 3,
            "errors": 0
        }
    }


@pytest.fixture
def sample_pair_data():
    """Sample co-occurrence data for analysis testing."""
    return [
        {"tag": "work", "tagCount": 50, "relativePaths": ["file1.md", "file2.md", "file3.md"]},
        {"tag": "notes", "tagCount": 30, "relativePaths": ["file1.md", "file2.md"]},
        {"tag": "ideas", "tagCount": 25, "relativePaths": ["file1.md", "file3.md"]},
        {"tag": "reference", "tagCount": 20, "relativePaths": ["file2.md", "file4.md"]},
        {"tag": "articles", "tagCount": 15, "relativePaths": ["file2.md", "file4.md"]},
        {"tag": "singleton", "tagCount": 1, "relativePaths": ["file5.md"]}
    ]


@pytest.fixture
def invalid_tags_list():
    """List of tags that should be filtered out by validation."""
    return [
        "123",           # Pure number
        "456789",        # Pure number 
        "_underscore",   # Starts with underscore
        "-dash",         # Starts with dash
        "html&entities", # HTML entities
        "dom-element",   # Technical pattern
        "fs_operation",  # Technical pattern
        "dispatcher",    # Technical pattern
        "a1b2c3d4e5f6", # Hex-like pattern
        "&#x",          # HTML entity
        "\u200b",       # Unicode noise
        ""              # Empty string
    ]


@pytest.fixture 
def valid_tags_list():
    """List of tags that should pass validation."""
    return [
        "work",
        "notes", 
        "project-ideas",
        "2024-goals",
        "v1.2",
        "3d-model",
        "api2",
        "category/subcategory",
        "français",
        "日本語",
        "tech-stack"
    ]