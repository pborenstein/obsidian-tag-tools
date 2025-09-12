# TagEx Architecture

```
    ╔══════════════════════════════════════════════════════════════╗
    ║                    TAGEX PROCESSING PIPELINE                 ║
    ║                                                              ║
    ║    Markdown Files → Tag Extraction → Analysis → Operations   ║
    ║                         ↓              ↓            ↓       ║
    ║                    Tag Output    Relationships   Tag Modify  ║
    ╚══════════════════════════════════════════════════════════════╝
```

## Core Components

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   main.py       │      │  extractor/     │      │    parsers/     │
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
│  operations/     │      │output_formatter │      │ tag-analysis/   │
│                  │      │                 │      │                 │
│ ┌──────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │TagOperation  │ │      │ │ JSON Format │ │      │ │co-occurrence│ │
│ │   Engine     │ │      │ │             │ │      │ │  analyzer   │ │
│ └──────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │
│                  │      │                 │      │                 │
│ ┌──────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │Rename/Merge/ │ │      │ │ CSV & Text  │ │      │ │ migration   │ │
│ │Apply Ops     │ │      │ │  Formats    │ │      │ │  analysis   │ │
│ └──────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │
└──────────────────┘      └─────────────────┘      └─────────────────┘
        │
        ▼
┌──────────────────┐
│     utils/       │
│                  │
│ ┌──────────────┐ │
│ │file_discovery│ │
│ │              │ │
│ └──────────────┘ │
│                  │
│ ┌──────────────┐ │
│ │tag_normalizer│ │
│ │& validation  │ │
│ └──────────────┘ │
└──────────────────┘
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

### Main Pipeline (`main.py`)
```
┌─────────────────────────────────────────────┐
│              MAIN CONTROLLER                │
├─────────────────────────────────────────────┤
│ • Multi-command CLI using Click groups      │
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
│ tagex extract   → TagExtractor class        │
│ tagex rename    → RenameOperation class     │
│ tagex merge     → MergeOperation class      │
│ tagex apply     → ApplyOperation class      │
└─────────────────────────────────────────────┘
```

### Tag Extraction Engine (`extractor/core.py`)
```
┌─────────────────────────────────────────────┐
│             TAGEXTRACTOR CLASS              │
├─────────────────────────────────────────────┤
│ • Processes vault files sequentially        │
│ • Aggregates tag data from all sources      │
│ • Maintains processing statistics           │
│ • Coordinates parser modules                │
│ • Handles file processing errors            │
└─────────────────────────────────────────────┘
```

### Parser Modules (`parsers/`)
```
┌─────────────────────┐    ┌─────────────────────┐
│ frontmatter_parser  │    │   inline_parser     │
├─────────────────────┤    ├─────────────────────┤
│ • YAML header       │    │ • Hashtag scanning  │
│   parsing           │    │ • Content regex     │
│ • tags/tag arrays   │    │   matching          │
│ • Validation        │    │ • Tag validation    │
│ • Error handling    │    │ • Position tracking │
└─────────────────────┘    └─────────────────────┘
```

### Utility Functions (`utils/`)
```
┌─────────────────────┐    ┌─────────────────────┐
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

### Tag Operations Engine (`operations/tag_operations.py`)
```
┌─────────────────────────────────────────────┐
│           TAG OPERATION ENGINE              │
├─────────────────────────────────────────────┤
│ TagOperationEngine (Abstract Base Class)    │
│ ├─ Dry-run capability for safe previews     │
│ ├─ Operation logging with integrity checks  │
│ ├─ File modification tracking               │
│ └─ Error handling and statistics            │
│                                             │
│ RenameOperation                             │
│   └─ Rename single tag across vault        │
│                                             │
│ MergeOperation                              │
│   └─ Consolidate multiple tags into one    │
│                                             │
│ ApplyOperation                              │
│   └─ Apply migration mappings from JSON    │
└─────────────────────────────────────────────┘
```

### Output Formatter (`extractor/output_formatter.py`)
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
    ├─► frontmatter_parser.py ──┐
    │                           │
    └─► inline_parser.py ───────┼─► Aggregation
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

## Tag Validation System

TagEx includes comprehensive tag validation to filter out noise and technical artifacts:

### Validation Rules (`utils/tag_normalizer.py`)

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

```bash
# Install as editable tool
uv tool install --editable .

# Run extraction with system-wide command
tagex extract /path/to/vault

# Extract with filtering (default)
tagex extract /vault/path -o tags.json

# Extract raw tags (no filtering)
tagex extract /vault/path --no-filter -o raw_tags.json

# Tag operations (always with preview first)
tagex rename /vault old-tag new-tag --dry-run
tagex merge /vault tag1 tag2 --into combined-tag --dry-run
tagex apply /vault migration.json --dry-run
```

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
│  STEP 2: File Discovery & Filtering                            │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │Find Markdown│───►│Filter by    │───►│Build Target │          │
│  │Files        │    │Tag Presence │    │File List    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Tag Transformation (Per File)                         │
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
4. **Analysis Modules**: The `tag-analysis/` directory demonstrates advanced processing
5. **File Filters**: Pattern-based exclusion system can be extended
6. **Statistics**: The statistics tracking system can be enhanced for additional metrics
7. **Tag Validation**: Validation rules can be customized in `utils/tag_normalizer.py`
8. **Console Integration**: Script entry points defined in `pyproject.toml`
9. **Operation Logging**: Structured logging system supports custom reporting
