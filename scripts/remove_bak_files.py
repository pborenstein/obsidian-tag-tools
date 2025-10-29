#!/usr/bin/env python3
"""
BULLETPROOF script to remove .bak backup files.

Safety features:
- Dry-run mode by default
- Shows what will be deleted
- Handles impossible filenames
- Comprehensive logging
"""

import sys
from pathlib import Path
from typing import List
from datetime import datetime


class BakRemover:
    """Remove .bak backup files safely."""

    def __init__(self, dry_run: bool = True, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'found': 0,
            'deleted': 0,
            'errors': 0
        }

    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {level}: {message}"
        if self.verbose or level == "ERROR":
            print(entry)

    def find_bak_files(self, directory: Path, recursive: bool = True) -> List[Path]:
        """Find all .bak files in directory."""
        if recursive:
            bak_files = list(directory.rglob("**/*.bak"))
        else:
            bak_files = list(directory.glob("*.bak"))
        return sorted(bak_files)

    def remove_files(self, directory: Path, recursive: bool = True):
        """Remove .bak files from directory."""
        self.log(f"\n{'='*70}")
        self.log(f"Scanning for .bak files")
        self.log(f"Directory: {directory}")
        self.log(f"Recursive: {'Yes' if recursive else 'No (single directory only)'}")
        self.log(f"Mode: {'DRY-RUN (no deletions)' if self.dry_run else 'LIVE (files will be deleted)'}")
        self.log(f"{'='*70}\n")

        # Find all .bak files
        bak_files = self.find_bak_files(directory, recursive=recursive)
        self.stats['found'] = len(bak_files)

        if not bak_files:
            self.log("No .bak files found")
            return

        self.log(f"Found {len(bak_files)} .bak files:\n")

        for bak_file in bak_files:
            try:
                self.log(f"  {bak_file.name}")

                if self.dry_run:
                    self.log(f"    [DRY-RUN] Would delete", "DRYRUN")
                else:
                    bak_file.unlink()
                    self.stats['deleted'] += 1
                    self.log(f"    ✓ Deleted", "SUCCESS")

            except Exception as e:
                self.log(f"    ERROR: {e}", "ERROR")
                self.stats['errors'] += 1

        self.print_summary()

    def print_summary(self):
        """Print summary statistics."""
        self.log(f"\n{'='*70}")
        self.log("SUMMARY")
        self.log(f"{'='*70}")
        self.log(f".bak files found:     {self.stats['found']}")
        self.log(f".bak files deleted:   {self.stats['deleted']}")
        self.log(f"Errors:               {self.stats['errors']}")

        if self.dry_run and self.stats['found'] > 0:
            self.log(f"\nThis was a DRY-RUN. To actually delete files, run with --execute")
        elif not self.dry_run and self.stats['deleted'] > 0:
            self.log(f"\n✓ Backup files have been removed")

        self.log(f"{'='*70}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove .bak backup files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run recursively (safe, shows what will be deleted, default)
  python remove_bak_files.py /path/to/directory

  # Dry-run single directory only (not recursive)
  python remove_bak_files.py /path/to/directory --no-recursive

  # Actually delete files recursively
  python remove_bak_files.py /path/to/directory --execute

  # Quiet mode
  python remove_bak_files.py /path/to/directory --execute --quiet
        """
    )

    parser.add_argument('directory',
                       help='Directory containing .bak files')
    parser.add_argument('--execute', action='store_true',
                       help='Actually delete files (default is dry-run)')
    parser.add_argument('--recursive', action='store_true', default=True,
                       help='Search subdirectories recursively (default: True)')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false',
                       help='Only search immediate directory, not subdirectories')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"ERROR: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    if not directory.is_dir():
        print(f"ERROR: Not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    # Create remover and run
    remover = BakRemover(
        dry_run=not args.execute,
        verbose=not args.quiet
    )

    remover.remove_files(directory, recursive=args.recursive)

    # Exit with error code if there were errors
    if remover.stats['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
