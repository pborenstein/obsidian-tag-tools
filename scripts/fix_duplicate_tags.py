#!/usr/bin/env python3
"""
BULLETPROOF script to fix duplicate 'tags:' fields in frontmatter.

Safety features:
- Creates backups before any modification (.bak files)
- Dry-run mode by default
- Comprehensive logging
- Validates each change
- Handles impossible filenames
- Preserves file formatting
"""

import sys
import shutil
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime


class DuplicateTagsFixer:
    """Fix duplicate tags: fields in markdown frontmatter."""

    def __init__(self, dry_run: bool = True, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'total_files': 0,
            'files_with_duplicates': 0,
            'files_fixed': 0,
            'files_skipped': 0,
            'errors': 0
        }
        self.log_entries = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(entry)
        if self.verbose or level == "ERROR":
            print(entry)

    def find_duplicate_tags(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Check if file has duplicate tags: fields and return fixed content.

        Returns:
            (has_duplicates, fixed_content or None)
        """
        # Split on frontmatter delimiters
        if not content.startswith('---\n'):
            return False, None

        parts = content.split('---\n', 2)
        if len(parts) < 3:
            return False, None

        frontmatter = parts[1]
        body = parts[2]

        # Find all lines that start with 'tags:'
        lines = frontmatter.split('\n')
        tag_line_indices = []
        tag_line_values = []

        for i, line in enumerate(lines):
            # Match 'tags:' at start of line (may have leading whitespace)
            if re.match(r'^\s*tags:\s*', line):
                tag_line_indices.append(i)
                # Extract what comes after 'tags:'
                match = re.match(r'^\s*tags:\s*(.*)', line)
                tag_line_values.append(match.group(1).strip() if match else '')

        # If no duplicates, nothing to fix
        if len(tag_line_indices) <= 1:
            return False, None

        # We have duplicates - consolidate them
        self.log(f"Found {len(tag_line_indices)} 'tags:' fields")

        # Collect all non-empty tag values
        all_tags = []
        for value in tag_line_values:
            if value:
                all_tags.append(value)
                self.log(f"  Tag value: {value}")
            else:
                self.log(f"  Empty tags: field")

        # Determine the consolidated value
        if not all_tags:
            # All were empty - keep one empty
            consolidated_value = ""
        elif len(all_tags) == 1:
            # One has value - use it
            consolidated_value = all_tags[0]
        else:
            # Multiple have values - this is unusual, log warning
            self.log(f"WARNING: Multiple non-empty tags fields, using last one: {all_tags[-1]}", "WARN")
            consolidated_value = all_tags[-1]

        # Rebuild frontmatter with only one tags: field
        # Keep the first tags: line position, remove others
        new_lines = []
        kept_tags_line = False

        for i, line in enumerate(lines):
            if i in tag_line_indices:
                if not kept_tags_line:
                    # This is the first tags: line - keep it with consolidated value
                    if consolidated_value:
                        new_lines.append(f"tags: {consolidated_value}")
                    else:
                        new_lines.append("tags:")
                    kept_tags_line = True
                    self.log(f"  Keeping tags line at position {i}")
                else:
                    # Skip duplicate tags: lines
                    self.log(f"  Removing duplicate tags line at position {i}")
            else:
                # Keep all non-tags lines as-is
                new_lines.append(line)

        # Reconstruct file
        new_frontmatter = '\n'.join(new_lines)
        new_content = f"---\n{new_frontmatter}\n---\n{body}"

        return True, new_content

    def fix_file(self, file_path: Path) -> bool:
        """
        Fix duplicate tags in a single file.

        Returns:
            True if file was fixed, False otherwise
        """
        self.stats['total_files'] += 1

        try:
            # Read file
            self.log(f"\nProcessing: {file_path.name}")
            content = file_path.read_text(encoding='utf-8')

            # Check for duplicates and get fixed content
            has_duplicates, fixed_content = self.find_duplicate_tags(content)

            if not has_duplicates:
                self.log("  No duplicate tags found")
                self.stats['files_skipped'] += 1
                return False

            self.stats['files_with_duplicates'] += 1

            if self.dry_run:
                self.log("  [DRY-RUN] Would fix this file", "DRYRUN")
                return False

            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            self.log(f"  Created backup: {backup_path.name}")

            # Write fixed content
            file_path.write_text(fixed_content, encoding='utf-8')
            self.log(f"  ✓ Fixed duplicate tags", "SUCCESS")

            # Validate the fix
            new_content = file_path.read_text(encoding='utf-8')
            still_has_dupes, _ = self.find_duplicate_tags(new_content)

            if still_has_dupes:
                # Restore from backup
                shutil.copy2(backup_path, file_path)
                self.log(f"  ERROR: Fix failed validation, restored from backup", "ERROR")
                self.stats['errors'] += 1
                return False

            self.stats['files_fixed'] += 1
            return True

        except Exception as e:
            self.log(f"  ERROR: {e}", "ERROR")
            self.stats['errors'] += 1
            return False

    def fix_files(self, file_paths: List[Path]):
        """Fix multiple files."""
        self.log(f"\n{'='*70}")
        self.log(f"Starting duplicate tags fix")
        self.log(f"Mode: {'DRY-RUN (no changes will be made)' if self.dry_run else 'LIVE (files will be modified)'}")
        self.log(f"Files to process: {len(file_paths)}")
        self.log(f"{'='*70}\n")

        for file_path in file_paths:
            if not file_path.exists():
                self.log(f"File not found: {file_path}", "ERROR")
                self.stats['errors'] += 1
                continue

            if not file_path.is_file():
                self.log(f"Not a file: {file_path}", "ERROR")
                self.stats['errors'] += 1
                continue

            self.fix_file(file_path)

        self.print_summary()

    def print_summary(self):
        """Print summary statistics."""
        self.log(f"\n{'='*70}")
        self.log("SUMMARY")
        self.log(f"{'='*70}")
        self.log(f"Total files processed:       {self.stats['total_files']}")
        self.log(f"Files with duplicate tags:   {self.stats['files_with_duplicates']}")
        self.log(f"Files fixed:                 {self.stats['files_fixed']}")
        self.log(f"Files skipped (no dupes):    {self.stats['files_skipped']}")
        self.log(f"Errors:                      {self.stats['errors']}")

        if self.dry_run and self.stats['files_with_duplicates'] > 0:
            self.log(f"\nThis was a DRY-RUN. To actually fix files, run with --execute")
        elif not self.dry_run and self.stats['files_fixed'] > 0:
            self.log(f"\n✓ Files have been fixed. Backups saved with .bak extension")

        self.log(f"{'='*70}\n")

    def save_log(self, log_path: Path):
        """Save log to file."""
        log_path.write_text('\n'.join(self.log_entries), encoding='utf-8')
        print(f"\nLog saved to: {log_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix duplicate 'tags:' fields in markdown frontmatter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run on directory (safe, no changes)
  python fix_duplicate_tags.py /path/to/clippings

  # Dry-run on filelist
  python fix_duplicate_tags.py --filelist ~/filelist.txt

  # Actually fix files (creates .bak backups)
  python fix_duplicate_tags.py /path/to/clippings --execute

  # Fix both directory and filelist
  python fix_duplicate_tags.py /path/to/clippings --filelist ~/filelist.txt --execute
        """
    )

    parser.add_argument('directory', nargs='?',
                       help='Directory containing markdown files')
    parser.add_argument('--filelist', type=Path,
                       help='Text file containing list of files to process')
    parser.add_argument('--execute', action='store_true',
                       help='Actually modify files (default is dry-run)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    parser.add_argument('--log', type=Path,
                       help='Save log to file')

    args = parser.parse_args()

    # Collect files to process
    files_to_process = []

    if args.directory:
        directory = Path(args.directory)
        if not directory.exists():
            print(f"ERROR: Directory not found: {directory}", file=sys.stderr)
            sys.exit(1)
        if not directory.is_dir():
            print(f"ERROR: Not a directory: {directory}", file=sys.stderr)
            sys.exit(1)

        # Find all .md files
        md_files = list(directory.glob("*.md"))
        files_to_process.extend(md_files)
        print(f"Found {len(md_files)} markdown files in directory")

    if args.filelist:
        if not args.filelist.exists():
            print(f"ERROR: Filelist not found: {args.filelist}", file=sys.stderr)
            sys.exit(1)

        # Read filelist
        lines = args.filelist.read_text(encoding='utf-8').strip().split('\n')
        # Remove quotes and create Path objects
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove surrounding quotes
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            # Unescape any escape sequences
            line = line.encode().decode('unicode_escape')
            file_path = Path(line)
            if file_path.exists():
                files_to_process.append(file_path)
            else:
                print(f"WARNING: File in list not found: {file_path}", file=sys.stderr)

        print(f"Found {len(lines)} files in filelist")

    if not files_to_process:
        print("ERROR: No files to process. Specify directory or --filelist", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Remove duplicates
    files_to_process = list(set(files_to_process))

    # Create fixer and run
    fixer = DuplicateTagsFixer(
        dry_run=not args.execute,
        verbose=not args.quiet
    )

    fixer.fix_files(files_to_process)

    # Save log if requested
    if args.log:
        fixer.save_log(args.log)

    # Exit with error code if there were errors
    if fixer.stats['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
