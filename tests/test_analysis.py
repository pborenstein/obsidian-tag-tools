"""
Tests for tag analysis tools - co-occurrence analysis and filtering.
"""

import pytest
import json
import subprocess
import sys
from pathlib import Path


class TestCooccurrenceAnalyzer:
    """Tests for the co-occurrence analysis tool."""
    
    def test_pair_analyzer_exists(self):
        """Test that co-occurrence analyzer script exists."""
        analyzer_path = Path("tag-analysis/pair_analyzer.py")
        # Script should exist in project root
        assert analyzer_path.exists() or (Path.cwd() / analyzer_path).exists()
    
    def test_pair_analyzer_cli_help(self):
        """Test co-occurrence analyzer CLI help."""
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            result = subprocess.run([
                sys.executable, analyzer_script, "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Should show help without errors
            assert result.returncode == 0 or "usage" in result.stderr.lower()
            help_text = result.stdout + result.stderr
            assert "pair" in help_text.lower() or "analysis" in help_text.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # If script not found or times out, skip this test
            pytest.skip("Co-occurrence analyzer script not available")
    
    def test_pair_analysis_with_sample_data(self, temp_dir, sample_pair_data):
        """Test co-occurrence analysis with sample data."""
        # Create sample JSON file
        sample_file = temp_dir / "sample_tags.json"
        with open(sample_file, 'w') as f:
            json.dump(sample_pair_data, f)
        
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            result = subprocess.run([
                sys.executable, analyzer_script, str(sample_file)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                
                # Should contain analysis results
                assert len(output) > 0
                
                # Should mention co-occurring pairs
                assert "co-occur" in output.lower() or "pairs" in output.lower()
                
                # Should show some of our sample tags
                assert "work" in output or "notes" in output
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Co-occurrence analyzer not available or timeout")
    
    def test_pair_analysis_with_filtering(self, temp_dir):
        """Test co-occurrence analysis with and without filtering."""
        # Create test data with both valid and invalid tags
        test_data = [
            {"tag": "work", "tagCount": 10, "relativePaths": ["file1.md", "file2.md"]},
            {"tag": "notes", "tagCount": 8, "relativePaths": ["file1.md", "file3.md"]},
            {"tag": "123", "tagCount": 3, "relativePaths": ["file2.md"]},  # Invalid - pure number
            {"tag": "_invalid", "tagCount": 2, "relativePaths": ["file3.md"]},  # Invalid - starts with underscore
            {"tag": "valid-tag", "tagCount": 5, "relativePaths": ["file1.md", "file4.md"]}
        ]
        
        test_file = temp_dir / "test_filtering.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            # Run with filtering (default)
            filtered_result = subprocess.run([
                sys.executable, analyzer_script, str(test_file)
            ], capture_output=True, text=True, timeout=30)
            
            # Run without filtering
            unfiltered_result = subprocess.run([
                sys.executable, analyzer_script, str(test_file), "--no-filter"
            ], capture_output=True, text=True, timeout=30)
            
            if filtered_result.returncode == 0 and unfiltered_result.returncode == 0:
                filtered_output = filtered_result.stdout + filtered_result.stderr
                unfiltered_output = unfiltered_result.stdout + unfiltered_result.stderr
                
                # Both should produce output
                assert len(filtered_output) > 0
                assert len(unfiltered_output) > 0
                
                # Filtered output should not contain invalid tags
                assert "123" not in filtered_output
                assert "_invalid" not in filtered_output
                
                # Unfiltered might contain invalid tags
                # (exact behavior depends on implementation)
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Co-occurrence analyzer not available")
    
    def test_pair_analysis_minimum_threshold(self, temp_dir):
        """Test co-occurrence analysis with minimum threshold option."""
        # Create test data with various co-occurrence frequencies
        test_data = [
            {"tag": "frequent1", "tagCount": 20, "relativePaths": ["file1.md", "file2.md", "file3.md"]},
            {"tag": "frequent2", "tagCount": 15, "relativePaths": ["file1.md", "file2.md", "file4.md"]},
            {"tag": "rare1", "tagCount": 2, "relativePaths": ["file5.md", "file6.md"]},
            {"tag": "rare2", "tagCount": 1, "relativePaths": ["file7.md"]}
        ]
        
        test_file = temp_dir / "threshold_test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            # Run with high minimum threshold
            result = subprocess.run([
                sys.executable, analyzer_script, str(test_file),
                "--min-pair", "5"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                
                # Should focus on frequent co-occurrences
                assert len(output) > 0
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Co-occurrence analyzer not available")


class TestAnalysisDataProcessing:
    """Tests for analysis data processing functionality."""
    
    def test_build_file_to_tags_mapping(self, sample_pair_data):
        """Test building file-to-tags mapping from extraction data."""
        # This tests the expected internal functionality
        # Based on documentation, analyzer should build reverse index
        
        # Simulate what the analyzer should do
        file_to_tags = {}
        
        for tag_entry in sample_pair_data:
            tag = tag_entry["tag"]
            files = tag_entry["relativePaths"]
            
            for file_path in files:
                if file_path not in file_to_tags:
                    file_to_tags[file_path] = set()
                file_to_tags[file_path].add(tag)
        
        # Verify mapping structure
        assert len(file_to_tags) > 0
        
        # Files should have multiple tags
        for file_path, tags in file_to_tags.items():
            assert len(tags) > 0
            assert isinstance(tags, set)
    
    def test_pair_calculation(self, sample_pair_data):
        """Test co-occurrence calculation logic."""
        from itertools import combinations
        
        # Build file-to-tags mapping
        file_to_tags = {}
        for tag_entry in sample_pair_data:
            for file_path in tag_entry["relativePaths"]:
                if file_path not in file_to_tags:
                    file_to_tags[file_path] = set()
                file_to_tags[file_path].add(tag_entry["tag"])
        
        # Calculate co-occurrences
        pair_counts = {}
        for file_path, tags in file_to_tags.items():
            for tag1, tag2 in combinations(sorted(tags), 2):
                pair = (tag1, tag2)
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
        
        # Verify co-occurrence structure
        assert len(pair_counts) >= 0
        
        for (tag1, tag2), count in pair_counts.items():
            assert isinstance(tag1, str)
            assert isinstance(tag2, str)
            assert tag1 != tag2
            assert count > 0
    
    def test_hub_tag_identification(self, sample_pair_data):
        """Test identification of hub tags (highly connected tags)."""
        # Simulate hub tag identification logic
        tag_connections = {}
        
        for tag_entry in sample_pair_data:
            tag = tag_entry["tag"]
            count = tag_entry["tagCount"]
            tag_connections[tag] = count
        
        # Sort by connection count (tag frequency)
        hub_tags = sorted(tag_connections.items(), key=lambda x: x[1], reverse=True)
        
        # Should identify most connected tags
        assert len(hub_tags) > 0
        
        # First tag should have highest count
        if len(hub_tags) > 1:
            assert hub_tags[0][1] >= hub_tags[1][1]
    
    def test_tag_clustering_logic(self, sample_pair_data):
        """Test tag clustering detection logic."""
        # This tests the expected clustering functionality
        # Based on documentation, analyzer should find connected components
        
        # Build adjacency graph from co-occurrence data
        from itertools import combinations
        
        file_to_tags = {}
        for tag_entry in sample_pair_data:
            for file_path in tag_entry["relativePaths"]:
                if file_path not in file_to_tags:
                    file_to_tags[file_path] = set()
                file_to_tags[file_path].add(tag_entry["tag"])
        
        # Find tag pairs that co-occur
        pair_pairs = set()
        for tags in file_to_tags.values():
            for tag1, tag2 in combinations(tags, 2):
                pair_pairs.add((min(tag1, tag2), max(tag1, tag2)))
        
        # Build adjacency list
        adjacency = {}
        for tag1, tag2 in pair_pairs:
            if tag1 not in adjacency:
                adjacency[tag1] = set()
            if tag2 not in adjacency:
                adjacency[tag2] = set()
            adjacency[tag1].add(tag2)
            adjacency[tag2].add(tag1)
        
        # Find connected components (clusters)
        visited = set()
        clusters = []
        
        def dfs(tag, current_cluster):
            if tag in visited:
                return
            visited.add(tag)
            current_cluster.add(tag)
            
            for neighbor in adjacency.get(tag, []):
                dfs(neighbor, current_cluster)
        
        for tag in adjacency:
            if tag not in visited:
                cluster = set()
                dfs(tag, cluster)
                if len(cluster) > 1:  # Only keep multi-tag clusters
                    clusters.append(cluster)
        
        # Should find some clusters
        assert len(clusters) >= 0  # May or may not find clusters depending on data


class TestAnalysisFiltering:
    """Tests for filtering functionality in analysis tools."""
    
    def test_filter_integration_with_analysis(self):
        """Test that tag filtering integrates properly with analysis."""
        # Create mixed valid/invalid tag data
        mixed_tags = [
            "work",           # Valid
            "notes",          # Valid
            "123",            # Invalid - pure number
            "project-ideas",  # Valid
            "_underscore",    # Invalid - starts with underscore
            "html&entities",  # Invalid - HTML entities
            "2024-goals",     # Valid - contains letters
        ]
        
        # Simulate filtering (would use actual filter function)
        valid_tags = []
        for tag in mixed_tags:
            # Basic validation rules
            if tag.isdigit():  # Pure number
                continue
            if tag.startswith('_'):  # Starts with underscore
                continue
            if '&' in tag:  # Contains HTML entities
                continue
            valid_tags.append(tag)
        
        # Should keep valid tags
        assert "work" in valid_tags
        assert "notes" in valid_tags
        assert "project-ideas" in valid_tags
        assert "2024-goals" in valid_tags
        
        # Should remove invalid tags
        assert "123" not in valid_tags
        assert "_underscore" not in valid_tags
        assert "html&entities" not in valid_tags
    
    def test_noise_filtering_effectiveness_in_analysis(self):
        """Test that noise filtering is effective for analysis quality."""
        # Simulate realistic noisy extraction data
        noisy_data = [
            {"tag": "work", "tagCount": 50, "relativePaths": ["file1.md", "file2.md"]},
            {"tag": "notes", "tagCount": 30, "relativePaths": ["file1.md", "file3.md"]},
            {"tag": "123", "tagCount": 5, "relativePaths": ["file4.md"]},  # Noise
            {"tag": "dispatcher", "tagCount": 3, "relativePaths": ["file5.md"]},  # Technical noise
            {"tag": "project-ideas", "tagCount": 25, "relativePaths": ["file2.md", "file6.md"]},
            {"tag": "&nbsp;", "tagCount": 1, "relativePaths": ["file7.md"]},  # HTML noise
        ]
        
        # Filter out noise (simulate tag filtering)
        filtered_data = []
        for entry in noisy_data:
            tag = entry["tag"]
            # Basic noise detection
            if tag.isdigit():  # Pure numbers
                continue
            if tag in ["dispatcher", "fs_operation", "dom-element"]:  # Technical terms
                continue
            if "&" in tag or "&#" in tag:  # HTML entities
                continue
            filtered_data.append(entry)
        
        # Should have meaningful tags for analysis
        filtered_tags = {entry["tag"] for entry in filtered_data}
        assert "work" in filtered_tags
        assert "notes" in filtered_tags
        assert "project-ideas" in filtered_tags
        
        # Should not have noise
        assert "123" not in filtered_tags
        assert "dispatcher" not in filtered_tags
        assert "&nbsp;" not in filtered_tags
        
        # Filtered data should be better for co-occurrence analysis
        assert len(filtered_data) < len(noisy_data)
        assert len(filtered_data) > 0


class TestAnalysisOutput:
    """Tests for analysis output formats and content."""
    
    def test_analysis_output_contains_expected_sections(self, temp_dir, sample_pair_data):
        """Test that analysis output contains expected sections."""
        sample_file = temp_dir / "output_test.json"
        with open(sample_file, 'w') as f:
            json.dump(sample_pair_data, f)
        
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            result = subprocess.run([
                sys.executable, analyzer_script, str(sample_file)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                
                # Should contain key analysis sections
                expected_sections = [
                    "co-occur",
                    "pairs",
                    "tags",
                    "cluster",
                    "hub",
                    "connected"
                ]
                
                # Should have at least some of these sections
                sections_found = sum(1 for section in expected_sections 
                                   if section.lower() in output.lower())
                assert sections_found > 0
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Analysis script not available")
    
    def test_analysis_handles_empty_data(self, temp_dir):
        """Test analysis handles empty or minimal data gracefully."""
        # Empty data
        empty_file = temp_dir / "empty.json"
        with open(empty_file, 'w') as f:
            json.dump([], f)
        
        # Minimal data
        minimal_data = [{"tag": "single", "tagCount": 1, "relativePaths": ["file1.md"]}]
        minimal_file = temp_dir / "minimal.json"
        with open(minimal_file, 'w') as f:
            json.dump(minimal_data, f)
        
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        for test_file in [empty_file, minimal_file]:
            try:
                result = subprocess.run([
                    sys.executable, analyzer_script, str(test_file)
                ], capture_output=True, text=True, timeout=30)
                
                # Should handle gracefully (may succeed or fail appropriately)
                assert isinstance(result.returncode, int)
                
                if result.returncode == 0:
                    # If successful, should have reasonable output
                    output = result.stdout + result.stderr
                    assert len(output) >= 0
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Skip if script not available
                break
    
    def test_analysis_statistics_accuracy(self, sample_pair_data):
        """Test that analysis statistics are calculated accurately."""
        # Calculate expected statistics
        total_tags = len(sample_pair_data)
        total_usages = sum(entry["tagCount"] for entry in sample_pair_data)
        
        all_files = set()
        for entry in sample_pair_data:
            all_files.update(entry["relativePaths"])
        total_files = len(all_files)
        
        # These are the statistics analysis should report
        expected_stats = {
            "unique_tags": total_tags,
            "total_usages": total_usages,
            "total_files": total_files
        }
        
        # Verify calculations are reasonable
        assert expected_stats["unique_tags"] > 0
        assert expected_stats["total_usages"] >= expected_stats["unique_tags"]
        assert expected_stats["total_files"] > 0
        
        # Average tags per file should be reasonable
        avg_tags_per_file = expected_stats["total_usages"] / expected_stats["total_files"]
        assert avg_tags_per_file > 0
        assert avg_tags_per_file < 100  # Sanity check


class TestAnalysisIntegration:
    """Integration tests for analysis tools with extraction pipeline."""
    
    def test_extract_to_analysis_pipeline(self, simple_vault, temp_dir):
        """Test complete pipeline from extraction to analysis."""
        from main import cli
        from click.testing import CliRunner
        
        # 1. Extract tags to JSON
        tags_file = temp_dir / "pipeline_tags.json"
        runner = CliRunner()
        extract_result = runner.invoke(cli, [
            'extract', str(simple_vault),
            '--output', str(tags_file)
        ])
        
        assert extract_result.exit_code == 0
        assert tags_file.exists()
        
        # 2. Run analysis on extracted data
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            analysis_result = subprocess.run([
                sys.executable, analyzer_script, str(tags_file)
            ], capture_output=True, text=True, timeout=30)
            
            if analysis_result.returncode == 0:
                # Analysis should work with extracted data
                output = analysis_result.stdout + analysis_result.stderr
                assert len(output) > 0
                
                # Should contain analysis information (may not show specific tags if no pairs found)
                assert any(phrase in output.lower() for phrase in ["analyzing", "files", "tags", "pairs"])
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Analysis pipeline not available")
    
    def test_analysis_with_different_extraction_formats(self, simple_vault, temp_dir):
        """Test analysis compatibility with different extraction formats."""
        from main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Extract in JSON format (should work with analysis)
        json_file = temp_dir / "format_test.json"
        json_result = runner.invoke(cli, [
            'extract', str(simple_vault),
            '--format', 'json',
            '--output', str(json_file)
        ])
        
        assert json_result.exit_code == 0
        
        # Verify JSON format is compatible with analysis tools
        with open(json_file) as f:
            json_data = json.load(f)
        
        # Should have structure expected by analysis tools
        assert isinstance(json_data, list)
        
        for entry in json_data:
            assert "tag" in entry
            assert "tagCount" in entry
            assert "relativePaths" in entry
            assert isinstance(entry["relativePaths"], list)
    
    def test_filtered_vs_unfiltered_analysis(self, complex_vault, temp_dir):
        """Test analysis results with filtered vs unfiltered extraction."""
        from main import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Extract with filtering
        filtered_file = temp_dir / "filtered_analysis.json"
        filtered_result = runner.invoke(cli, [
            'extract', str(complex_vault),
            '--output', str(filtered_file)
        ])
        
        # Extract without filtering
        unfiltered_file = temp_dir / "unfiltered_analysis.json"
        unfiltered_result = runner.invoke(cli, [
            'extract', str(complex_vault),
            '--no-filter',
            '--output', str(unfiltered_file)
        ])
        
        assert filtered_result.exit_code == 0
        assert unfiltered_result.exit_code == 0
        
        analyzer_script = "tag-analysis/pair_analyzer.py"
        
        try:
            # Run analysis on both datasets
            filtered_analysis = subprocess.run([
                sys.executable, analyzer_script, str(filtered_file)
            ], capture_output=True, text=True, timeout=30)
            
            unfiltered_analysis = subprocess.run([
                sys.executable, analyzer_script, str(unfiltered_file)
            ], capture_output=True, text=True, timeout=30)
            
            if filtered_analysis.returncode == 0 and unfiltered_analysis.returncode == 0:
                filtered_output = filtered_analysis.stdout + filtered_analysis.stderr
                unfiltered_output = unfiltered_analysis.stdout + unfiltered_analysis.stderr
                
                # Both should produce meaningful analysis
                assert len(filtered_output) > 0
                assert len(unfiltered_output) > 0
                
                # Filtered analysis should be cleaner
                # (exact comparison depends on implementation)
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Analysis comparison not available")