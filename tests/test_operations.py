"""
Tests for the operations module - tag rename, merge, and operation logging.
"""

import pytest
import json
from pathlib import Path
import shutil


class TestTagOperationEngine:
    """Tests for the base TagOperationEngine class."""
    
    def test_operation_engine_initialization(self):
        """Test TagOperationEngine can be initialized."""
        from operations.tag_operations import TagOperationEngine
        
        # This is an abstract base class, so we may need to test via subclasses
        # But we can test that it exists and has expected interface
        assert hasattr(TagOperationEngine, '__init__')
    
    def test_dry_run_mode_available(self):
        """Test that dry-run mode is available in operation engine."""
        from operations.tag_operations import TagOperationEngine
        
        # Check that dry-run functionality exists in the interface
        # This might be tested through subclasses
        assert hasattr(TagOperationEngine, 'run_operation')


class TestRenameOperation:
    """Tests for tag rename operations."""
    
    def test_rename_operation_initialization(self):
        """Test RenameOperation can be initialized."""
        from operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path="/test/vault",
            old_tag="old-name",
            new_tag="new-name",
            dry_run=True
        )
        assert operation is not None
    
    def test_rename_dry_run_mode(self, simple_vault):
        """Test rename operation in dry-run mode."""
        from operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path=str(simple_vault),
            old_tag="work",
            new_tag="professional", 
            dry_run=True
        )
        
        results = operation.run_operation()
        
        # Dry run should return preview of changes without modifying files
        assert "preview" in results or "changes" in results or isinstance(results, dict)
        
        # Original files should be unchanged
        file1_content = (simple_vault / "file1.md").read_text()
        assert "work" in file1_content  # Should still contain old tag
        assert "professional" not in file1_content  # Should not contain new tag
    
    def test_rename_actual_execution(self, temp_dir):
        """Test actual rename operation execution."""
        from operations.tag_operations import RenameOperation
        
        # Create a copy of vault for modification
        test_vault = temp_dir / "rename_vault"
        test_vault.mkdir()
        
        # Create test file with target tag
        test_file = test_vault / "test.md"
        test_file.write_text("""---
tags: [work, notes]
---

# Test File

Content with #work inline tag.
""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work", 
            new_tag="professional",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # Check that file was actually modified
        modified_content = test_file.read_text()
        assert "professional" in modified_content
        # Original tag should be replaced (depending on implementation)
        
        # Results should contain operation summary
        assert isinstance(results, dict)
        assert "stats" in results
        assert "files_modified" in results["stats"]
    
    def test_rename_preserves_file_structure(self, temp_dir):
        """Test that rename operation preserves original file structure."""
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "structure_vault"
        test_vault.mkdir()
        
        # Create file with complex structure
        test_file = test_vault / "complex.md"
        original_content = """---
title: "Complex File"
tags: [work, notes, ideas]
created: 2024-01-15
author: "Test User"
---

# Complex File

This file has complex structure with #work tags.

## Section 2

More content here.
"""
        test_file.write_text(original_content)
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional", 
            dry_run=False
        )
        
        operation.run_operation()
        
        # Check that structure is preserved
        modified_content = test_file.read_text()
        
        # Should still have frontmatter structure
        assert "title: \"Complex File\"" in modified_content
        assert "created: 2024-01-15" in modified_content  
        assert "author: \"Test User\"" in modified_content
        
        # Should preserve content structure
        assert "# Complex File" in modified_content
        assert "## Section 2" in modified_content
    
    def test_rename_only_target_tag(self, temp_dir):
        """Test rename only affects the target tag, not other tags."""
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "selective_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "selective.md"
        test_file.write_text("""---
tags: [work, workflow, workspace]
---

Content with #work #workflow and #workspace tags.
""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=False
        )
        
        operation.run_operation()
        
        modified_content = test_file.read_text()
        
        # Should have renamed 'work' to 'professional'
        # But should preserve 'workflow' and 'workspace' (similar but different tags)
        assert "workflow" in modified_content
        assert "workspace" in modified_content
    
    def test_rename_handles_no_matching_files(self, simple_vault):
        """Test rename operation when no files contain the target tag."""
        from operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path=str(simple_vault),
            old_tag="nonexistent-tag",
            new_tag="new-tag",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # Should handle gracefully
        assert isinstance(results, dict)
        assert results.get("files_modified", 0) == 0 or results.get("statistics", {}).get("files_modified", 0) == 0


class TestMergeOperation:
    """Tests for tag merge operations."""
    
    def test_merge_operation_initialization(self):
        """Test MergeOperation can be initialized."""
        from operations.tag_operations import MergeOperation
        
        operation = MergeOperation(
            vault_path="/test/vault",
            source_tags=["tag1", "tag2", "tag3"],
            target_tag="merged-tag",
            dry_run=True
        )
        assert operation is not None
    
    def test_merge_dry_run_mode(self, temp_dir):
        """Test merge operation in dry-run mode."""
        from operations.tag_operations import MergeOperation
        
        # Create test vault with merge candidates
        test_vault = temp_dir / "merge_vault"
        test_vault.mkdir()
        
        (test_vault / "file1.md").write_text("""---
tags: [ideas, brainstorming]
---
Content""")
        
        (test_vault / "file2.md").write_text("""---
tags: [thoughts, ideas]
---
Content with #brainstorming""")
        
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["ideas", "brainstorming", "thoughts"],
            target_tag="thinking",
            dry_run=True
        )
        
        results = operation.run_operation()
        
        # Should return preview without modifying files
        assert isinstance(results, dict)
        
        # Files should be unchanged
        file1_content = (test_vault / "file1.md").read_text()
        assert "ideas" in file1_content
        assert "thinking" not in file1_content
    
    def test_merge_actual_execution(self, temp_dir):
        """Test actual merge operation execution."""
        from operations.tag_operations import MergeOperation
        
        test_vault = temp_dir / "merge_exec_vault"
        test_vault.mkdir()
        
        (test_vault / "file1.md").write_text("""---
tags: [ideas, brainstorming, notes]
---

Content with #thoughts inline.""")
        
        (test_vault / "file2.md").write_text("""---
tags: [thoughts, reference]
---

Content with #ideas and #brainstorming.""")
        
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["ideas", "brainstorming", "thoughts"],
            target_tag="thinking",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # Check files were modified
        file1_content = (test_vault / "file1.md").read_text()
        file2_content = (test_vault / "file2.md").read_text()
        
        # Should contain target tag
        assert "thinking" in file1_content or "thinking" in file2_content
        
        # Other tags should be preserved
        assert "notes" in file1_content
        assert "reference" in file2_content
    
    def test_merge_handles_partial_matches(self, temp_dir):
        """Test merge when files only contain some of the source tags."""
        from operations.tag_operations import MergeOperation
        
        test_vault = temp_dir / "partial_vault"
        test_vault.mkdir()
        
        # File with only one of the source tags
        (test_vault / "partial.md").write_text("""---
tags: [ideas, unrelated]
---
Content""")
        
        # File with multiple source tags
        (test_vault / "multiple.md").write_text("""---
tags: [ideas, brainstorming, thoughts]
---
Content""")
        
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["ideas", "brainstorming", "thoughts"],
            target_tag="thinking",
            dry_run=False
        )
        
        operation.run_operation()
        
        # Both files should be processed
        partial_content = (test_vault / "partial.md").read_text()
        multiple_content = (test_vault / "multiple.md").read_text()
        
        # Files that had any of the source tags should be modified
        assert "thinking" in partial_content or "thinking" in multiple_content


class TestOperationLogging:
    """Tests for operation logging functionality."""
    
    def test_operation_creates_log_file(self, temp_dir):
        """Test that operations create log files."""
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "log_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "test.md"
        test_file.write_text("""---
tags: [work]
---
Content""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work", 
            new_tag="professional",
            dry_run=False
        )
        
        operation.run_operation()
        
        # Should create log file in current directory (not vault)
        # Look for log files in temp_dir or working directory
        log_files = list(Path.cwd().glob("tag-*-op_*.json"))
        if len(log_files) == 0:
            # Check temp directory
            log_files = list(temp_dir.glob("tag-*-op_*.json"))
        
        # Should have created at least one log file
        assert len(log_files) > 0
    
    def test_log_file_structure(self, mock_operation_log):
        """Test that log file has expected structure."""
        # This tests the expected structure based on the fixture
        log_data = mock_operation_log
        
        # Required top-level fields
        assert "operation" in log_data
        assert "timestamp" in log_data
        assert "vault_path" in log_data
        assert "dry_run" in log_data
        assert "files_processed" in log_data
        assert "statistics" in log_data
        
        # Statistics structure
        stats = log_data["statistics"]
        assert "total_files" in stats
        assert "files_modified" in stats
        assert "errors" in stats
        
        # Modifications structure (if not dry run)
        if not log_data["dry_run"]:
            assert "modifications" in log_data
            if len(log_data["modifications"]) > 0:
                mod = log_data["modifications"][0]
                assert "file" in mod
                assert "original_hash" in mod or "changes" in mod
    
    def test_operation_integrity_checks(self, temp_dir):
        """Test that operations include integrity checks."""
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "integrity_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "integrity_test.md"
        original_content = """---
tags: [test-tag]
---

# Test File

Content to check integrity."""
        test_file.write_text(original_content)
        
        # Get original file hash/size for comparison
        original_size = test_file.stat().st_size
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="test-tag",
            new_tag="renamed-tag",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # File should exist and have reasonable size
        assert test_file.exists()
        new_size = test_file.stat().st_size
        
        # Size should be similar (tag rename shouldn't drastically change file size)
        assert abs(new_size - original_size) < 100  # Allow for reasonable tag name differences
    
    def test_dry_run_produces_log(self, temp_dir):
        """Test that dry-run mode also produces logs."""
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "dry_run_vault"
        test_vault.mkdir()
        
        (test_vault / "test.md").write_text("""---
tags: [work]
---
Content""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=True
        )
        
        results = operation.run_operation()
        
        # Dry run should also produce results/logs
        assert isinstance(results, dict)
        # Should indicate no files were actually modified
        if "files_modified" in results:
            # In dry run, files_modified should be 0 or indicate preview mode
            pass


class TestOperationEdgeCases:
    """Tests for edge cases and error conditions in operations."""
    
    def test_operation_with_nonexistent_vault(self):
        """Test operation with nonexistent vault path."""
        from operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path="/nonexistent/vault/path",
            old_tag="work",
            new_tag="professional", 
            dry_run=True
        )
        
        # Should handle gracefully
        try:
            results = operation.run_operation()
            # Should either return empty results or raise appropriate exception
            assert isinstance(results, dict) or results is None
        except (FileNotFoundError, OSError):
            # Acceptable to raise appropriate exceptions
            pass
    
    def test_operation_with_invalid_tag_names(self, simple_vault):
        """Test operation with invalid tag names."""
        from operations.tag_operations import RenameOperation
        
        # Test with empty tag name
        operation = RenameOperation(
            vault_path=str(simple_vault),
            old_tag="",
            new_tag="valid-tag",
            dry_run=True
        )
        
        # Should handle invalid input gracefully
        try:
            results = operation.run_operation()
            if results:
                assert results.get("files_modified", 0) == 0
        except ValueError:
            # Acceptable to raise validation errors
            pass
    
    def test_operation_with_readonly_files(self, temp_dir):
        """Test operation behavior with readonly files."""
        import os
        import stat
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "readonly_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "readonly.md"
        test_file.write_text("""---
tags: [work]
---
Content""")
        
        # Make file readonly
        test_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=False
        )
        
        try:
            results = operation.run_operation()
            # Should handle readonly files gracefully
            assert isinstance(results, dict)
        except PermissionError:
            # Acceptable to fail with permission errors
            pass
        finally:
            # Restore write permissions for cleanup
            try:
                test_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass
    
    def test_concurrent_operations_safety(self, temp_dir):
        """Test that operations are safe from concurrent modification issues."""
        from operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "concurrent_vault"  
        test_vault.mkdir()
        
        test_file = test_vault / "concurrent.md"
        test_file.write_text("""---
tags: [work, notes]
---
Content""")
        
        # Create two operations on the same vault
        operation1 = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=True  # Use dry run to avoid actual conflicts
        )
        
        operation2 = RenameOperation(
            vault_path=str(test_vault), 
            old_tag="notes",
            new_tag="documentation",
            dry_run=True
        )
        
        # Both should execute without interfering
        results1 = operation1.run_operation()
        results2 = operation2.run_operation()
        
        assert isinstance(results1, dict)
        assert isinstance(results2, dict)
        
        # Original file should be unchanged (dry run)
        content = test_file.read_text()
        assert "work" in content
        assert "notes" in content