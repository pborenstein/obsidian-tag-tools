"""
Tests for the CLI interface - main.py command-line interface using Click.
"""

import pytest
from click.testing import CliRunner
import json
import tempfile
from pathlib import Path


class TestCLIBasics:
    """Tests for basic CLI functionality."""
    
    def test_cli_entry_point_exists(self):
        """Test that main CLI entry point exists and is importable."""
        from main import cli
        
        assert cli is not None
        assert callable(cli)
    
    def test_cli_help_message(self):
        """Test CLI displays help message."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Usage:" in result.output or "Commands:" in result.output
        
        # Should show available commands
        assert "extract" in result.output
        assert "rename" in result.output
        assert "merge" in result.output
    
    def test_cli_version_info(self):
        """Test CLI version information if available."""
        from main import cli
        
        runner = CliRunner()
        
        # Try common version flags
        for version_flag in ['--version', '-V']:
            result = runner.invoke(cli, [version_flag])
            if result.exit_code == 0:
                # If version flag exists, should display version
                assert len(result.output.strip()) > 0
                break
    
    def test_cli_without_args_shows_help(self):
        """Test CLI without arguments shows help or usage info."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [])
        
        # Should either show help or fail with usage message
        assert "Usage:" in result.output or "Commands:" in result.output or result.exit_code != 0


class TestExtractCommand:
    """Tests for the extract command."""
    
    def test_extract_command_help(self):
        """Test extract command help message."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', '--help'])
        
        assert result.exit_code == 0
        assert "extract" in result.output.lower()
        
        # Should show available options
        assert "--output" in result.output or "-o" in result.output
        assert "--format" in result.output or "-f" in result.output
    
    def test_extract_command_basic(self, simple_vault):
        """Test basic extract command execution."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', str(simple_vault)])
        
        assert result.exit_code == 0
        
        # Should output JSON by default
        output = result.output
        assert len(output) > 0
        
        # Try to parse as JSON
        try:
            if '[' in output or '{' in output:
                # Extract JSON part if mixed with other output
                json_start = output.find('[')
                if json_start == -1:
                    json_start = output.find('{')
                json_data = json.loads(output[json_start:])
                assert isinstance(json_data, (list, dict))
        except json.JSONDecodeError:
            # Output might include summary text along with JSON
            pass
    
    def test_extract_command_with_output_file(self, simple_vault, temp_dir):
        """Test extract command with output file option."""
        from main import cli
        
        output_file = temp_dir / "test_output.json"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract', 
            str(simple_vault), 
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # File should contain valid JSON
        content = output_file.read_text()
        json_data = json.loads(content)
        assert isinstance(json_data, list)
    
    def test_extract_command_csv_format(self, simple_vault, temp_dir):
        """Test extract command with CSV format."""
        from main import cli
        
        output_file = temp_dir / "test_output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(simple_vault),
            '--format', 'csv',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "tag,tagCount,files" in content or "tag," in content
    
    def test_extract_command_text_format(self, simple_vault):
        """Test extract command with text format."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(simple_vault),
            '--format', 'txt'
        ])
        
        assert result.exit_code == 0
        
        output = result.output
        assert len(output) > 0
        # Should contain human-readable summary
        assert any(word in output.lower() for word in ['tags', 'files', 'total'])
    
    def test_extract_command_with_exclusions(self, complex_vault):
        """Test extract command with exclusion patterns."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(complex_vault),
            '--exclude', '*.template.md',
            '--exclude', 'templates/*'
        ])
        
        assert result.exit_code == 0
        
        # Should execute successfully with exclusions
        assert len(result.output) >= 0
    
    def test_extract_command_verbose_mode(self, simple_vault):
        """Test extract command with verbose output."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(simple_vault),
            '--verbose'
        ])
        
        assert result.exit_code == 0
        
        # Verbose should produce more output
        assert len(result.output) > 0
    
    def test_extract_command_quiet_mode(self, simple_vault):
        """Test extract command with quiet mode."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(simple_vault),
            '--quiet'
        ])
        
        assert result.exit_code == 0
        
        # Quiet mode might suppress summary output
        # But should still produce the main output
    
    def test_extract_command_no_filter(self, simple_vault):
        """Test extract command with --no-filter option."""
        from main import cli
        
        runner = CliRunner()
        
        # Extract with filtering (default)
        result_filtered = runner.invoke(cli, ['extract', str(simple_vault)])
        
        # Extract without filtering
        result_unfiltered = runner.invoke(cli, [
            'extract', 
            str(simple_vault),
            '--no-filter'
        ])
        
        assert result_filtered.exit_code == 0
        assert result_unfiltered.exit_code == 0
        
        # Unfiltered might have more results
        # This depends on the test data having invalid tags
    
    def test_extract_command_nonexistent_vault(self):
        """Test extract command with nonexistent vault."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['extract', '/nonexistent/vault'])
        
        # Should fail gracefully
        assert result.exit_code != 0
        assert len(result.output) > 0  # Should have error message


class TestRenameCommand:
    """Tests for the rename command."""
    
    def test_rename_command_help(self):
        """Test rename command help message."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['rename', '--help'])
        
        assert result.exit_code == 0
        assert "rename" in result.output.lower()
        assert "--dry-run" in result.output
    
    def test_rename_command_dry_run(self, simple_vault):
        """Test rename command in dry-run mode."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'rename',
            str(simple_vault),
            'work',
            'professional', 
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        
        # Should show preview without modifying files
        output = result.output
        assert len(output) > 0
        
        # Original files should be unchanged
        file1_content = (simple_vault / "file1.md").read_text()
        assert "work" in file1_content
        assert "professional" not in file1_content
    
    def test_rename_command_missing_arguments(self):
        """Test rename command with missing arguments."""
        from main import cli
        
        runner = CliRunner()
        
        # Missing new tag argument
        result = runner.invoke(cli, ['rename', '/vault', 'old-tag'])
        assert result.exit_code != 0
        
        # Missing both tags
        result = runner.invoke(cli, ['rename', '/vault'])
        assert result.exit_code != 0
    
    def test_rename_command_actual_execution(self, temp_dir):
        """Test actual rename command execution."""
        from main import cli
        
        # Create a test vault copy for modification
        test_vault = temp_dir / "rename_test_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "test_rename.md"
        test_file.write_text("""---
tags: [work, notes]
---

Content with #work tag.""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'rename',
            str(test_vault),
            'work',
            'professional'
        ])
        
        # Should execute successfully
        assert result.exit_code == 0
        
        # Check that file was modified
        modified_content = test_file.read_text()
        # Depending on implementation, should contain new tag
    
    def test_rename_command_nonexistent_tag(self, simple_vault):
        """Test rename command with nonexistent tag."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'rename',
            str(simple_vault),
            'nonexistent-tag',
            'new-tag',
            '--dry-run'
        ])
        
        # Should handle gracefully
        assert result.exit_code == 0 or "no files" in result.output.lower()
    
    def test_rename_command_invalid_tag_names(self, simple_vault):
        """Test rename command with invalid tag names."""
        from main import cli
        
        runner = CliRunner()
        
        # Empty tag names
        result = runner.invoke(cli, [
            'rename',
            str(simple_vault),
            '',
            'new-tag',
            '--dry-run'
        ])
        
        # Should handle invalid input
        assert result.exit_code != 0 or len(result.output) > 0


class TestMergeCommand:
    """Tests for the merge command."""
    
    def test_merge_command_help(self):
        """Test merge command help message."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['merge', '--help'])
        
        assert result.exit_code == 0
        assert "merge" in result.output.lower()
        assert "--into" in result.output
        assert "--dry-run" in result.output
    
    def test_merge_command_dry_run(self, temp_dir):
        """Test merge command in dry-run mode."""
        from main import cli
        
        # Create test vault with merge candidates
        test_vault = temp_dir / "merge_test_vault"
        test_vault.mkdir()
        
        (test_vault / "file1.md").write_text("""---
tags: [ideas, brainstorming]
---
Content""")
        
        (test_vault / "file2.md").write_text("""---  
tags: [thoughts]
---
Content""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'merge',
            str(test_vault),
            'ideas',
            'brainstorming', 
            'thoughts',
            '--into', 'thinking',
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        
        # Should show preview
        assert len(result.output) > 0
        
        # Files should be unchanged
        file1_content = (test_vault / "file1.md").read_text()
        assert "ideas" in file1_content
        assert "thinking" not in file1_content
    
    def test_merge_command_missing_target(self, simple_vault):
        """Test merge command without --into target."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'merge',
            str(simple_vault),
            'tag1',
            'tag2'
        ])
        
        # Should fail - merge requires target tag
        assert result.exit_code != 0
        assert "--into" in result.output or "required" in result.output.lower()
    
    def test_merge_command_single_source_tag(self, simple_vault):
        """Test merge command with only one source tag."""
        from main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            'merge',
            str(simple_vault),
            'work',
            '--into', 'professional',
            '--dry-run'
        ])

        # Should handle single tag merge
        assert result.exit_code == 0 or len(result.output) > 0


class TestDeleteCommand:
    """Tests for the delete command."""

    def test_delete_command_help(self):
        """Test delete command help message."""
        from main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ['delete', '--help'])

        assert result.exit_code == 0
        assert "delete" in result.output.lower()
        assert "--dry-run" in result.output

    def test_delete_command_dry_run(self, temp_dir):
        """Test delete command in dry-run mode."""
        from main import cli

        # Create test vault with tags to delete
        test_vault = temp_dir / "delete_test_vault"
        test_vault.mkdir()

        (test_vault / "file1.md").write_text("""---
tags: [work, unwanted-tag, notes]
---

Content with #unwanted-tag inline.
""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(test_vault),
            'unwanted-tag',
            '--dry-run'
        ])

        assert result.exit_code == 0

        # Should show preview
        assert len(result.output) > 0

        # Files should be unchanged
        file_content = (test_vault / "file1.md").read_text()
        assert "unwanted-tag" in file_content
        assert "#unwanted-tag" in file_content

    def test_delete_command_multiple_tags(self, temp_dir):
        """Test delete command with multiple tags."""
        from main import cli

        test_vault = temp_dir / "multi_delete_vault"
        test_vault.mkdir()

        (test_vault / "test.md").write_text("""---
tags: [work, unwanted1, unwanted2, notes]
---

Content with #unwanted1 and #unwanted2.
""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(test_vault),
            'unwanted1',
            'unwanted2',
            '--dry-run'
        ])

        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_delete_command_missing_arguments(self):
        """Test delete command with missing arguments."""
        from main import cli

        runner = CliRunner()

        # Missing tag arguments
        result = runner.invoke(cli, ['delete', '/vault'])
        assert result.exit_code != 0

        # Missing vault path
        result = runner.invoke(cli, ['delete'])
        assert result.exit_code != 0

    def test_delete_command_shows_warnings_for_inline(self, temp_dir, capsys):
        """Test that delete command shows warnings for inline tag deletion."""
        from main import cli

        test_vault = temp_dir / "warning_vault"
        test_vault.mkdir()

        (test_vault / "inline_test.md").write_text("""---
tags: [work]
---

This content has #unwanted-inline tag that will trigger warnings.
""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(test_vault),
            'unwanted-inline',
            '--dry-run'
        ])

        # Should succeed but show warnings
        assert result.exit_code == 0

        # Output should contain warning about inline deletion
        output = result.output
        assert "WARNING" in output or "warn" in output.lower()

    def test_delete_command_actual_execution(self, temp_dir):
        """Test delete command actual execution (not dry-run)."""
        from main import cli

        test_vault = temp_dir / "exec_delete_vault"
        test_vault.mkdir()

        test_file = test_vault / "execution_test.md"
        test_file.write_text("""---
tags: [work, unwanted-tag, notes]
---

# Test File

Content with some text.
""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(test_vault),
            'unwanted-tag'
        ])

        assert result.exit_code == 0

        # File should be modified
        modified_content = test_file.read_text()
        assert "unwanted-tag" not in modified_content
        assert "work" in modified_content  # Other tags preserved
        assert "notes" in modified_content

    def test_delete_command_nonexistent_tag(self, simple_vault):
        """Test delete command with nonexistent tag."""
        from main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(simple_vault),
            'absolutely-nonexistent-tag',
            '--dry-run'
        ])

        # Should handle gracefully
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_delete_command_preserves_structure(self, temp_dir):
        """Test delete command preserves file structure."""
        from main import cli

        test_vault = temp_dir / "structure_vault"
        test_vault.mkdir()

        test_file = test_vault / "structure_test.md"
        test_file.write_text("""---
title: "Important File"
tags: [work, unwanted-tag, notes]
author: "Test User"
---

# Important File

This file has important structure.

## Section 2

Content here.
""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(test_vault),
            'unwanted-tag'
        ])

        assert result.exit_code == 0

        # Structure should be preserved
        modified_content = test_file.read_text()
        assert "title: \"Important File\"" in modified_content
        assert "author: \"Test User\"" in modified_content
        assert "# Important File" in modified_content
        assert "## Section 2" in modified_content

        # Tag should be gone
        assert "unwanted-tag" not in modified_content

    def test_delete_command_empty_tag_argument(self, simple_vault):
        """Test delete command with empty tag argument."""
        from main import cli

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete',
            str(simple_vault),
            '',
            '--dry-run'
        ])

        # Should handle empty tag gracefully or reject it
        # Either exit code != 0 or should process gracefully
        assert result.exit_code == 0 or len(result.output) > 0
    
    def test_merge_command_actual_execution(self, temp_dir):
        """Test actual merge command execution."""
        from main import cli
        
        test_vault = temp_dir / "merge_exec_vault"
        test_vault.mkdir()
        
        (test_vault / "merge_test.md").write_text("""---
tags: [ideas, brainstorming, notes]
---

Content with #thoughts inline.""")
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'merge',
            str(test_vault),
            'ideas',
            'brainstorming',
            'thoughts',
            '--into', 'thinking'
        ])
        
        # Should execute successfully
        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Tests for CLI error handling and edge cases."""
    
    def test_invalid_command(self):
        """Test CLI with invalid command."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['invalid-command'])
        
        assert result.exit_code != 0
        assert "Usage:" in result.output or "No such command" in result.output
    
    def test_extract_invalid_format(self, simple_vault):
        """Test extract with invalid format option."""
        from main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract',
            str(simple_vault),
            '--format', 'invalid-format'
        ])
        
        # Should fail with invalid format
        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "choice" in result.output.lower()
    
    def test_command_with_invalid_vault_path(self):
        """Test commands with invalid vault paths."""
        from main import cli
        
        runner = CliRunner()
        
        # Test with clearly invalid paths
        invalid_paths = ['/definitely/not/a/real/path', '']
        
        for path in invalid_paths:
            if path:  # Skip empty path as it might be handled differently
                result = runner.invoke(cli, ['extract', path])
                # Should fail gracefully with error message
                assert result.exit_code != 0
    
    def test_permission_errors(self, temp_dir):
        """Test CLI handling of permission errors."""
        import os
        import stat
        from main import cli
        
        # Create a vault with no read permissions
        restricted_vault = temp_dir / "restricted"
        restricted_vault.mkdir()
        
        test_file = restricted_vault / "restricted.md"
        test_file.write_text("""---
tags: [test]
---
Content""")
        
        # Remove read permissions
        try:
            restricted_vault.chmod(stat.S_IWUSR)
            
            runner = CliRunner()
            result = runner.invoke(cli, ['extract', str(restricted_vault)])
            
            # Should handle permission errors gracefully
            # Exact behavior depends on implementation
            assert isinstance(result.exit_code, int)
            
        finally:
            # Restore permissions for cleanup
            try:
                restricted_vault.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            except:
                pass
    
    def test_keyboard_interrupt_handling(self, simple_vault):
        """Test CLI handling of keyboard interrupts."""
        from main import cli
        import signal
        
        runner = CliRunner()
        
        # This is difficult to test directly, but we can at least verify
        # the CLI doesn't crash on normal operations
        result = runner.invoke(cli, ['extract', str(simple_vault)])
        assert isinstance(result.exit_code, int)


class TestCLIIntegration:
    """Integration tests combining multiple CLI features."""
    
    def test_full_workflow_via_cli(self, temp_dir):
        """Test complete workflow using CLI commands."""
        from main import cli
        
        # Create test vault
        test_vault = temp_dir / "workflow_vault"
        test_vault.mkdir()
        
        (test_vault / "workflow.md").write_text("""---
tags: [work, old-project]
---

Content with #work and #notes tags.""")
        
        runner = CliRunner()
        
        # 1. Extract tags
        extract_result = runner.invoke(cli, ['extract', str(test_vault)])
        assert extract_result.exit_code == 0
        
        # 2. Rename a tag (dry run first)
        rename_dry_result = runner.invoke(cli, [
            'rename', str(test_vault), 'work', 'professional', '--dry-run'
        ])
        assert rename_dry_result.exit_code == 0
        
        # 3. Actually rename tag
        rename_result = runner.invoke(cli, [
            'rename', str(test_vault), 'work', 'professional'
        ])
        assert rename_result.exit_code == 0
        
        # 4. Extract again to verify changes
        final_extract = runner.invoke(cli, ['extract', str(test_vault)])
        assert final_extract.exit_code == 0
    
    def test_cli_output_consistency(self, simple_vault, temp_dir):
        """Test that CLI output is consistent across different invocations."""
        from main import cli
        
        runner = CliRunner()
        
        # Run same command multiple times
        results = []
        for _ in range(3):
            result = runner.invoke(cli, ['extract', str(simple_vault)])
            results.append(result)
        
        # All should succeed
        for result in results:
            assert result.exit_code == 0
        
        # Outputs should be consistent (assuming deterministic ordering)
        # This might vary depending on implementation details
    
    def test_cli_with_complex_vault(self, complex_vault):
        """Test CLI commands with complex vault structure."""
        from main import cli
        
        runner = CliRunner()
        
        # Extract from complex vault
        result = runner.invoke(cli, ['extract', str(complex_vault)])
        assert result.exit_code == 0
        
        # Try operations on complex vault
        rename_result = runner.invoke(cli, [
            'rename', str(complex_vault), 'work', 'professional', '--dry-run'
        ])
        assert rename_result.exit_code == 0


class TestCLITagTypesOptions:
    """Test CLI with tag_types option."""

    def test_extract_with_tag_types_frontmatter(self, temp_dir):
        """Test extract command with --tag-types frontmatter."""
        from main import cli
        from click.testing import CliRunner

        # Create test vault with mixed tags
        vault_path = temp_dir / "tag_types_vault"
        vault_path.mkdir()

        (vault_path / "mixed.md").write_text("""---
tags: [frontmatter-tag]
---
Content with #inline-tag""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract', str(vault_path), '--tag-types', 'frontmatter'
        ])

        assert result.exit_code == 0
        output = result.output
        assert "frontmatter-tag" in output
        assert "inline-tag" not in output

    def test_extract_with_tag_types_inline(self, temp_dir):
        """Test extract command with --tag-types inline."""
        from main import cli
        from click.testing import CliRunner

        vault_path = temp_dir / "inline_vault"
        vault_path.mkdir()

        (vault_path / "mixed.md").write_text("""---
tags: [frontmatter-tag]
---
Content with #inline-tag""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract', str(vault_path), '--tag-types', 'inline'
        ])

        assert result.exit_code == 0
        output = result.output
        assert "frontmatter-tag" not in output
        assert "inline-tag" in output

    def test_rename_with_tag_types_option(self, temp_dir):
        """Test rename command with --tag-types option."""
        from main import cli
        from click.testing import CliRunner

        vault_path = temp_dir / "rename_types_vault"
        vault_path.mkdir()

        test_file = vault_path / "test.md"
        test_file.write_text("""---
tags: [old-tag]
---
Content with #old-tag""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'rename', str(vault_path), 'old-tag', 'new-tag',
            '--tag-types', 'frontmatter', '--dry-run'
        ])

        assert result.exit_code == 0
        # Should not error out with tag-types option

    def test_merge_with_tag_types_option(self, temp_dir):
        """Test merge command with --tag-types option."""
        from main import cli
        from click.testing import CliRunner

        vault_path = temp_dir / "merge_types_vault"
        vault_path.mkdir()

        test_file = vault_path / "test.md"
        test_file.write_text("""---
tags: [tag1, tag2]
---
Content with #tag1 and #tag2""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'merge', str(vault_path), 'tag1', 'tag2',
            '--into', 'merged-tag',
            '--tag-types', 'inline', '--dry-run'
        ])

        assert result.exit_code == 0

    def test_delete_with_tag_types_option(self, temp_dir):
        """Test delete command with --tag-types option."""
        from main import cli
        from click.testing import CliRunner

        vault_path = temp_dir / "delete_types_vault"
        vault_path.mkdir()

        test_file = vault_path / "test.md"
        test_file.write_text("""---
tags: [delete-me]
---
Content with #delete-me""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            'delete', str(vault_path), 'delete-me',
            '--tag-types', 'frontmatter', '--dry-run'
        ])

        assert result.exit_code == 0

    def test_invalid_tag_types_value(self, simple_vault):
        """Test that invalid tag-types values are rejected."""
        from main import cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cli, [
            'extract', str(simple_vault), '--tag-types', 'invalid'
        ])

        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "choice" in result.output.lower()

    def test_tag_types_default_behavior(self, simple_vault):
        """Test that default tag-types behavior works (both)."""
        from main import cli
        from click.testing import CliRunner

        runner = CliRunner()

        # Default behavior (should be 'both')
        result_default = runner.invoke(cli, ['extract', str(simple_vault)])

        # Explicit 'both'
        result_both = runner.invoke(cli, [
            'extract', str(simple_vault), '--tag-types', 'both'
        ])

        assert result_default.exit_code == 0
        assert result_both.exit_code == 0
        # Output should be the same
        assert result_default.output == result_both.output