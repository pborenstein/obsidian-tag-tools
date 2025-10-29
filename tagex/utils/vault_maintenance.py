"""Vault maintenance utilities for cleanup operations."""

from pathlib import Path
from typing import List
from datetime import datetime


class BakRemover:
  """Remove .bak backup files safely."""

  def __init__(self, dry_run: bool = True, quiet: bool = False):
    self.dry_run = dry_run
    self.quiet = quiet
    self.stats = {
      'found': 0,
      'deleted': 0,
      'errors': 0
    }

  def log(self, message: str, level: str = "INFO"):
    """Log a message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {level}: {message}"
    if not self.quiet or level == "ERROR":
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


def run_cleanup(vault_path: str, execute: bool = False,
                recursive: bool = True, quiet: bool = False) -> dict:
  """
  Run backup file cleanup operation.

  Args:
    vault_path: Path to vault directory
    execute: Actually delete files (default: dry-run)
    recursive: Search subdirectories
    quiet: Reduce output verbosity

  Returns:
    Statistics dictionary with results
  """
  directory = Path(vault_path)

  if not directory.exists():
    raise ValueError(f"Directory not found: {vault_path}")
  if not directory.is_dir():
    raise ValueError(f"Not a directory: {vault_path}")

  # Create remover and run
  remover = BakRemover(dry_run=not execute, quiet=quiet)
  remover.remove_files(directory, recursive=recursive)

  return remover.stats
