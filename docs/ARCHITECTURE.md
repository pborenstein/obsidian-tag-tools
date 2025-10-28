# Obsidian Tag Management Tool - Architecture



## Core Components

```
Markdown Files → Tag Extraction → Analysis → Operations
                      ↓              ↓            ↓
                 Tag Output   Relationships   Tag Modify


┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   tagex/        │      │ tagex/core/     │      │ tagex/core/     │
│                 │      │                 │      │                 │
│ ┌─────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │ Click CLI   │ │─────►│ │TagExtractor │ │─────►│ │frontmatter  │ │
│ │ Multi-Cmd   │ │      │ │   Engine    │ │      │ │   parser    │ │
│ └─────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │
│                 │      │                 │      │                 │
│ ┌─────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │ Console     │ │      │ │ Statistics  │ │      │ │   inline    │ │
│ │ Script      │ │      │ │  Tracking   │ │      │ │   parser    │ │
│ └─────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ tagex/core/      │      │output_formatter │      │tagex/analysis/  │
│                  │      │                 │      │                 │
│ ┌──────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │TagOperation  │ │      │ │ JSON Format │ │      │ │pair_analyzer│ │
│ │   Engine     │ │      │ │             │ │      │ │merge_       │ │
│ └──────────────┘ │      │ └─────────────┘ │      │ │ analyzer    │ │
│                  │      │                 │      │ └─────────────┘ │
│ ┌──────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │Rename/Merge/ │ │      │ │ CSV & Text  │ │      │ │breadth_     │ │
│ │Delete Ops    │ │      │ │  Formats    │ │      │ │ analyzer    │ │
│ └──────────────┘ │      │ └─────────────┘ │      │ │synonym_     │ │
│                  │      │                 │      │ │ analyzer    │ │
└──────────────────┘      └─────────────────┘      └─────────────────┘
       │                        │                        │
       ▼                        ▼                        ▼
┌──────────────────┐      ┌─────────────────┐
│  tagex/config/   │      │ tagex/utils/    │
│                  │      │                 │
│ ┌──────────────┐ │      │ ┌─────────────┐ │
│ │  synonym     │ │      │ │file_discovery│ │
│ │  config      │ │      │ │tag_normalizer│ │
│ └──────────────┘ │      │ │plural_       │ │
│                  │      │ │ normalizer   │ │
└──────────────────┘      └─────────────────┘
```

## Data Flow Pipeline

```
Input: Obsidian Vault
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: File Discovery                                         │
│                                                                 │
│  find_markdown_files()                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  *.md files │───►│Pattern      │───►│Filtered     │          │
│  │    scan     │    │Exclusions   │    │File List    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Tag Extraction (Per File)                              │
│                                                                 │
│  File Processing Loop:                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Read File    │───►│Extract      │───►│Extract      │          │
│  │Content      │    │Frontmatter  │    │Inline Tags  │          │
│  └─────────────┘    │YAML Tags    │    │(#hashtags)  │          │
│                     └─────────────┘    └─────────────┘          │
│                              │                   │              │
│                              ▼                   ▼              │
│                     ┌─────────────────────────────────┐         │
│                     │ Tag Validation & Normalization  │         │
│                     │ • Filter pure numbers           │         │
│                     │ • Remove HTML entities          │         │
│                     │ • Filter technical patterns     │         │
│                     │ • Validate character sets       │         │
│                     │ • Check minimum length          │         │
│                     └─────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Aggregation                                            │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Tag Counts   │───►│File         │───►│Statistics   │          │
│  │Per Tag      │    │Associations │    │Collection   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Output Formatting                                      │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   JSON      │    │    CSV      │    │    TEXT     │          │
│  │ (Plugin     │    │(Spreadsheet │    │ (Human      │          │
│  │Compatible)  │    │ Analysis)   │    │ Readable)   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### Main Pipeline (`tagex/main.py`)
```
┌─────────────────────────────────────────────┐
│              MAIN CONTROLLER                │
├─────────────────────────────────────────────┤
│ • Vault-first CLI using Click groups        │
│ • Global --tag-types option handling        │
│ • Console script entry point (tagex)        │
│ • Tag filtering by default (--no-filter)    │
│ • Orchestrates extraction workflow          │
│ • Coordinates tag operations                │
│ • Handles logging configuration             │
│ • Error reporting and exit codes            │
│ • Output file management                    │
└─────────────────────────────────────────────┘

Commands:
┌─────────────────────────────────────────────┐
│ tagex /vault extract → TagExtractor class   │
│ tagex /vault rename  → RenameOperation class│
│ tagex /vault merge   → MergeOperation class │
│ tagex /vault delete  → DeleteOperation class│
│                                             │
│ Global --tag-types option affects all       │
└─────────────────────────────────────────────┘
```

### Tag Extraction Engine (`tagex/core/extractor/core.py`)
```
┌─────────────────────────────────────────────┐
│             TAGEXTRACTOR CLASS              │
├─────────────────────────────────────────────┤
│ • Processes vault files sequentially        │
│ • Aggregates tag data from all sources      │
│ • Selective tag type filtering capability   │
│ • Maintains processing statistics           │
│ • Coordinates parser modules                │
│ • Handles file processing errors            │
└─────────────────────────────────────────────┘
```

### Parser Modules (`tagex/core/parsers/`)
```
┌─────────────────────┐    ┌─────────────────────┐
│tagex/core/parsers/  │    │ tagex/core/parsers/ │
│ frontmatter_parser  │    │   inline_parser     │
├─────────────────────┤    ├─────────────────────┤
│ • YAML header       │    │ • Hashtag scanning  │
│   parsing           │    │ • Content regex     │
│ • tags/tag arrays   │    │   matching          │
│ • Validation        │    │ • Tag validation    │
│ • Error handling    │    │ • Position tracking │
└─────────────────────┘    └─────────────────────┘
```

### Utility Functions (`tagex/utils/`)
```
┌─────────────────────┐    ┌─────────────────────┐
│tagex/utils/         │    │ tagex/utils/        │
│  file_discovery     │    │  tag_normalizer     │
├─────────────────────┤    ├─────────────────────┤
│ • Markdown file     │    │ • Case normalization│
│   enumeration       │    │ • Whitespace        │
│ • Pattern exclusion │    │   cleanup           │
│ • Relative path     │    │ • Deduplication     │
│   calculation       │    │ • Character encoding│
│                     │    │ • Tag validation    │
│                     │    │ • Noise filtering   │
└─────────────────────┘    └─────────────────────┘
```

### Tag Operations Engine (`tagex/core/operations/tag_operations.py`)
```
┌─────────────────────────────────────────────┐
│           TAG OPERATION ENGINE              │
├─────────────────────────────────────────────┤
│ TagOperationEngine (Abstract Base Class)    │
│ ├─ Dry-run capability for safe previews     │
│ ├─ Tag type filtering (frontmatter/inline)  │
│ ├─ Operation logging with integrity checks  │
│ ├─ File modification tracking               │
│ ├─ Parser-based tag transformation          │
│ └─ Error handling and statistics            │
│                                             │
│ RenameOperation                             │
│   └─ Rename single tag across vault         │
│                                             │
│ MergeOperation                              │
│   └─ Consolidate multiple tags into one     │
│                                             │
│ DeleteOperation                             │
│   └─ Remove tags entirely from vault        │
└─────────────────────────────────────────────┘
```

### Output Formatter (`tagex/core/extractor/output_formatter.py`)
```
┌─────────────────────────────────────────────┐
│            OUTPUT PROCESSORS                │
├─────────────────────────────────────────────┤
│ format_as_plugin_json()                     │
│   └─ Obsidian plugin compatible structure   │
│                                             │
│ format_as_csv()                             │
│   └─ Tabular data for spreadsheet analysis  │
│                                             │
│ format_as_text()                            │
│   └─ Human-readable summary format          │
│                                             │
│ save_output() / print_summary()             │
│   └─ File I/O and statistics display        │
└─────────────────────────────────────────────┘
```

## Key Design Patterns

### Modular Parsing Architecture
```
File Input
    │
    ├─► tagex/core/parsers/frontmatter_parser.py ──┐
    │                                              │
    └─► tagex/core/parsers/inline_parser.py ───────┼─► Aggregation
                                │
        [future_parser.py] ─────┘
                │
        Future Extension Point
```

### Error Resilience Strategy
```
┌─────────────┐    Error?    ┌─────────────┐
│Process File │─────No──────►│Add to       │
│             │              │Results      │
└─────────────┘              └─────────────┘
      │                            │
      │Yes                         │
      ▼                            │
┌─────────────┐                    │
│Log Error &  │                    │
│Continue     │────────────────────┤
│Processing   │                    │
└─────────────┘                    ▼
                              ┌─────────────┐
                              │Continue to  │
                              │Next File    │
                              └─────────────┘
```

### Configurable Output Pipeline
```
Tag Data
   │
   ├─► JSON ──► stdout/file
   │
   ├─► CSV ───► file
   │
   └─► TEXT ──► stdout/file
```

### Tag Type Filtering System
```
Input: Global --tag-types parameter
   │
   ├─► 'both' ──────────► Process frontmatter + inline
   │
   ├─► 'frontmatter' (default) ────► Process YAML tags only
   │
   └─► 'inline' ─────────► Process hashtags only

CLI Structure:
tagex [--tag-types TYPE] VAULT_PATH COMMAND [OPTIONS]

Tag Processing Flow:
┌─────────────────────────────────────────────┐
│  File Content → Parser Selection            │
├─────────────────────────────────────────────┤
│ if tag_types in ('both', 'frontmatter'):    │
│   ├─► tagex/core/parsers/frontmatter_parser │
│                                             │
│ if tag_types in ('both', 'inline'):         │
│   └─► tagex/core/parsers/inline_parser      │
└─────────────────────────────────────────────┘
```

## Tag Validation System

The tool includes tag validation to filter out noise and technical artifacts:

### Validation Rules (`tagex/utils/tag_normalizer.py`)

```
┌─────────────────────────────────────────────┐
│                TAG FILTER                   │
├─────────────────────────────────────────────┤
│ RULE 1: No pure numbers                     │
│   ✗ 123, 456789                             │
│   ✓ v1.2, 2024-project                      │
│                                             │
│ RULE 2: Must start with alphanumeric        │
│   ✗ -tag, _underscore                       │
│   ✓ alpha, 3d-model                         │
│                                             │
│ RULE 3: Filter HTML/Unicode noise           │
│   ✗ &#x, \u200b, &nbsp;                     │
│   ✓ clean-text                              │
│                                             │
│ RULE 4: Block technical patterns            │
│   ✗ a1b2c3d4e5f6, dispatcher, dom-element   │
│   ✓ programming, design-pattern             │
│                                             │
│ RULE 5: Must contain letters                │
│   ✗ 123-456, +-*/                           │
│   ✓ api2, 3d-graphics                       │
│                                             │
│ RULE 6: Valid character set only            │
│   ✗ tag@symbol, tag#hash                    │
│   ✓ tag_name, category/subcategory          │
└─────────────────────────────────────────────┘
```

### Filtering by Default

- **Main extractor**: Filters tags by default, use `--no-filter` for raw output
- **Analysis tools**: Include filter options with `--no-filter` override
- **Console script**: Available as `tagex` command after installation

### Installation & Usage

| Command | Description |
|:--------|:------------|
| `uv tool install --editable .` | Install as editable tool |
| `tagex /vault rename old-tag new-tag` | Tag rename (preview by default) |
| `tagex /vault merge tag1 tag2 --into combined-tag --execute` | Tag merge (actually apply) |
| `tagex /vault delete unwanted-tag another-tag` | Tag delete (preview by default) |
| `tagex --tag-types frontmatter /vault rename work project` | Rename frontmatter tags only (preview) |
| `tagex --tag-types inline /vault delete temp-tag --execute` | Delete inline tags (actually apply) |

## Tag Operations Architecture

### Operation Flow Pipeline

```
Input: Vault + Operation Parameters
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Operation Setup                                        │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Initialize   │───►│Create       │───►│Setup        │          │
│  │Operation    │    │Log Structure│    │Dry-run Mode │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: File Discovery & Filtering                             │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Find Markdown│───►│Filter by    │───►│Build Target │          │
│  │Files        │    │Tag Presence │    │File List    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Tag Transformation (Per File)                          │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Read File &  │───►│Transform    │───►│Validate     │          │
│  │Calculate    │    │Tags Using   │    │Changes      │          │
│  │Hash         │    │Parsers      │    │             │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│                              │                   │              │
│                              ▼                   ▼              │
│                     ┌─────────────────────────────────┐         │
│                     │ Write Back (if not dry-run)     │         │
│                     │ • Preserve original formatting  │         │
│                     │ • Log modifications             │         │
│                     │ • Update statistics             │         │
│                     └─────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Operation Logging                                      │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Generate     │───►│Save Log to  │───►│Display      │          │
│  │Operation    │    │Current Dir  │    │Summary      │          │
│  │Report       │    │(Not Vault)  │    │Statistics   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Safe Operation Design

```
┌─────────────┐    Dry-run?   ┌─────────────┐
│Operation    │─────Yes──────►│Preview Only │
│Request      │               │Show Changes │
└─────────────┘               └─────────────┘
      │                             │
      │No                           │
      ▼                             │
┌─────────────┐                     │
│Process File │                     │
│Calculate    │─────────────────────┤
│Modifications│                     │
└─────────────┘                     ▼
      │                       ┌─────────────┐
      │                       │Display      │
      ▼                       │Results &    │
┌─────────────┐               │Statistics   │
│Write Changes│               └─────────────┘
│Log Operation│
└─────────────┘
```

## Extension Points

The architecture supports extension through:

1. **Additional Operations**: Extend `TagOperationEngine` for new tag operations
2. **Additional Parsers**: New tag sources can be added by implementing the parser interface
3. **Output Formats**: New formatters can be added to `output_formatter.py`
4. **Analysis Modules**: The `tagex/analysis/` directory provides five analysis types:
   - Pair analysis (co-occurrence patterns)
   - Merge analysis (semantic similarity via TF-IDF embeddings)
   - Quality analysis (overbroad tag detection and specificity scoring)
   - Synonym analysis (context-based synonym detection via Jaccard similarity)
   - Plural analysis (singular/plural variant detection)
5. **Configuration Systems**: `tagex/config/` for user-defined mappings (.tagex-synonyms.yaml)
6. **File Filters**: Pattern-based exclusion system can be extended
7. **Statistics**: The statistics tracking system can be enhanced for additional metrics
8. **Tag Validation**: Validation rules can be customized in `tagex/utils/tag_normalizer.py`
9. **Plural Normalization**: Irregular plural dictionary in `tagex/utils/plural_normalizer.py`
10. **Console Integration**: Script entry points defined in `pyproject.toml`
11. **Operation Logging**: Structured logging system supports custom reporting
