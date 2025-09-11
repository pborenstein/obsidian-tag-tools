#!/usr/bin/env python3
"""
Analyze the impact of the proposed tag migration.
"""
import json
from collections import defaultdict, Counter
import argparse


def analyze_migration_impact(input_file):
    """Analyze the before/after impact of tag migration."""
    
    # Load original tags
    with open(input_file, 'r') as f:
        original_tags = json.load(f)
    
    # Load migration mappings
    from tag_migration import TAG_MAPPINGS, DELETE_TAGS
    
    print("MIGRATION IMPACT ANALYSIS")
    print("="*50)
    
    # Calculate before/after stats
    original_tag_count = len(original_tags)
    original_usage_count = sum(tag['tagCount'] for tag in original_tags)
    
    # Apply mappings
    new_tags = defaultdict(lambda: {"count": 0, "files": set()})
    deleted_count = 0
    
    for tag_info in original_tags:
        tag = tag_info['tag']
        
        # Check if tag should be deleted
        if tag in DELETE_TAGS:
            deleted_count += tag_info['tagCount']
            continue
        
        # Apply mapping
        if tag in TAG_MAPPINGS:
            new_tag = TAG_MAPPINGS[tag]
        else:
            # Check for partial matches
            new_tag = tag
            for old_tag, mapped_tag in TAG_MAPPINGS.items():
                if old_tag in tag:
                    new_tag = mapped_tag
                    break
        
        # Add to new structure
        new_tags[new_tag]["count"] += tag_info['tagCount']
        new_tags[new_tag]["files"].update(tag_info['relativePaths'])
    
    new_tag_count = len(new_tags)
    new_usage_count = sum(data["count"] for data in new_tags.values())
    
    print(f"BEFORE: {original_tag_count:,} unique tags, {original_usage_count:,} total usages")
    print(f"AFTER:  {new_tag_count:,} unique tags, {new_usage_count:,} total usages")
    print(f"REDUCTION: {original_tag_count - new_tag_count:,} tags ({((original_tag_count - new_tag_count) / original_tag_count * 100):.1f}%)")
    print(f"DELETED: {deleted_count:,} tag usages")
    
    # Show new hierarchical structure
    print(f"\nNEW HIERARCHICAL STRUCTURE:")
    hierarchies = defaultdict(list)
    
    for tag, data in new_tags.items():
        if '/' in tag:
            root = tag.split('/')[0]
            hierarchies[root].append((tag, data["count"]))
        else:
            hierarchies['[flat]'].append((tag, data["count"]))
    
    for hierarchy, tags in sorted(hierarchies.items()):
        tags.sort(key=lambda x: -x[1])  # Sort by usage count
        print(f"\n{hierarchy.upper()}/ ({len(tags)} tags):")
        for tag, count in tags[:8]:  # Show top 8 in each hierarchy
            if hierarchy != '[flat]':
                display_tag = tag.replace(f"{hierarchy}/", "  ")
            else:
                display_tag = tag
            print(f"  {count:3d}  {display_tag}")
        if len(tags) > 8:
            print(f"      ... and {len(tags) - 8} more")
    
    # Show biggest consolidations
    print(f"\nBIGGEST CONSOLIDATIONS:")
    consolidations = defaultdict(int)
    consolidation_sources = defaultdict(list)
    
    for tag_info in original_tags:
        old_tag = tag_info['tag']
        if old_tag in TAG_MAPPINGS:
            new_tag = TAG_MAPPINGS[old_tag]
            consolidations[new_tag] += tag_info['tagCount']
            consolidation_sources[new_tag].append(f"{old_tag} ({tag_info['tagCount']})")
    
    for new_tag, total_count in sorted(consolidations.items(), key=lambda x: -x[1])[:10]:
        sources = consolidation_sources[new_tag]
        print(f"\n{new_tag} → {total_count} total usages")
        for source in sources[:5]:
            print(f"  ← {source}")
        if len(sources) > 5:
            print(f"  ← ... and {len(sources) - 5} more sources")
    
    # Show potential issues
    print(f"\nPOTENTIAL ISSUES:")
    
    # Very high usage tags that might be over-consolidated
    high_usage = [(tag, data["count"]) for tag, data in new_tags.items() if data["count"] > 100]
    if high_usage:
        print(f"\nHigh-usage tags (may need further subdivision):")
        for tag, count in sorted(high_usage, key=lambda x: -x[1])[:5]:
            print(f"  {count:3d}  {tag}")
    
    # Tags that didn't get mapped
    unmapped = [tag_info['tag'] for tag_info in original_tags 
                if tag_info['tag'] not in TAG_MAPPINGS 
                and tag_info['tag'] not in DELETE_TAGS
                and tag_info['tagCount'] >= 3]
    if unmapped:
        print(f"\nUnmapped tags with ≥3 usages (consider adding mappings):")
        for tag in unmapped[:10]:
            original_count = next(t['tagCount'] for t in original_tags if t['tag'] == tag)
            print(f"  {original_count:3d}  {tag}")


def main():
    parser = argparse.ArgumentParser(description='Analyze tag migration impact')
    parser.add_argument('input_file', help='JSON file containing tag data')
    args = parser.parse_args()
    
    analyze_migration_impact(args.input_file)


if __name__ == "__main__":
    main()