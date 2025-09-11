"""
Output formatting utilities for tag extraction results.
"""
import json
import csv
from typing import Dict, List, Any
from pathlib import Path


def format_as_plugin_json(tag_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Format tag data to match the Obsidian plugin JSON structure.
    
    Args:
        tag_data: Tag data from extractor
        
    Returns:
        List of tag objects matching plugin format
    """
    formatted_tags = []
    
    for tag_name, data in tag_data.items():
        tag_obj = {
            "tag": tag_name,
            "tagCount": data["count"],
            "relativePaths": sorted(list(data["files"]))
        }
        formatted_tags.append(tag_obj)
    
    # Sort by tag count (descending) then by tag name
    formatted_tags.sort(key=lambda x: (-x["tagCount"], x["tag"]))
    
    return formatted_tags


def format_as_csv(tag_data: Dict[str, Dict]) -> List[List[str]]:
    """
    Format tag data as CSV rows.
    
    Args:
        tag_data: Tag data from extractor
        
    Returns:
        List of CSV rows (including header)
    """
    rows = [["tag", "count", "files"]]
    
    for tag_name, data in tag_data.items():
        files_str = "; ".join(sorted(list(data["files"])))
        rows.append([tag_name, str(data["count"]), files_str])
    
    # Sort by count (descending) then by tag name
    rows[1:] = sorted(rows[1:], key=lambda x: (-int(x[1]), x[0]))
    
    return rows


def format_as_text(tag_data: Dict[str, Dict]) -> str:
    """
    Format tag data as readable text.
    
    Args:
        tag_data: Tag data from extractor
        
    Returns:
        Formatted text string
    """
    if not tag_data:
        return "No tags found."
    
    lines = []
    lines.append(f"Found {len(tag_data)} unique tags:")
    lines.append("")
    
    # Sort by count (descending) then by tag name
    sorted_tags = sorted(tag_data.items(), key=lambda x: (-x[1]["count"], x[0]))
    
    for tag_name, data in sorted_tags:
        lines.append(f"{tag_name} ({data['count']} files)")
        for file_path in sorted(list(data["files"])):
            lines.append(f"  - {file_path}")
        lines.append("")
    
    return "\n".join(lines)


def save_output(data: Any, output_path: Path, format_type: str = "json") -> None:
    """
    Save formatted data to file.
    
    Args:
        data: Formatted data to save
        output_path: Path to save the file
        format_type: Output format (json, csv, txt)
    """
    if format_type == "json":
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    elif format_type == "csv":
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
    
    elif format_type == "txt":
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(data)
    
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def print_summary(tag_data: Dict[str, Dict], stats: Dict) -> None:
    """
    Print a summary of extraction results.
    
    Args:
        tag_data: Tag data from extractor
        stats: Extraction statistics
    """
    print(f"Extraction complete!")
    print(f"Vault: {stats['vault_path']}")
    print(f"Files processed: {stats['files_processed']}")
    print(f"Errors: {stats['errors']}")
    print(f"Unique tags found: {len(tag_data)}")
    
    if tag_data:
        top_tags = sorted(tag_data.items(), key=lambda x: -x[1]["count"])[:5]
        print(f"Top tags:")
        for tag_name, data in top_tags:
            print(f"  {tag_name}: {data['count']} files")