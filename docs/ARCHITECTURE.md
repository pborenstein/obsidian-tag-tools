# Tagex Architecture

## Overview

Tagex is a comprehensive tag management system for Obsidian vaults. It provides extraction, analysis, and modification capabilities through a modular CLI architecture with safe-by-default operations.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI STRUCTURE                           │
│                                                                 │
│  tagex                                                          │
│   ├─ tags          → Tag operations (extract, rename, merge)    │
│   ├─ analyze       → Analysis commands (pairs, quality, etc.)   │
│   ├─ vault         → Maintenance (cleanup)                      │
│   ├─ init          → Configuration setup                        │
│   ├─ validate      → Config validation                          │
│   ├─ stats         → Vault statistics                           │
│   └─ health        → Health reporting                           │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         MAIN COMPONENTS                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   CLI Layer  │─────►│    Core      │─────►│   Analysis   │      │
│  │  (main.py)   │      │  Extraction  │      │    Layer     │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
│         │                     │                      │             │
│         │                     ▼                      ▼             │
│         │              ┌──────────────┐      ┌──────────────┐      │
│         │              │  Operations  │      │Configuration │      │
│         └─────────────►│    Layer     │      │   System     │      │
│                        └──────────────┘      └──────────────┘      │
│                               │                      │             │
│                               ▼                      ▼             │
│                        ┌──────────────┐      ┌──────────────┐      │
│                        │   Utilities  │      │    Vault     │      │
│                        │  (parsers,   │      │ Maintenance  │      │
│                        │   filters)   │      └──────────────┘      │
│                        └──────────────┘                            │
└────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Breakdown

### CLI Layer (tagex/main.py)

Command structure with three primary groups:

```
┌─────────────────────────────────────────────────────────────┐
│ COMMAND GROUP: tags                                         │
├─────────────────────────────────────────────────────────────┤
│ tagex tag export [vault_path]                               │
│   └─ Extract tags from vault (JSON/CSV/TXT)                 │
│                                                             │
│ tagex tag rename [vault_path] old-tag new-tag               │
│   └─ Rename tag across all files                            │
│                                                             │
│ tagex tag merge [vault_path] tag1 tag2 --into target        │
│   └─ Merge multiple tags into one                           │
│                                                             │
│ tagex tag delete [vault_path] unwanted-tag                  │
│   └─ Remove tags from vault                                 │
│                                                             │
│ tagex tag fix [vault_path]                                  │
│   └─ Fix duplicate 'tags:' fields in frontmatter            │
│                                                             │
│ tagex tag apply operations.yaml                             │
│   └─ Apply tag operations from YAML file                    │
│                                                             │
│ All commands: --execute flag required to apply changes      │
│              Default is preview mode                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ COMMAND GROUP: analyze                                      │
├─────────────────────────────────────────────────────────────┤
│ tagex analyze pairs [vault_path]                            │
│   └─ Tag co-occurrence and clustering                       │
│                                                             │
│ tagex analyze merges [vault_path]                           │
│   └─ Suggest tag merges (TF-IDF embeddings)                 │
│                                                             │
│ tagex analyze quality [vault_path]                          │
│   └─ Overbroad tags and specificity scoring                 │
│                                                             │
│ tagex analyze synonyms [vault_path]                         │
│   └─ Semantic synonym detection (sentence-transformers)     │
│                                                             │
│ tagex analyze plurals [vault_path]                          │
│   └─ Singular/plural variant detection                      │
│                                                             │
│ tagex analyze suggest --vault-path /vault [paths...]        │
│   └─ Content-based tag suggestions                          │
│                                                             │
│ tagex analyze recommendations [vault_path]                  │
│   └─ Unified recommendations from all analyzers             │
│                                                             │
│ All analyze commands accept vault path or JSON file         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ COMMAND GROUP: vault                                        │
├─────────────────────────────────────────────────────────────┤
│ tagex vault cleanup [vault_path]                            │
│   └─ Remove .bak backup files                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TOP-LEVEL COMMANDS                                          │
├─────────────────────────────────────────────────────────────┤
│ tagex init [vault_path]                                     │
│   └─ Initialize .tagex/ configuration directory             │
│                                                             │
│ tagex config validate [vault_path]                          │
│   └─ Validate configuration files                           │
│                                                             │
│ tagex stats [vault_path]                                    │
│   └─ Comprehensive vault statistics                         │
│                                                             │
│ tagex health [vault_path]                                   │
│   └─ Health report with recommendations                     │
│                                                             │
│ Commands default to current directory if vault_path omitted │
└─────────────────────────────────────────────────────────────┘
```

### Core Extraction Layer

```
┌─────────────────────────────────────────────────────────────┐
│ tagex/core/extractor/                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ core.py                                                     │
│   └─ TagExtractor class                                     │
│      ├─ Processes vault files sequentially                  │
│      ├─ Aggregates tag data from parsers                    │
│      ├─ Selective tag type filtering                        │
│      ├─ Statistics tracking                                 │
│      └─ Error resilience (continues on failures)            │
│                                                             │
│ output_formatter.py                                         │
│   └─ Format output data                                     │
│      ├─ format_as_plugin_json() → Obsidian compatible       │
│      ├─ format_as_csv() → Spreadsheet analysis              │
│      ├─ format_as_text() → Human readable                   │
│      └─ save_output() / print_summary()                     │
└─────────────────────────────────────────────────────────────┘
```

### Parser Layer

```
┌─────────────────────────────────────────────────────────────┐
│ tagex/core/parsers/                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ frontmatter_parser.py                                       │
│   └─ Parse YAML frontmatter tags                            │
│      ├─ extract_frontmatter() → Parse YAML block            │
│      ├─ extract_tags_from_frontmatter() → Get tags          │
│      ├─ Handles both 'tags:' and 'tag:' fields              │
│      ├─ Supports array and single value formats             │
│      └─ Error handling for malformed YAML                   │
│                                                             │
│ inline_parser.py                                            │
│   └─ Parse inline hashtags                                  │
│      ├─ extract_tags_from_content() → Regex scanning        │
│      ├─ Handles #tag and #nested/tag formats                │
│      ├─ Position tracking                                   │
│      └─ Excludes code blocks                                │
└─────────────────────────────────────────────────────────────┘
```

### Operations Layer

```
┌─────────────────────────────────────────────────────────────┐
│ tagex/core/operations/                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ tag_operations.py                                           │
│   └─ TagOperationEngine (Abstract Base Class)               │
│      ├─ Dry-run capability (preview mode)                   │
│      ├─ Tag type filtering (frontmatter/inline/both)        │
│      ├─ Operation logging with file hashes                  │
│      ├─ File modification tracking                          │
│      ├─ Parser-based tag transformation                     │
│      └─ Error handling and statistics                       │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Concrete Operation Classes                              │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ RenameOperation                                         │ │
│ │   └─ Rename single tag across vault                     │ │
│ │                                                         │ │
│ │ MergeOperation                                          │ │
│ │   └─ Consolidate multiple tags into one                 │ │
│ │                                                         │ │
│ │ DeleteOperation                                         │ │
│ │   └─ Remove tags entirely from vault                    │ │
│ │                                                         │ │
│ │ AddTagsOperation                                        │ │
│ │   └─ Add tags to specific notes                         │ │
│ │      ├─ Handles notes with no frontmatter               │ │
│ │      ├─ Adds tags field if missing                      │ │
│ │      ├─ Appends to existing tags                        │ │
│ │      └─ Deduplicates tags                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ fix_duplicates.py                                           │
│   └─ DuplicateTagsFixer                                     │
│      ├─ Detects multiple 'tags:' fields                     │
│      ├─ Consolidates into single field                      │
│      ├─ Creates .bak backups                                │
│      ├─ Validates fixes                                     │
│      └─ Dry-run support                                     │
│                                                             │
│ All operations follow safe-by-default pattern:              │
│   - Dry-run is default mode                                 │
│   - --execute flag required to apply changes                │
│   - File hashing for integrity checks                       │
│   - Operation logs saved to current directory               │
└─────────────────────────────────────────────────────────────┘
```

### Analysis Layer

```
┌─────────────────────────────────────────────────────────────┐
│ tagex/analysis/                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ pair_analyzer.py                                            │
│   └─ Tag co-occurrence analysis                             │
│      ├─ analyze_tag_relationships() → Pair counts           │
│      ├─ find_tag_clusters() → Natural groupings             │
│      └─ Hub tag identification                              │
│                                                             │
│ merge_analyzer.py                                           │
│   └─ TF-IDF embedding-based similarity                      │
│      ├─ build_tag_stats() → Tag statistics                  │
│      ├─ suggest_merges() → Multiple approaches              │
│      │   ├─ Similar names (string similarity)               │
│      │   ├─ Semantic duplicates (TF-IDF vectors)            │
│      │   ├─ High file overlap                               │
│      │   └─ Variant patterns (morphological)                │
│      └─ print_merge_suggestions()                           │
│                                                             │
│ breadth_analyzer.py                                         │
│   └─ Tag quality assessment                                 │
│      ├─ analyze_tag_quality() → Overbroad detection         │
│      ├─ Specificity scoring                                 │
│      └─ Refinement suggestions                              │
│                                                             │
│ synonym_analyzer.py                                         │
│   └─ Semantic synonym detection                             │
│      ├─ detect_synonyms_by_semantics()                      │
│      │   └─ Uses sentence-transformers embeddings           │
│      ├─ detect_related_tags()                               │
│      │   └─ Co-occurrence based (Jaccard similarity)        │
│      └─ find_acronym_expansions()                           │
│          └─ Pattern matching for abbreviations              │
│                                                             │
│ plural_normalizer.py                                        │
│   └─ Plural/singular variant detection                      │
│      ├─ normalize_plural_forms()                            │
│      │   ├─ Regular patterns (-s, -es, -ies)                │
│      │   ├─ Irregular plurals (child/children)              │
│      │   └─ Complex patterns (-ves/-f)                      │
│      ├─ normalize_compound_plurals()                        │
│      │   └─ Handles hyphenated compounds                    │
│      └─ get_preferred_form()                                │
│          └─ Usage-based, plural, or singular preference     │
│                                                             │
│ singleton_analyzer.py                                       │
│   └─ SingletonAnalyzer class                                │
│      ├─ Merges tags used only once                          │
│      ├─ String similarity (typo detection)                  │
│      ├─ Semantic similarity (true synonyms)                 │
│      └─ One-directional: singleton → frequent tag           │
│                                                             │
│ content_analyzer.py                                         │
│   └─ ContentAnalyzer class                                  │
│      ├─ Analyzes note content                               │
│      ├─ Suggests tags from existing vocabulary              │
│      ├─ Semantic embeddings (sentence-transformers)         │
│      ├─ Keyword fallback (when embeddings unavailable)      │
│      ├─ Excludes auto-generated tags                        │
│      └─ Targets notes with < min_tags threshold             │
│                                                             │
│ recommendations.py                                          │
│   └─ RecommendationsEngine class                            │
│      ├─ Consolidates all analyzer suggestions               │
│      ├─ Runs multiple analyzers in priority order:          │
│      │   1. User-defined synonyms (highest priority)        │
│      │   2. Semantic synonyms                               │
│      │   3. Plural variants                                 │
│      │   4. Singleton merges                                │
│      ├─ Deduplicates operations                             │
│      ├─ Filters conflicts with user-defined synonyms        │
│      ├─ Applies exclusion rules                             │
│      └─ Exports to YAML operations file                     │
└─────────────────────────────────────────────────────────────┘
```

### Configuration System

```
┌─────────────────────────────────────────────────────────────┐
│ tagex/config/                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Configuration stored in .tagex/ directory within vault:     │
│                                                             │
│ .tagex/                                                     │
│   ├─ config.yaml        → General settings                  │
│   ├─ synonyms.yaml      → User-defined synonym mappings     │
│   ├─ exclusions.yaml    → Tags to exclude from operations   │
│   └─ README.md          → Configuration documentation       │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Configuration Modules                                   │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │                                                         │ │
│ │ plural_config.py                                        │ │
│ │   └─ PluralConfig class                                 │ │
│ │      ├─ Preference modes: usage, plural, singular       │ │
│ │      ├─ Usage ratio threshold                           │ │
│ │      └─ from_vault() → Load from .tagex/config.yaml     │ │
│ │                                                         │ │
│ │ synonym_config.py                                       │ │
│ │   └─ SynonymConfig class                                │ │
│ │      ├─ Load user-defined synonyms                      │ │
│ │      ├─ get_canonical() → Map variant → canonical       │ │
│ │      ├─ get_all_groups() → All synonym groups           │ │
│ │      └─ Highest priority in recommendations             │ │
│ │                                                         │ │
│ │ exclusions_config.py                                    │ │
│ │   └─ ExclusionsConfig class                             │ │
│ │      ├─ exclude_tags: Never merge (proper nouns, etc.)  │ │
│ │      ├─ auto_generated_tags: Never suggest              │ │
│ │      ├─ is_excluded() → Check merge exclusion           │ │
│ │      ├─ is_auto_generated() → Check tool tag            │ │
│ │      ├─ is_suggestion_excluded()                        │ │
│ │      └─ is_operation_excluded()                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Configuration commands:                                     │
│   tagex init [vault_path]     → Create .tagex/ directory    │
│   tagex config validate [vault_path] → Check config validity│
└─────────────────────────────────────────────────────────────┘
```

### Utilities Layer

```
┌─────────────────────────────────────────────────────────────┐
│ tagex/utils/                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ file_discovery.py                                           │
│   └─ find_markdown_files()                                  │
│      ├─ Pattern-based file enumeration                      │
│      ├─ .obsidian directory exclusion                       │
│      ├─ Dotfile filtering (.DS_Store, etc.)                 │
│      ├─ Configurable exclude patterns                       │
│      └─ Relative path calculation                           │
│                                                             │
│ tag_normalizer.py                                           │
│   └─ Tag validation and filtering                           │
│      ├─ is_valid_tag() → Comprehensive validation           │
│      ├─ normalize_tag() → Case/whitespace cleanup           │
│      ├─ Filters pure numbers                                │
│      ├─ Removes HTML entities                               │
│      ├─ Blocks technical patterns                           │
│      ├─ Character set validation                            │
│      └─ Minimum length checks                               │
│                                                             │
│ vault_maintenance.py                                        │
│   └─ BakRemover class                                       │
│      ├─ Find .bak backup files                              │
│      ├─ Recursive directory scanning                        │
│      ├─ Safe deletion with preview mode                     │
│      └─ Statistics reporting                                │
│                                                             │
│ input_handler.py                                            │
│   └─ Dual input mode support                                │
│      ├─ load_or_extract_tags()                              │
│      ├─ get_input_type() → Vault or JSON                    │
│      └─ Auto-extract or load from file                      │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Pipelines

### Standard Extraction Pipeline

```
Input: Obsidian Vault Path
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: File Discovery                                      │
│                                                             │
│ find_markdown_files()                                       │
│   ├─ Scan for *.md files                                    │
│   ├─ Apply exclusion patterns (.obsidian, dotfiles)         │
│   └─ Build file list with relative paths                    │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Tag Extraction (Per File)                           │
│                                                             │
│ For each markdown file:                                     │
│   ├─ Read file content                                      │
│   ├─ Parse frontmatter (frontmatter_parser.py)              │
│   │   └─ Extract tags from YAML                             │
│   ├─ Parse inline tags (inline_parser.py)                   │
│   │   └─ Extract #hashtags from content                     │
│   └─ Validate and normalize tags                            │
│       ├─ Filter noise (pure numbers, HTML entities)         │
│       ├─ Validate character sets                            │
│       └─ Check minimum length                               │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Aggregation                                         │
│                                                             │
│   ├─ Tag counts (frequency)                                 │
│   ├─ File associations (which files have which tags)        │
│   └─ Statistics collection                                  │
│       ├─ Total files processed                              │
│       ├─ Total unique tags                                  │
│       ├─ Processing errors                                  │
│       └─ Tag type breakdown                                 │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Output Formatting                                   │
│                                                             │
│ Choose format:                                              │
│   ├─ JSON (plugin compatible)                               │
│   ├─ CSV (spreadsheet analysis)                             │
│   └─ TEXT (human readable)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Tag Operations Pipeline

```
Input: Vault + Operation Parameters
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Operation Setup                                     │
│                                                             │
│   ├─ Initialize TagOperationEngine subclass                 │
│   ├─ Create operation log structure                         │
│   └─ Set preview mode (default: enabled)                    │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: File Discovery & Filtering                          │
│                                                             │
│   ├─ Find all markdown files                                │
│   ├─ Extract tags from each file                            │
│   └─ Filter to files containing target tags only            │
│       (Smart processing: skip files without target tags)    │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Tag Transformation (Per File)                       │
│                                                             │
│ For each file with target tags:                             │
│   ├─ Read file content                                      │
│   ├─ Calculate file hash (integrity check)                  │
│   ├─ Transform tags using operation logic                   │
│   │   ├─ Rename: old → new                                  │
│   │   ├─ Merge: [tag1, tag2] → target                       │
│   │   ├─ Delete: remove tags                                │
│   │   └─ AddTags: append to frontmatter                     │
│   ├─ Validate changes                                       │
│   └─ Write back (if --execute flag set)                     │
│       ├─ Preserve formatting                                │
│       ├─ Update operation log                               │
│       └─ Track statistics                                   │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Operation Logging                                   │
│                                                             │
│   ├─ Generate operation report                              │
│   ├─ Save log to current directory (not vault)              │
│   │   └─ tagex-<operation>-<timestamp>.json                 │
│   └─ Display summary statistics                             │
│       ├─ Files modified                                     │
│       ├─ Tags modified                                      │
│       ├─ Errors encountered                                 │
│       └─ Dry-run reminder                                   │
└─────────────────────────────────────────────────────────────┘
```

### Unified Recommendations Workflow

```
Input: Vault Path
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Tag Extraction                                      │
│                                                             │
│ Standard extraction pipeline:                               │
│   └─ Extract all tags → tag_stats dictionary                │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Run Analyzers (Priority Order)                      │
│                                                             │
│ RecommendationsEngine runs enabled analyzers:               │
│                                                             │
│ 1. User-defined synonyms (HIGHEST PRIORITY)                 │
│    └─ Load from .tagex/synonyms.yaml                        │
│    └─ Create merge operations: variants → canonical         │
│                                                             │
│ 2. Semantic synonyms (if sentence-transformers available)   │
│    └─ Detect synonym pairs using embeddings                 │
│    └─ Find acronym expansions                               │
│                                                             │
│ 3. Plural variants                                          │
│    └─ Group singular/plural forms                           │
│    └─ Choose preferred form (usage/plural/singular)         │
│                                                             │
│ 4. Singleton merges                                         │
│    └─ Find singleton tags (count == 1)                      │
│    └─ Match to frequent tags via:                           │
│        ├─ String similarity (typos)                         │
│        └─ Semantic similarity (synonyms)                    │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Consolidation                                       │
│                                                             │
│   ├─ Deduplicate operations                                 │
│   │   └─ Keep highest confidence version                    │
│   ├─ Filter conflicts with user-defined synonyms            │
│   │   └─ User config takes absolute precedence              │
│   └─ Apply exclusion rules                                  │
│       └─ Remove operations involving excluded tags          │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Export to YAML Operations File                      │
│                                                             │
│ operations.yaml format:                                     │
│   operations:                                               │
│     - type: merge                                           │
│       source: [tag1, tag2]                                  │
│       target: canonical-tag                                 │
│       reason: "Semantic synonyms (similarity: 0.850)"       │
│       enabled: true                                         │
│       metadata:                                             │
│         confidence: 0.850                                   │
│         source_analyzer: synonyms                           │
│                                                             │
│ Each operation includes:                                    │
│   ├─ Operation type (merge/rename/delete/add_tags)          │
│   ├─ Source and target tags                                 │
│   ├─ Human-readable reason                                  │
│   ├─ Enabled flag (user can disable)                        │
│   └─ Metadata (confidence, source analyzer)                 │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: User Review and Apply                               │
│                                                             │
│ User edits operations.yaml:                                 │
│   ├─ Set enabled: false to skip operations                  │
│   ├─ Modify source/target tags                              │
│   ├─ Delete unwanted operations                             │
│   └─ Reorder (executed top-to-bottom)                       │
│                                                             │
│ Apply operations:                                           │
│   tagex tag apply operations.yaml          (preview)        │
│   tagex tag apply operations.yaml --execute (apply)         │
└─────────────────────────────────────────────────────────────┘
```

### Content-Based Tag Suggestions Workflow

```
Input: Vault Path + Target Criteria
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Extract Tag Vocabulary                              │
│                                                             │
│   ├─ Extract all tags from vault                            │
│   ├─ Filter to frequent tags (>= min_frequency)             │
│   └─ Exclude auto-generated tags                            │
│       └─ From .tagex/exclusions.yaml                        │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Find Target Notes                                   │
│                                                             │
│ Criteria:                                                   │
│   ├─ Notes with < min_tag_count tags (default: 2)           │
│   └─ Optional: <= max_tag_count                             │
│   └─ Optional: Specific paths/globs                         │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Content Analysis (Per Note)                         │
│                                                             │
│ Extract meaningful content:                                 │
│   ├─ Filename (repeated for emphasis)                       │
│   ├─ Headers (higher weight)                                │
│   └─ First 3 paragraphs (up to 500 chars)                   │
│   └─ Exclude code blocks                                    │
│                                                             │
│ Generate suggestions:                                       │
│                                                             │
│ If semantic model available (sentence-transformers):        │
│   ├─ Embed note content                                     │
│   ├─ Embed all candidate tags                               │
│   └─ Calculate cosine similarity                            │
│       └─ Return top N tags above min_confidence             │
│                                                             │
│ Fallback (keyword matching):                                │
│   ├─ Split tags into parts                                  │
│   ├─ Count matches in content                               │
│   └─ Confidence = match_ratio + frequency_boost             │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Export Suggestions                                  │
│                                                             │
│ suggestions.yaml format:                                    │
│   operations:                                               │
│     - type: add_tags                                        │
│       source: [suggested-tag1, suggested-tag2]              │
│       target: path/to/note.md                               │
│       reason: "Content-based suggestion (avg conf: 0.72)"   │
│       enabled: true                                         │
│       metadata:                                             │
│         file: path/to/note.md                               │
│         current_tags: []                                    │
│         confidences: [0.75, 0.69, 0.72]                     │
│         methods: [semantic, semantic, semantic]             │
│                                                             │
│ Apply with:                                                 │
│   tagex tag apply suggestions.yaml --execute                │
└─────────────────────────────────────────────────────────────┘
```

### Frontmatter Repair Flow

```
Input: Vault Path or File List
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: File Discovery                                      │
│                                                             │
│   ├─ If vault directory: find all .md files                 │
│   ├─ If single file: process that file                      │
│   └─ If filelist: read paths from text file                 │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Detect Duplicates (Per File)                        │
│                                                             │
│ DuplicateTagsFixer logic:                                   │
│   ├─ Parse frontmatter                                      │
│   ├─ Find all lines starting with 'tags:'                   │
│   └─ If multiple 'tags:' fields found:                      │
│       ├─ Collect all tag values                             │
│       ├─ Consolidate into single 'tags:' field              │
│       └─ Use last non-empty value                           │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Fix and Validate                                    │
│                                                             │
│ If preview mode (default):                                  │
│   └─ Show changes only                                      │
│                                                             │
│ If --execute flag set:                                      │
│   ├─ Create .bak backup                                     │
│   ├─ Write fixed content                                    │
│   ├─ Re-parse to validate fix                               │
│   └─ Restore from backup if validation fails                │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Reporting                                           │
│                                                             │
│   ├─ Total files processed                                  │
│   ├─ Files with duplicates                                  │
│   ├─ Files fixed                                            │
│   └─ Errors encountered                                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### Safe by Default

All write operations follow the safe-by-default pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                     SAFE BY DEFAULT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DEFAULT: Dry-run (preview) mode                             │
│   ├─ Shows what would change                                │
│   ├─ No files modified                                      │
│   └─ Clear output formatting                                │
│                                                             │
│ EXPLICIT: --execute flag required                           │
│   ├─ User must explicitly opt-in to changes                 │
│   ├─ Big obvious header shows mode                          │
│   └─ Confirmation in output                                 │
│                                                             │
│ SAFEGUARDS:                                                 │
│   ├─ File hash integrity checks                             │
│   ├─ Operation logs saved (audit trail)                     │
│   ├─ Backup files created (.bak)                            │
│   └─ Error handling with rollback                           │
└─────────────────────────────────────────────────────────────┘

Example:
  tagex tag rename /vault old new        → Preview only
  tagex tag rename /vault old new --execute  → Actually rename
```

### Current Directory Defaults

```
┌─────────────────────────────────────────────────────────────┐
│               CURRENT DIRECTORY DEFAULTS                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Commands default to current directory when vault_path       │
│ argument is omitted:                                        │
│                                                             │
│   tagex stats               → Stats for ./                  │
│   tagex health              → Health for ./                 │
│   tagex init                → Initialize ./.tagex/          │
│   tagex config validate            → Validate ./.tagex/     │
│   tagex tag export        → Extract from ./                 │
│   tagex analyze plurals     → Analyze ./                    │
│                                                             │
│ This allows for convenient usage when working within        │
│ a vault directory.                                          │
└─────────────────────────────────────────────────────────────┘
```

### Dual Input Modes

```
┌─────────────────────────────────────────────────────────────┐
│                   DUAL INPUT MODES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ All analyze commands accept either:                         │
│                                                             │
│ 1. VAULT PATH (auto-extract)                                │
│    tagex analyze merges /vault                              │
│      └─ Extracts tags → runs analysis                       │
│                                                             │
│ 2. JSON FILE (pre-extracted data)                           │
│    tagex analyze merges tags-export.json                    │
│      └─ Loads tags → runs analysis                          │
│                                                             │
│ Benefits:                                                   │
│   ├─ Separation of extraction and analysis                  │
│   ├─ Faster iteration during analysis development           │
│   └─ Can analyze pre-filtered datasets                      │
└─────────────────────────────────────────────────────────────┘
```

### Modular Parsing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                MODULAR PARSING SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ File Content                                                │
│      │                                                      │
│      ├─► frontmatter_parser.py ──┐                          │
│      │                            │                         │
│      └─► inline_parser.py ────────┼──► Aggregation          │
│                 │                 │                         │
│      [future_parser.py] ──────────┘                         │
│                 │                                           │
│          Extension Point                                    │
│                                                             │
│ Each parser is independent and can be:                      │
│   ├─ Enabled/disabled via --tag-types                       │
│   ├─ Extended with new parsers                              │
│   └─ Tested in isolation                                    │
└─────────────────────────────────────────────────────────────┘
```

### Error Resilience Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                  ERROR RESILIENCE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Process File                                                │
│      │                                                      │
│      ├─ Error? ──No──► Add to Results                       │
│      │                      │                               │
│      │                      ▼                               │
│      │               Continue to Next File                  │
│      │                                                      │
│      └─ Error? ──Yes─► Log Error & Continue                 │
│                              │                              │
│                              ▼                              │
│                       Continue to Next File                 │
│                                                             │
│ Strategy:                                                   │
│   ├─ Never fail entire operation for single file error      │
│   ├─ Log all errors for review                              │
│   ├─ Track error statistics                                 │
│   └─ Exit code reflects error count                         │
└─────────────────────────────────────────────────────────────┘
```

### Tag Type Filtering System

```
┌─────────────────────────────────────────────────────────────┐
│              TAG TYPE FILTERING                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Global --tag-types parameter (all commands):                │
│                                                             │
│   --tag-types frontmatter  (DEFAULT)                        │
│     └─ Process only YAML frontmatter tags                   │
│                                                             │
│   --tag-types inline                                        │
│     └─ Process only #hashtags in content                    │
│                                                             │
│   --tag-types both                                          │
│     └─ Process both frontmatter and inline tags             │
│                                                             │
│ Applied to:                                                 │
│   ├─ Tag extraction (tagex tag export)                      │
│   ├─ All operations (rename, merge, delete)                 │
│   └─ All analyzers (pairs, merge, quality, etc.)            │
│                                                             │
│ Implementation:                                             │
│   if tag_types in ('both', 'frontmatter'):                  │
│     ├─► frontmatter_parser                                  │
│                                                             │
│   if tag_types in ('both', 'inline'):                       │
│     └─► inline_parser                                       │
└─────────────────────────────────────────────────────────────┘
```

### Configuration-Driven Behavior

```
┌─────────────────────────────────────────────────────────────┐
│           CONFIGURATION-DRIVEN BEHAVIOR                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ .tagex/config.yaml                                          │
│   └─ Plural preference (usage/plural/singular)              │
│   └─ Usage ratio thresholds                                 │
│   └─ Loaded automatically per vault                         │
│                                                             │
│ .tagex/synonyms.yaml                                        │
│   └─ User-defined canonical forms                           │
│   └─ HIGHEST priority in recommendations                    │
│   └─ Prevents conflicts with auto-suggestions               │
│                                                             │
│ .tagex/exclusions.yaml                                      │
│   └─ exclude_tags: Never merge (proper nouns)               │
│   └─ auto_generated_tags: Never suggest                     │
│   └─ Filters applied to all operations and suggestions      │
│                                                             │
│ Command-line overrides:                                     │
│   └─ --prefer option overrides config.yaml preference       │
└─────────────────────────────────────────────────────────────┘
```

## Extension Points

The architecture is designed for extensibility at multiple levels:

### 1. New Tag Operations

Extend `TagOperationEngine` base class:

```python
from tagex.core.operations.tag_operations import TagOperationEngine

class CustomOperation(TagOperationEngine):
    def transform_tags(self, content: str, file_path: str) -> str:
        # Your custom tag transformation logic
        pass

    def get_operation_log_name(self) -> str:
        return "custom-op"
```

### 2. New Parsers

Implement parser interface:

```python
# In tagex/core/parsers/custom_parser.py

def extract_tags_from_custom_source(content: str) -> List[str]:
    # Your custom tag extraction logic
    pass
```

Then integrate in `TagExtractor` class.

### 3. New Analyzers

Create analyzer module:

```python
# In tagex/analysis/custom_analyzer.py

def analyze_custom_pattern(
    tag_stats: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    # Your custom analysis logic
    pass
```

Then add to `RecommendationsEngine` if needed.

### 4. New Configuration Options

Extend configuration system:

```python
# In tagex/config/custom_config.py

class CustomConfig:
    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path
        # Load from .tagex/custom.yaml
```

### 5. New Vault Maintenance Commands

Add commands to `vault` group:

```python
@vault.command('custom-cleanup')
@click.argument('vault_path', type=click.Path(exists=True))
@click.option('--execute', is_flag=True)
def custom_cleanup(vault_path, execute):
    """Custom vault cleanup operation."""
    pass
```

### 6. New Output Formats

Add formatters to `output_formatter.py`:

```python
def format_as_custom(tag_data: Dict) -> Any:
    # Your custom format logic
    pass
```

### 7. New Statistics Metrics

Extend statistics calculation:

```python
def calculate_custom_metric(tag_data: Dict) -> float:
    # Your custom metric logic
    pass
```

### 8. New Validation Rules

Extend `tag_normalizer.py`:

```python
def is_valid_custom_tag(tag: str) -> bool:
    # Your custom validation logic
    pass
```

## Module Index

| Module                | Location               | Purpose                                |
| :-------------------- | :--------------------- | :------------------------------------- |
| **CLI Layer**         |
| main.py               | tagex/                 | Command-line interface and entry point |
| **Core Extraction**   |
| core.py               | tagex/core/extractor/  | Main tag extraction engine             |
| output_formatter.py   | tagex/core/extractor/  | Output formatting (JSON/CSV/TXT)       |
| **Parsers**           |
| frontmatter_parser.py | tagex/core/parsers/    | YAML frontmatter tag parsing           |
| inline_parser.py      | tagex/core/parsers/    | Inline hashtag parsing                 |
| **Operations**        |
| tag_operations.py     | tagex/core/operations/ | Base operation engine                  |
| fix_duplicates.py     | tagex/core/operations/ | Duplicate tags field repair            |
| add_tags.py           | tagex/core/operations/ | Add tags to notes                      |
| **Analysis**          |
| pair_analyzer.py      | tagex/analysis/        | Co-occurrence patterns                 |
| merge_analyzer.py     | tagex/analysis/        | TF-IDF similarity detection            |
| breadth_analyzer.py   | tagex/analysis/        | Overbroad tag detection                |
| synonym_analyzer.py   | tagex/analysis/        | Semantic synonym detection             |
| plural_normalizer.py  | tagex/analysis/        | Plural/singular variants               |
| singleton_analyzer.py | tagex/analysis/        | Singleton tag merges                   |
| content_analyzer.py   | tagex/analysis/        | Content-based tag suggestions          |
| recommendations.py    | tagex/analysis/        | Unified recommendations engine         |
| **Configuration**     |
| plural_config.py      | tagex/config/          | Plural preference settings             |
| synonym_config.py     | tagex/config/          | User-defined synonyms                  |
| exclusions_config.py  | tagex/config/          | Tag exclusion rules                    |
| **Utilities**         |
| file_discovery.py     | tagex/utils/           | Markdown file enumeration              |
| tag_normalizer.py     | tagex/utils/           | Tag validation and filtering           |
| vault_maintenance.py  | tagex/utils/           | Backup file cleanup                    |
| input_handler.py      | tagex/utils/           | Dual input mode support                |

## Command Reference

### Tag Operations (8 commands)

| Command                     | Description                  | Safe by Default          |
| :-------------------------- | :--------------------------- | :----------------------- |
| `tagex tag export`        | Extract tags to JSON/CSV/TXT | Read-only                |
| `tagex tag rename`         | Rename tag across vault      | Yes (--execute required) |
| `tagex tag merge`          | Merge multiple tags into one | Yes (--execute required) |
| `tagex tag delete`         | Delete tags from vault       | Yes (--execute required) |
| `tagex tag fix` | Fix duplicate tags: fields   | Yes (--execute required) |
| `tagex tag apply`          | Apply operations from YAML   | Yes (--execute required) |

### Analysis Commands (7 analyzers)

| Analyzer          | Description                   | Requires                        |
| :---------------- | :---------------------------- | :------------------------------ |
| `pairs`           | Tag co-occurrence patterns    | -                               |
| `merge`           | Semantic merge suggestions    | Optional: sklearn               |
| `quality`         | Overbroad tag detection       | -                               |
| `synonyms`        | True synonym detection        | Optional: sentence-transformers |
| `plurals`         | Singular/plural variants      | -                               |
| `suggest`         | Content-based tag suggestions | Optional: sentence-transformers |
| `recommendations` | Unified recommendations (ALL) | Optional: sentence-transformers |

### Vault Maintenance (1 command)

| Command | Description | Safe by Default |
|:--------|:------------|:----------------|
| `cleanup` | Remove .bak backup files | Yes (--execute required) |

### Configuration Commands (2 commands)

| Command    | Description              | Purpose                       |
| :--------- | :----------------------- | :---------------------------- |
| `init`     | Create .tagex/ directory | Setup vault configuration     |
| `validate` | Check config validity    | Verify YAML syntax and values |

### Information Commands (2 commands)

| Command  | Description              | Output                    |
| :------- | :----------------------- | :------------------------ |
| `stats`  | Comprehensive statistics | Text or JSON              |
| `health` | Vault health report      | Recommendations and score |

## Technical Implementation Notes

### File Exclusion System

```
Default exclusions:
  ├─ .obsidian/ directory (Obsidian metadata)
  ├─ .DS_Store files (macOS system files)
  ├─ Files starting with '.' (dotfiles)
  └─ Custom patterns via --exclude option

Configurable via:
  └─ Command-line: --exclude pattern (repeatable)
```

### Tag Validation Rules

```
RULE 1: No pure numbers
  ✗ 123, 456789
  ✓ v1.2, 2024-project

RULE 2: Must start with alphanumeric
  ✗ -tag, _underscore
  ✓ alpha, 3d-model

RULE 3: Filter HTML/Unicode noise
  ✗ &#x, \u200b, &nbsp;
  ✓ clean-text

RULE 4: Block technical patterns
  ✗ a1b2c3d4e5f6, dispatcher, dom-element
  ✓ programming, design-pattern

RULE 5: Must contain letters
  ✗ 123-456, +-*/
  ✓ api2, 3d-graphics

RULE 6: Valid character set only
  ✗ tag@symbol, tag#hash
  ✓ tag_name, category/subcategory

Can be disabled: --no-filter flag
```

### Semantic Analysis Requirements

```
sentence-transformers package required for:
  ├─ tagex analyze synonyms (semantic mode)
  ├─ tagex analyze suggest (content analysis)
  ├─ tagex analyze recommendations (synonym analyzer)
  └─ singleton analyzer (semantic similarity)

Model: all-MiniLM-L6-v2
  ├─ Lightweight (80MB)
  ├─ Fast inference
  └─ Good balance of quality/speed

Fallbacks when unavailable:
  ├─ Keyword matching for content suggestions
  ├─ Co-occurrence analysis for synonyms
  └─ String similarity only for singletons
```

### Operation Log Format

```json
{
  "operation": "tag-rename",
  "operation_type": "rename",
  "dry_run": false,
  "timestamp": "2025-10-29T10:30:00",
  "vault_path": "/path/to/vault",
  "parameters": {
    "old_tag": "old-name",
    "new_tag": "new-name",
    "tag_types": "frontmatter"
  },
  "stats": {
    "files_processed": 42,
    "files_modified": 18,
    "tags_modified": 24,
    "errors": 0
  },
  "modifications": [
    {
      "file": "path/to/note.md",
      "changes": [
        {
          "type": "frontmatter_tag_renamed",
          "old": "old-name",
          "new": "new-name"
        }
      ]
    }
  ]
}
```

## Performance Characteristics

| Operation           | Complexity | Notes                            |
| :------------------ | :--------- | :------------------------------- |
| Tag extraction      | O(n)       | Linear in file count             |
| Tag operations      | O(m)       | Linear in files with target tags |
| Pair analysis       | O(n²)      | All tag combinations             |
| Semantic similarity | O(n²)      | With embeddings cache            |
| Content suggestions | O(n*m)     | n=notes, m=candidate tags        |

## Summary

Tagex provides a comprehensive, modular architecture for Obsidian tag management with:

- **Safe operations**: Dry-run by default, --execute required
- **Command groups**: tags, analyze, vault for logical organization
- **Multiple analyzers**: 7 specialized analysis tools
- **Unified workflow**: recommendations → YAML → apply
- **Configuration system**: .tagex/ directory for vault-specific settings
- **Extensible design**: Clear extension points at all layers
- **Semantic intelligence**: Optional sentence-transformers for advanced analysis
- **Content-aware**: Suggests tags based on note content
- **Error resilient**: Continues processing on individual failures

All components follow consistent patterns and can be extended or customized as needed.
