"""
Unified recommendations system for tag operations.

This module consolidates recommendations from all analyzers into a single,
actionable operations file that can be reviewed and applied.
"""

from typing import Dict, List, Any, Set
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import yaml

from .synonym_analyzer import detect_synonyms_by_semantics, find_acronym_expansions
from .plural_normalizer import normalize_plural_forms, normalize_compound_plurals, get_preferred_form
from .singleton_analyzer import SingletonAnalyzer
from ..config.plural_config import PluralConfig
from ..config.exclusions_config import ExclusionsConfig
from ..config.synonym_config import SynonymConfig


class Operation:
    """Represents a single tag operation recommendation."""

    def __init__(
        self,
        operation_type: str,
        source_tags: List[str],
        target_tag: str,
        reason: str,
        enabled: bool = True,
        confidence: float = 0.0,
        source_analyzer: str = "",
        metadata: Dict[str, Any] = None
    ):
        self.operation_type = operation_type
        self.source_tags = source_tags
        self.target_tag = target_tag
        self.reason = reason
        self.enabled = enabled
        self.confidence = confidence
        self.source_analyzer = source_analyzer
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary for YAML export."""
        return {
            'type': self.operation_type,
            'source': self.source_tags,
            'target': self.target_tag,
            'reason': self.reason,
            'enabled': self.enabled,
            'metadata': {
                'confidence': round(self.confidence, 3),
                'source_analyzer': self.source_analyzer,
                **self.metadata
            }
        }


class RecommendationsEngine:
    """Runs all analyzers and consolidates recommendations."""

    def __init__(
        self,
        tag_stats: Dict[str, Dict[str, Any]],
        vault_path: str = None,
        analyzers: List[str] = None
    ):
        self.tag_stats = tag_stats
        self.vault_path = vault_path
        self.analyzers = analyzers or ['synonyms', 'plurals']
        self.operations: List[Operation] = []
        self.config = PluralConfig.from_vault(vault_path) if vault_path else PluralConfig()
        self.exclusions = ExclusionsConfig(Path(vault_path) if vault_path else None)
        self.synonym_config = SynonymConfig(Path(vault_path) if vault_path else None)

    def run_all_analyzers(self, min_similarity: float = 0.7, no_transformers: bool = False) -> List[Operation]:
        """Run all enabled analyzers and collect operations."""
        self.operations = []

        # Run user-defined synonyms FIRST (highest priority)
        self._run_user_synonyms()

        # Run analyzers in priority order
        if 'synonyms' in self.analyzers and not no_transformers:
            self._run_synonyms_analyzer(min_similarity)

        if 'plurals' in self.analyzers:
            self._run_plurals_analyzer()

        if 'singletons' in self.analyzers:
            self._run_singletons_analyzer(no_transformers)

        # Deduplicate operations
        self.operations = self._deduplicate_operations(self.operations)

        # Filter out operations that conflict with user-defined synonyms
        self.operations = self._filter_synonym_conflicts(self.operations)

        # Filter out excluded tags
        self.operations = self._filter_exclusions(self.operations)

        return self.operations

    def _run_user_synonyms(self):
        """Process user-defined synonyms from synonyms.yaml."""
        if not self.synonym_config.has_synonyms():
            return

        print("  Processing user-defined synonyms...")

        # Get all synonym groups
        for group in self.synonym_config.get_all_groups():
            if len(group) < 2:
                continue

            canonical = group[0]
            variants = group[1:]

            # Only suggest operations for tags that exist in the vault
            existing_variants = [v for v in variants if v in self.tag_stats]
            if not existing_variants:
                continue

            # Note: We DON'T require canonical to exist - merging variants will create it

            # Create single operation with all variants → canonical
            operation = Operation(
                operation_type='merge',
                source_tags=existing_variants,
                target_tag=canonical,
                reason=f"User-defined synonym",
                enabled=True,
                confidence=1.0,  # Highest confidence - user defined
                source_analyzer='user-synonyms',
                metadata={}
            )
            self.operations.append(operation)

    def _operation_conflicts_with_synonyms(self, op: Operation) -> bool:
        """Check if an operation conflicts with user-defined synonyms.

        Args:
            op: Operation to check

        Returns:
            True if the operation conflicts with user-defined synonyms
        """
        # Check each source tag
        for source_tag in op.source_tags:
            user_defined_canonical = self.synonym_config.get_canonical(source_tag)
            is_variant_tag = (user_defined_canonical != source_tag)

            if is_variant_tag and op.target_tag != user_defined_canonical:
                # Operation would merge to wrong canonical form
                return True

        # Check if target is a variant (should only target canonical forms)
        target_canonical = self.synonym_config.get_canonical(op.target_tag)
        if target_canonical != op.target_tag:
            # Target is a variant, not a canonical - conflict
            return True

        return False

    def _filter_synonym_conflicts(self, operations: List[Operation]) -> List[Operation]:
        """Filter out operations that conflict with user-defined synonyms."""
        if not self.synonym_config.has_synonyms():
            return operations

        filtered = []
        conflicted_count = 0

        for op in operations:
            # Skip user-defined synonym operations (already correct)
            if op.source_analyzer == 'user-synonyms':
                filtered.append(op)
                continue

            if self._operation_conflicts_with_synonyms(op):
                conflicted_count += 1
            else:
                filtered.append(op)

        if conflicted_count > 0:
            print(f"  Filtered out {conflicted_count} operations conflicting with user-defined synonyms")

        return filtered

    def _run_synonyms_analyzer(self, min_similarity: float = 0.7):
        """Run semantic synonym detection."""
        print(f"  Running synonym analyzer (min_similarity={min_similarity})...")

        try:
            # Semantic synonyms
            synonym_candidates = detect_synonyms_by_semantics(
                self.tag_stats,
                similarity_threshold=min_similarity
            )

            for candidate in synonym_candidates:
                # Only include the source tag (not both)
                source = candidate['source']
                target = candidate['target']

                operation = Operation(
                    operation_type='merge',
                    source_tags=[source],
                    target_tag=target,
                    reason=f"Semantic synonyms (similarity: {candidate['semantic_similarity']:.3f})",
                    enabled=True,
                    confidence=candidate['semantic_similarity'],
                    source_analyzer='synonyms',
                    metadata={
                        'co_occurrence_ratio': round(candidate['co_occurrence_ratio'], 3),
                        'shared_files': candidate['shared_files']
                    }
                )
                self.operations.append(operation)

            # Acronym expansions
            acronym_candidates = find_acronym_expansions(self.tag_stats)

            for candidate in acronym_candidates[:10]:  # Limit to top 10
                operation = Operation(
                    operation_type='merge',
                    source_tags=[candidate['acronym']],
                    target_tag=candidate['expansion'],
                    reason=f"Acronym expansion (overlap: {candidate['overlap_ratio']:.1%})",
                    enabled=True,
                    confidence=candidate['overlap_ratio'],
                    source_analyzer='synonyms',
                    metadata={
                        'shared_files': candidate['shared_files'],
                        'acronym_count': candidate['acronym_count'],
                        'expansion_count': candidate['expansion_count']
                    }
                )
                self.operations.append(operation)

        except ImportError:
            print("  ⚠ sentence-transformers not available, skipping synonym analysis")

    def _run_plurals_analyzer(self):
        """Run plural/singular detection."""
        print("  Running plural analyzer...")

        variant_groups = defaultdict(set)

        for tag in self.tag_stats.keys():
            # Get all normalized forms
            forms = normalize_plural_forms(tag)
            forms.update(normalize_compound_plurals(tag))

            # Get preferred form based on configuration
            usage_counts = {t: self.tag_stats.get(t, {}).get('count', 0) for t in forms}
            canonical = get_preferred_form(
                forms,
                usage_counts,
                self.config.preference.value,
                self.config.usage_ratio_threshold
            )

            variant_groups[canonical].add(tag)

        # Filter to only groups with multiple variants
        variant_groups = {k: v for k, v in variant_groups.items() if len(v) > 1}

        # Generate operations
        for canonical, variants in variant_groups.items():
            # Calculate total usage
            total_usage = sum(self.tag_stats[t]['count'] for t in variants)
            canonical_usage = self.tag_stats[canonical]['count']

            # Remove canonical from sources
            sources = [v for v in variants if v != canonical]

            if sources:  # Only add if there are sources to merge
                # Determine reason based on preference mode
                if self.config.preference.value == 'usage':
                    reason = f"Plural variant (most-used: {canonical_usage}/{total_usage} uses)"
                elif self.config.preference.value == 'plural':
                    reason = "Plural variant (plural preferred)"
                else:
                    reason = "Plural variant (singular preferred)"

                operation = Operation(
                    operation_type='merge',
                    source_tags=sources,
                    target_tag=canonical,
                    reason=reason,
                    enabled=True,
                    confidence=canonical_usage / total_usage if total_usage > 0 else 0.5,
                    source_analyzer='plurals',
                    metadata={
                        'total_usage': total_usage,
                        'canonical_usage': canonical_usage,
                        'preference_mode': self.config.preference.value
                    }
                )
                self.operations.append(operation)

    def _run_singletons_analyzer(self, no_transformers: bool = False):
        """Run singleton tag analysis."""
        print("  Running singleton analyzer...")

        # Use semantic analysis unless disabled
        use_semantic = not no_transformers

        # Create analyzer and run
        analyzer = SingletonAnalyzer(
            self.tag_stats,
            frequent_threshold=2,  # Consider tags with 2+ uses as "frequent"
            string_similarity_threshold=0.90,  # High threshold for typos
            semantic_similarity_threshold=0.70  # Moderate threshold for synonyms
        )

        suggestions = analyzer.analyze(use_semantic=use_semantic)

        # Convert suggestions to operations
        for suggestion in suggestions:
            operation = Operation(
                operation_type='merge',
                source_tags=[suggestion['singleton']],
                target_tag=suggestion['target'],
                reason=f"Singleton → frequent tag ({suggestion['reason']})",
                enabled=True,
                confidence=suggestion['confidence'],
                source_analyzer='singletons',
                metadata={
                    'method': suggestion['method'],
                    'target_usage': suggestion['target_usage'],
                    **suggestion['metadata']
                }
            )
            self.operations.append(operation)

        print(f"  Found {len(suggestions)} singleton merge suggestions")

    def _deduplicate_operations(self, operations: List[Operation]) -> List[Operation]:
        """Remove duplicate operations, keeping highest confidence version."""
        # Group by (source_tags, target_tag) key
        groups: Dict[tuple, List[Operation]] = defaultdict(list)

        for op in operations:
            # Create a normalized key
            source_key = tuple(sorted(op.source_tags))
            key = (source_key, op.target_tag)
            groups[key].append(op)

        # Keep highest confidence operation from each group
        deduplicated = []
        for key, group_ops in groups.items():
            # Sort by confidence descending
            group_ops.sort(key=lambda x: x.confidence, reverse=True)
            best_op = group_ops[0]

            # If multiple analyzers suggested the same operation, note that
            if len(group_ops) > 1:
                analyzers = [op.source_analyzer for op in group_ops]
                best_op.metadata['also_suggested_by'] = list(set(analyzers) - {best_op.source_analyzer})

            deduplicated.append(best_op)

        return deduplicated

    def _filter_exclusions(self, operations: List[Operation]) -> List[Operation]:
        """Filter out operations involving excluded tags."""
        if not self.exclusions.get_all_exclusions():
            return operations  # No exclusions configured

        filtered = []
        excluded_count = 0

        for op in operations:
            if self.exclusions.is_operation_excluded(op.source_tags, op.target_tag):
                excluded_count += 1
            else:
                filtered.append(op)

        if excluded_count > 0:
            print(f"  Filtered out {excluded_count} operations involving excluded tags")

        return filtered

    def export_to_yaml(self, output_path: str = None) -> str:
        """Export operations to YAML format."""
        # Generate header comment
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        analyzers_run = ", ".join(self.analyzers)

        header_lines = [
            "# Tag Operations Plan",
            f"# Generated: {timestamp}",
            f"# Analyzers: {analyzers_run}",
            "#",
            "# Edit this file to customize operations:",
            "# - Set enabled: false to skip an operation",
            "# - Modify source/target tags as needed",
            "# - Delete operations you don't want",
            "# - Reorder operations (they execute top-to-bottom)",
            "#",
            "# Preview with: tagex tag apply <this-file>",
            "# Apply with:   tagex tag apply <this-file> --execute",
            ""
        ]

        # Build operations data
        operations_data = {
            'operations': [op.to_dict() for op in self.operations]
        }

        # Convert to YAML
        yaml_content = yaml.dump(
            operations_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )

        # Combine header and YAML
        full_content = "\n".join(header_lines) + yaml_content

        # Write to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            print(f"\nOperations exported to: {output_path}")

        return full_content

    def print_summary(self):
        """Print summary of recommendations."""
        if not self.operations:
            print("\nNo recommendations found.")
            return

        print(f"\n{'='*70}")
        print(f"RECOMMENDATIONS SUMMARY")
        print(f"{'='*70}")
        print(f"\nTotal operations: {len(self.operations)}")

        # Group by analyzer
        by_analyzer = defaultdict(int)
        for op in self.operations:
            by_analyzer[op.source_analyzer] += 1

        print("\nBy analyzer:")
        for analyzer, count in sorted(by_analyzer.items()):
            print(f"  {analyzer}: {count}")

        # Group by type
        by_type = defaultdict(int)
        for op in self.operations:
            by_type[op.operation_type] += 1

        print("\nBy operation type:")
        for op_type, count in sorted(by_type.items()):
            print(f"  {op_type}: {count}")

        # Show top recommendations
        print(f"\nTop 10 recommendations (by confidence):")
        sorted_ops = sorted(self.operations, key=lambda x: x.confidence, reverse=True)[:10]

        for i, op in enumerate(sorted_ops, 1):
            sources_str = ", ".join(op.source_tags)
            print(f"\n  {i}. [{op.source_analyzer}] {sources_str} → {op.target_tag}")
            print(f"     {op.reason}")
            print(f"     Confidence: {op.confidence:.3f}")
