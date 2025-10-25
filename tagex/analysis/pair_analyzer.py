#!/usr/bin/env python3
"""
Tag pair analyzer for finding natural tag groupings.
"""
import json
from collections import defaultdict, Counter
from itertools import combinations
import sys
import argparse
from typing import Dict, List, Set, Tuple, Any
from tagex.utils.tag_normalizer import is_valid_tag


def load_tag_data(json_file: str) -> List[Dict[str, Any]]:
    """Load tag data from JSON file.

    Args:
        json_file: Path to JSON file containing tag data

    Returns:
        List of tag dictionaries
    """
    with open(json_file, 'r') as f:
        return json.load(f)  # type: ignore[no-any-return]


def build_file_to_tags_map(tag_data: List[Dict[str, Any]], filter_noise: bool = False) -> Dict[str, Set[str]]:
    """Build mapping from file path to all tags in that file.

    Args:
        tag_data: List of tag dictionaries
        filter_noise: Whether to filter out invalid tags

    Returns:
        Dictionary mapping file paths to sets of tags
    """
    file_to_tags: Dict[str, Set[str]] = defaultdict(set)

    for tag_info in tag_data:
        tag = tag_info['tag']
        if filter_noise and not is_valid_tag(tag):
            continue
        for file_path in tag_info['relativePaths']:
            file_to_tags[file_path].add(tag)

    return file_to_tags


def calculate_pairs(file_to_tags: Dict[str, Set[str]], min_pairs: int = 2) -> Dict[Tuple[str, str], int]:
    """Calculate tag pair frequencies.

    Args:
        file_to_tags: Dictionary mapping file paths to sets of tags
        min_pairs: Minimum number of occurrences for a pair to be included

    Returns:
        Dictionary mapping tag pairs to occurrence counts
    """
    pairs: Dict[Tuple[str, str], int] = defaultdict(int)

    for file_path, tags in file_to_tags.items():
        if len(tags) < 2:
            continue

        # Generate all pairs of tags that appear together
        for tag1, tag2 in combinations(sorted(tags), 2):
            pairs[(tag1, tag2)] += 1

    # Filter by minimum pairs
    return {pair: count for pair, count in pairs.items()
            if count >= min_pairs}


def find_tag_clusters(pairs: Dict[Tuple[str, str], int], min_cluster_size: int = 3) -> List[Set[str]]:
    """Find clusters of tags that frequently appear together.

    Args:
        pairs: Dictionary mapping tag pairs to occurrence counts
        min_cluster_size: Minimum size for a cluster to be included

    Returns:
        List of tag clusters (sets of tags)
    """
    # Build adjacency graph
    tag_connections: Dict[str, Set[Tuple[str, int]]] = defaultdict(set)

    for (tag1, tag2), count in pairs.items():
        tag_connections[tag1].add((tag2, count))
        tag_connections[tag2].add((tag1, count))

    # Find connected components / clusters
    clusters: List[Set[str]] = []
    visited: Set[str] = set()

    def dfs_cluster(tag: str, current_cluster: Set[str], min_connection_strength: int = 3) -> None:
        if tag in visited:
            return
        visited.add(tag)
        current_cluster.add(tag)

        # Add strongly connected neighbors
        for neighbor, strength in tag_connections[tag]:
            if neighbor not in visited and strength >= min_connection_strength:
                dfs_cluster(neighbor, current_cluster, min_connection_strength)

    for tag in tag_connections:
        if tag not in visited:
            cluster: Set[str] = set()
            dfs_cluster(tag, cluster)
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)

    return clusters


def analyze_tag_relationships(
    tag_data: List[Dict[str, Any]],
    min_pairs: int = 2,
    filter_noise: bool = False
) -> Tuple[Dict[Tuple[str, str], int], Dict[str, Set[str]]]:
    """Main analysis function.

    Args:
        tag_data: List of tag dictionaries
        min_pairs: Minimum number of occurrences for a pair to be included
        filter_noise: Whether to filter out invalid tags

    Returns:
        Tuple of (pairs dictionary, file_to_tags dictionary)
    """
    file_to_tags = build_file_to_tags_map(tag_data, filter_noise)
    pairs = calculate_pairs(file_to_tags, min_pairs)

    tag_type = "meaningful tags" if filter_noise else "all tags"
    print(f"Analyzing {len(file_to_tags)} files with {tag_type} pairs...")
    print(f"Found {len(pairs)} tag pairs with ≥{min_pairs} occurrences")

    return pairs, file_to_tags


def main() -> None:
    """Main entry point for pair analyzer CLI."""
    parser = argparse.ArgumentParser(description='Analyze tag pair patterns')
    parser.add_argument('input_file', help='JSON file containing tag data')
    parser.add_argument('--min-pairs', type=int, default=2, help='Minimum pair threshold')
    parser.add_argument('--filter-noise', action='store_true', default=True, help='Filter out technical noise tags (default: enabled)')
    parser.add_argument('--no-filter', action='store_true', help='Disable noise filtering')
    args = parser.parse_args()

    # Handle --no-filter override
    filter_noise = args.filter_noise and not args.no_filter

    tag_data = load_tag_data(args.input_file)
    pairs, file_to_tags = analyze_tag_relationships(tag_data, args.min_pairs, filter_noise)

    # Top tag pairs
    print("\nTop 20 Tag Pairs:")
    for (tag1, tag2), count in sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{count:3d}  {tag1} + {tag2}")

    # Find clusters
    clusters = find_tag_clusters(pairs)
    print(f"\nFound {len(clusters)} natural tag clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i} ({len(cluster)} tags):")
        for tag in sorted(cluster):
            print(f"  - {tag}")

    # Most connected tags
    tag_connections: Dict[str, int] = defaultdict(int)
    for (tag1, tag2), count in pairs.items():
        tag_connections[tag1] += count
        tag_connections[tag2] += count

    print(f"\nMost Connected Tags (hub tags):")
    for tag, total_connections in sorted(tag_connections.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"{total_connections:3d}  {tag}")


if __name__ == '__main__':
    main()