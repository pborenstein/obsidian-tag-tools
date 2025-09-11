#!/usr/bin/env python3
"""
Tag co-occurrence analyzer for finding natural tag groupings.
"""
import json
from collections import defaultdict, Counter
from itertools import combinations
import sys
import argparse
from utils.tag_normalizer import is_valid_tag


def load_tag_data(json_file):
    """Load tag data from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)


def build_file_to_tags_map(tag_data, filter_noise=False):
    """Build mapping from file path to all tags in that file."""
    file_to_tags = defaultdict(set)
    
    for tag_info in tag_data:
        tag = tag_info['tag']
        if filter_noise and not is_valid_tag(tag):
            continue
        for file_path in tag_info['relativePaths']:
            file_to_tags[file_path].add(tag)
    
    return file_to_tags


def calculate_cooccurrence(file_to_tags, min_cooccurrence=2):
    """Calculate tag co-occurrence frequencies."""
    cooccurrence = defaultdict(int)
    
    for file_path, tags in file_to_tags.items():
        if len(tags) < 2:
            continue
            
        # Generate all pairs of tags that appear together
        for tag1, tag2 in combinations(sorted(tags), 2):
            cooccurrence[(tag1, tag2)] += 1
    
    # Filter by minimum co-occurrence
    return {pair: count for pair, count in cooccurrence.items() 
            if count >= min_cooccurrence}


def find_tag_clusters(cooccurrence, min_cluster_size=3):
    """Find clusters of tags that frequently appear together."""
    # Build adjacency graph
    tag_connections = defaultdict(set)
    
    for (tag1, tag2), count in cooccurrence.items():
        tag_connections[tag1].add((tag2, count))
        tag_connections[tag2].add((tag1, count))
    
    # Find connected components / clusters
    clusters = []
    visited = set()
    
    def dfs_cluster(tag, current_cluster, min_connection_strength=3):
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
            cluster = set()
            dfs_cluster(tag, cluster)
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)
    
    return clusters


def analyze_tag_relationships(tag_data, min_cooccurrence=2, filter_noise=False):
    """Main analysis function."""
    file_to_tags = build_file_to_tags_map(tag_data, filter_noise)
    cooccurrence = calculate_cooccurrence(file_to_tags, min_cooccurrence)
    
    tag_type = "meaningful tags" if filter_noise else "all tags"
    print(f"Analyzing {len(file_to_tags)} files with {tag_type} co-occurrences...")
    print(f"Found {len(cooccurrence)} tag pairs with ≥{min_cooccurrence} co-occurrences")
    
    return cooccurrence, file_to_tags


def main():
    parser = argparse.ArgumentParser(description='Analyze tag co-occurrence patterns')
    parser.add_argument('input_file', help='JSON file containing tag data')
    parser.add_argument('--min-cooccurrence', type=int, default=2, help='Minimum co-occurrence threshold')
    parser.add_argument('--filter-noise', action='store_true', default=True, help='Filter out technical noise tags (default: enabled)')
    parser.add_argument('--no-filter', action='store_true', help='Disable noise filtering')
    args = parser.parse_args()
    
    # Handle --no-filter override
    filter_noise = args.filter_noise and not args.no_filter
    
    tag_data = load_tag_data(args.input_file)
    cooccurrence, file_to_tags = analyze_tag_relationships(tag_data, args.min_cooccurrence, filter_noise)
    
    # Top co-occurring pairs
    print("\nTop 20 Co-occurring Tag Pairs:")
    for (tag1, tag2), count in sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{count:3d}  {tag1} + {tag2}")
    
    # Find clusters
    clusters = find_tag_clusters(cooccurrence)
    print(f"\nFound {len(clusters)} natural tag clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i} ({len(cluster)} tags):")
        for tag in sorted(cluster):
            print(f"  - {tag}")
    
    # Most connected tags
    tag_connections = defaultdict(int)
    for (tag1, tag2), count in cooccurrence.items():
        tag_connections[tag1] += count
        tag_connections[tag2] += count
    
    print(f"\nMost Connected Tags (hub tags):")
    for tag, total_connections in sorted(tag_connections.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"{total_connections:3d}  {tag}")


if __name__ == '__main__':
    main()