"""
End-to-end workflow tests combining multiple components.

Tests complete user scenarios from vault processing to final output.
"""

import pytest
import json
import shutil
from pathlib import Path
from click.testing import CliRunner


class TestCompleteExtractionWorkflow:
    """Test complete tag extraction workflows."""
    
    def test_vault_to_json_pipeline(self, simple_vault, temp_dir):
        """Test complete pipeline from vault to JSON output."""
        from main import cli
        
        output_file = temp_dir / "complete_pipeline.json"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            str(simple_vault), 'extract',
            '--format', 'json',
            '--output', str(output_file),
            '--verbose'
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify each tag entry has expected structure
        for tag_entry in data:
            assert "tag" in tag_entry
            assert "tagCount" in tag_entry
            assert "relativePaths" in tag_entry
            assert isinstance(tag_entry["relativePaths"], list)
            assert tag_entry["tagCount"] > 0
        
        # Verify some expected tags from simple_vault fixture
        tag_names = {entry["tag"] for entry in data}
        assert "work" in tag_names  # Should be in multiple files
    
    def test_filtered_vs_unfiltered_extraction(self, complex_vault, temp_dir):
        """Test comparison between filtered and unfiltered extraction."""
        from main import cli
        
        filtered_output = temp_dir / "filtered.json"
        unfiltered_output = temp_dir / "unfiltered.json"
        
        runner = CliRunner()
        
        # Extract with filtering (default)
        filtered_result = runner.invoke(cli, [str(complex_vault), 'extract',
            '--output', str(filtered_output)
        ])
        
        # Extract without filtering
        unfiltered_result = runner.invoke(cli, [str(complex_vault), 'extract',
            '--no-filter',
            '--output', str(unfiltered_output)
        ])
        
        assert filtered_result.exit_code == 0
        assert unfiltered_result.exit_code == 0
        
        # Load both results
        with open(filtered_output) as f:
            filtered_data = json.load(f)
        with open(unfiltered_output) as f:
            unfiltered_data = json.load(f)
        
        filtered_tags = {entry["tag"] for entry in filtered_data}
        unfiltered_tags = {entry["tag"] for entry in unfiltered_data}
        
        # Filtered should be subset of unfiltered
        assert filtered_tags.issubset(unfiltered_tags)
        
        # Unfiltered should have more or equal number of tags
        assert len(unfiltered_tags) >= len(filtered_tags)
        
        # Check that obvious invalid tags are filtered out
        invalid_patterns = ["123", "_underscore"]
        for pattern in invalid_patterns:
            if pattern in unfiltered_tags:
                assert pattern not in filtered_tags
    
    def test_extraction_with_exclusion_patterns(self, complex_vault, temp_dir):
        """Test extraction workflow with file exclusion patterns."""
        from main import cli
        
        # Extract all files
        all_output = temp_dir / "all_files.json"
        runner = CliRunner()
        all_result = runner.invoke(cli, [str(complex_vault), 'extract',
            '--output', str(all_output)
        ])
        
        # Extract excluding templates
        excluded_output = temp_dir / "excluded_templates.json"
        excluded_result = runner.invoke(cli, [str(complex_vault), 'extract',
            '--exclude', '*.template.md',
            '--exclude', 'templates/*',
            '--output', str(excluded_output)
        ])
        
        assert all_result.exit_code == 0
        assert excluded_result.exit_code == 0
        
        # Load results
        with open(excluded_output) as f:
            excluded_data = json.load(f)
        
        # Check that template-related files are not in the results
        all_files = []
        for entry in excluded_data:
            all_files.extend(entry["relativePaths"])
        
        template_files = [f for f in all_files if "template" in f.lower()]
        assert len(template_files) == 0
    
    def test_multiple_output_formats_workflow(self, simple_vault, temp_dir):
        """Test generating multiple output formats from same vault."""
        from main import cli
        
        json_output = temp_dir / "tags.json"
        csv_output = temp_dir / "tags.csv"
        
        runner = CliRunner()
        
        # Generate JSON output
        json_result = runner.invoke(cli, [str(simple_vault), 'extract',
            '--format', 'json',
            '--output', str(json_output)
        ])
        
        # Generate CSV output
        csv_result = runner.invoke(cli, [str(simple_vault), 'extract',
            '--format', 'csv',
            '--output', str(csv_output)
        ])
        
        assert json_result.exit_code == 0
        assert csv_result.exit_code == 0
        assert json_output.exists()
        assert csv_output.exists()
        
        # Verify JSON format
        with open(json_output) as f:
            json_data = json.load(f)
        assert isinstance(json_data, list)
        
        # Verify CSV format
        csv_content = csv_output.read_text()
        lines = csv_content.strip().split('\n')
        assert len(lines) > 1  # Header + data
        assert "tag" in lines[0].lower()
        assert "count" in lines[0].lower()
        
        # Both should contain similar tag information
        json_tags = {entry["tag"] for entry in json_data}
        csv_tags = set()
        for line in lines[1:]:  # Skip header
            if line.strip():
                tag = line.split(',')[0].strip('"')
                csv_tags.add(tag)
        
        # Should have significant overlap
        common_tags = json_tags.intersection(csv_tags)
        assert len(common_tags) > 0


class TestTagOperationWorkflows:
    """Test complete tag operation workflows."""
    
    def test_rename_workflow_with_verification(self, temp_dir):
        """Test complete rename workflow with before/after verification."""
        from main import cli
        
        # Create test vault
        test_vault = temp_dir / "rename_workflow_vault"
        test_vault.mkdir()
        
        (test_vault / "file1.md").write_text("""---
tags: [work, project, notes]
---

# Work File

Content with #work and #project tags.""")
        
        (test_vault / "file2.md").write_text("""---
tags: [personal, work]
---

Personal notes with some #work references.""")
        
        runner = CliRunner()
        
        # 1. Extract initial state
        initial_output = temp_dir / "before_rename.json"
        initial_result = runner.invoke(cli, [str(test_vault), 'extract',
            '--output', str(initial_output)
        ])
        assert initial_result.exit_code == 0
        
        # 2. Preview rename operation
        dry_run_result = runner.invoke(cli, [str(test_vault), 'rename', 'work', 'professional', '--dry-run'
        ])
        assert dry_run_result.exit_code == 0
        
        # Files should be unchanged after dry run
        file1_content_before = (test_vault / "file1.md").read_text()
        assert "work" in file1_content_before
        assert "professional" not in file1_content_before
        
        # 3. Execute actual rename
        rename_result = runner.invoke(cli, [str(test_vault), 'rename', 'work', 'professional'
        ])
        assert rename_result.exit_code == 0
        
        # 4. Verify files were changed
        file1_content_after = (test_vault / "file1.md").read_text()
        file2_content_after = (test_vault / "file2.md").read_text()
        
        # Should contain new tag name
        assert "professional" in file1_content_after or "professional" in file2_content_after
        
        # 5. Extract final state
        final_output = temp_dir / "after_rename.json"
        final_result = runner.invoke(cli, [str(test_vault), 'extract',
            '--output', str(final_output)
        ])
        assert final_result.exit_code == 0
        
        # 6. Compare before and after
        with open(initial_output) as f:
            initial_data = json.load(f)
        with open(final_output) as f:
            final_data = json.load(f)
        
        initial_tags = {entry["tag"] for entry in initial_data}
        final_tags = {entry["tag"] for entry in final_data}
        
        # Should have the new tag
        assert "professional" in final_tags
    
    def test_merge_workflow_with_verification(self, temp_dir):
        """Test complete merge workflow with verification."""
        from main import cli
        
        # Create test vault with mergeable tags
        test_vault = temp_dir / "merge_workflow_vault"
        test_vault.mkdir()
        
        (test_vault / "ideas1.md").write_text("""---
tags: [ideas, brainstorming, creativity]
---

# Ideas File 1

Content with #thoughts and #innovation.""")
        
        (test_vault / "ideas2.md").write_text("""---
tags: [thoughts, brainstorming, personal]
---

# Ideas File 2

More content with #ideas.""")
        
        (test_vault / "other.md").write_text("""---
tags: [work, reference]
---

# Other File

Content with different tags.""")
        
        runner = CliRunner()
        
        # 1. Extract initial state
        initial_output = temp_dir / "before_merge.json"
        initial_result = runner.invoke(cli, [str(test_vault), 'extract',
            '--output', str(initial_output)
        ])
        assert initial_result.exit_code == 0
        
        # 2. Preview merge operation
        dry_run_result = runner.invoke(cli, [str(test_vault), 'merge',
            'ideas', 'thoughts', 'brainstorming',
            '--into', 'thinking',
            '--dry-run'
        ])
        assert dry_run_result.exit_code == 0
        
        # 3. Execute actual merge
        merge_result = runner.invoke(cli, [str(test_vault), 'merge',
            'ideas', 'thoughts', 'brainstorming',
            '--into', 'thinking'
        ])
        assert merge_result.exit_code == 0
        
        # 4. Extract final state
        final_output = temp_dir / "after_merge.json"
        final_result = runner.invoke(cli, [str(test_vault), 'extract',
            '--output', str(final_output)
        ])
        assert final_result.exit_code == 0
        
        # 5. Verify merge results
        with open(final_output) as f:
            final_data = json.load(f)
        
        final_tags = {entry["tag"] for entry in final_data}
        
        # Should have the merged tag
        assert "thinking" in final_tags
        
        # Check that unrelated tags are preserved
        assert "work" in final_tags
        assert "reference" in final_tags
        assert "personal" in final_tags
        assert "creativity" in final_tags
    
    def test_sequential_operations_workflow(self, temp_dir):
        """Test performing multiple operations in sequence."""
        from main import cli
        
        # Create test vault
        test_vault = temp_dir / "sequential_ops_vault"
        test_vault.mkdir()
        
        (test_vault / "multi_ops.md").write_text("""---
tags: [old-work, old-notes, ideas, brainstorming]
---

# Multi Operations File

Content with #old-work #thoughts and #creativity tags.""")
        
        runner = CliRunner()
        
        # 1. First operation: rename old-work to work
        rename1_result = runner.invoke(cli, [str(test_vault), 'rename', 'old-work', 'work'
        ])
        assert rename1_result.exit_code == 0
        
        # 2. Second operation: rename old-notes to notes
        rename2_result = runner.invoke(cli, [str(test_vault), 'rename', 'old-notes', 'notes'
        ])
        assert rename2_result.exit_code == 0
        
        # 3. Third operation: merge thinking-related tags
        merge_result = runner.invoke(cli, [str(test_vault), 'merge',
            'ideas', 'brainstorming', 'thoughts', 'creativity',
            '--into', 'thinking'
        ])
        assert merge_result.exit_code == 0
        
        # 4. Verify final state
        final_output = temp_dir / "sequential_final.json"
        final_result = runner.invoke(cli, [str(test_vault), 'extract',
            '--output', str(final_output)
        ])
        assert final_result.exit_code == 0
        
        # Check results
        with open(final_output) as f:
            final_data = json.load(f)
        
        final_tags = {entry["tag"] for entry in final_data}
        
        # Should have renamed tags
        assert "work" in final_tags
        assert "notes" in final_tags
        assert "thinking" in final_tags
        
        # Should not have old tags
        assert "old-work" not in final_tags
        assert "old-notes" not in final_tags


class TestRealWorldScenarios:
    """Test realistic user scenarios."""
    
    def test_large_vault_processing(self, temp_dir):
        """Test processing a larger, more realistic vault."""
        from main import cli
        
        # Create a larger test vault
        large_vault = temp_dir / "large_vault"
        large_vault.mkdir()
        
        # Create multiple directories
        (large_vault / "projects").mkdir()
        (large_vault / "notes").mkdir()
        (large_vault / "archive").mkdir()
        
        # Create many files with various tag patterns
        file_templates = [
            ("projects/project1.md", ["work", "project", "development"]),
            ("projects/project2.md", ["work", "project", "research"]),
            ("notes/meeting1.md", ["work", "meetings", "notes"]),
            ("notes/meeting2.md", ["work", "meetings", "decisions"]),
            ("notes/personal.md", ["personal", "journal", "thoughts"]),
            ("archive/old_project.md", ["archive", "old-work", "completed"]),
        ]
        
        for filepath, tags in file_templates:
            file_path = large_vault / filepath
            file_path.write_text(f"""---
tags: {tags}
created: 2024-01-15
---

# {file_path.stem.title()}

Content for {file_path.stem} with various inline tags like #work and #notes.

## Details

More detailed content with #project-related information.
""")
        
        runner = CliRunner()
        
        # Extract from large vault
        output_file = temp_dir / "large_vault_extract.json"
        extract_result = runner.invoke(cli, [str(large_vault), 'extract',
            '--output', str(output_file),
            '--verbose'
        ])
        
        assert extract_result.exit_code == 0
        assert output_file.exists()
        
        # Verify extraction results
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data) > 0
        
        # Should have found tags from multiple files
        tag_names = {entry["tag"] for entry in data}
        assert "work" in tag_names
        assert "project" in tag_names
        assert "notes" in tag_names
        
        # Check tag counts make sense
        work_entry = next(entry for entry in data if entry["tag"] == "work")
        assert work_entry["tagCount"] > 1  # Should appear in multiple files
    
    def test_vault_cleanup_workflow(self, temp_dir):
        """Test a realistic vault cleanup scenario."""
        from main import cli
        
        # Create vault that needs cleanup
        messy_vault = temp_dir / "messy_vault"
        messy_vault.mkdir()
        
        # Files with inconsistent tagging
        (messy_vault / "file1.md").write_text("""---
tags: [work-project, work_project, "work project"]
---

Content with #work-related stuff.""")
        
        (messy_vault / "file2.md").write_text("""---
tags: [meeting-notes, meeting_notes, meetings]
---

Content with #meeting information.""")
        
        runner = CliRunner()
        
        # 1. Analyze current state
        initial_analysis = temp_dir / "messy_initial.json"
        runner.invoke(cli, [str(messy_vault), 'extract',
            '--output', str(initial_analysis)
        ])
        
        # 2. Standardize work-related tags
        runner.invoke(cli, [str(messy_vault), 'rename', 'work_project', 'work-project'
        ])
        
        runner.invoke(cli, [str(messy_vault), 'rename', 'work project', 'work-project'
        ])
        
        # 3. Merge meeting-related tags
        runner.invoke(cli, [str(messy_vault), 'merge',
            'meeting-notes', 'meeting_notes', 'meetings',
            '--into', 'meetings'
        ])
        
        # 4. Analyze final state
        final_analysis = temp_dir / "messy_final.json"
        final_result = runner.invoke(cli, [str(messy_vault), 'extract',
            '--output', str(final_analysis)
        ])
        
        assert final_result.exit_code == 0
        
        # Verify cleanup worked
        with open(final_analysis) as f:
            final_data = json.load(f)
        
        final_tags = {entry["tag"] for entry in final_data}
        
        # Should have standardized tags
        assert "work-project" in final_tags
        assert "meetings" in final_tags
        
        # Should not have variations
        assert "work_project" not in final_tags
        assert "work project" not in final_tags
        assert "meeting-notes" not in final_tags
        assert "meeting_notes" not in final_tags
    
    def test_error_recovery_workflow(self, temp_dir):
        """Test workflow handles errors gracefully and continues processing."""
        from main import cli
        
        # Create vault with problematic files
        error_vault = temp_dir / "error_vault"
        error_vault.mkdir()
        
        # Good file
        (error_vault / "good.md").write_text("""---
tags: [good, working]
---

# Good File

Normal content.""")
        
        # File with malformed YAML
        (error_vault / "malformed.md").write_text("""---
tags: [broken, yaml
malformed: content
---

# Malformed File""")
        
        # Empty file
        (error_vault / "empty.md").write_text("")
        
        # Binary file disguised as markdown
        (error_vault / "binary.md").write_bytes(b'\x00\x01\x02\x03binary')
        
        runner = CliRunner()
        
        # Should process successfully despite errors
        output_file = temp_dir / "error_recovery.json"
        result = runner.invoke(cli, [str(error_vault), 'extract',
            '--output', str(output_file),
            '--verbose'
        ])
        
        # Should succeed (even if some files caused errors)
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Should have extracted tags from good files
        with open(output_file) as f:
            data = json.load(f)
        
        # Should have tags from the good file
        tag_names = {entry["tag"] for entry in data}
        assert "good" in tag_names
        assert "working" in tag_names


class TestPerformanceAndScalability:
    """Test performance with larger datasets."""
    
    def test_many_files_workflow(self, temp_dir):
        """Test processing vault with many files."""
        from main import cli
        
        # Create vault with many small files
        many_files_vault = temp_dir / "many_files_vault"
        many_files_vault.mkdir()
        
        # Create 50 small files
        for i in range(50):
            file_content = f"""---
tags: [file-{i}, batch-{i//10}, test]
---

# File {i}

Content for file number {i} with #test-tag-{i}.
"""
            (many_files_vault / f"file_{i:03d}.md").write_text(file_content)
        
        runner = CliRunner()
        
        # Extract should handle many files
        output_file = temp_dir / "many_files_output.json"
        result = runner.invoke(cli, [str(many_files_vault), 'extract',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify results
        with open(output_file) as f:
            data = json.load(f)
        
        # Should have many tags
        assert len(data) > 50  # Each file adds multiple tags
        
        # Common tags should have high counts
        test_tag = next(entry for entry in data if entry["tag"] == "test")
        assert test_tag["tagCount"] == 50  # Should be in all files
    
    def test_large_files_workflow(self, temp_dir):
        """Test processing vault with large files."""
        from main import cli
        
        large_files_vault = temp_dir / "large_files_vault"
        large_files_vault.mkdir()
        
        # Create a few large files
        large_content = """---
tags: [large-file, content, test]
---

# Large File

""" + ("This is a large file with repeated content.\n" * 1000) + """

## More Content

With additional #large-content tags and #test-references throughout.

""" + ("More repeated content with #inline-tags.\n" * 500)
        
        for i in range(3):
            (large_files_vault / f"large_{i}.md").write_text(large_content)
        
        runner = CliRunner()
        
        # Should handle large files
        output_file = temp_dir / "large_files_output.json"
        result = runner.invoke(cli, [str(large_files_vault), 'extract',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify processing worked correctly
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data) > 0
        
        # Tags from large files should be properly counted
        large_file_tag = next(entry for entry in data if entry["tag"] == "large-file")
        assert large_file_tag["tagCount"] == 3  # Should be in all 3 files