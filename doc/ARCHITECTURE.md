# TagEx Architecture

```
    ╔══════════════════════════════════════════════════════════════╗
    ║                    TAGEX PROCESSING PIPELINE                 ║
    ║                                                              ║
    ║    Markdown Files → Tag Extraction → Analysis → Output       ║
    ╚══════════════════════════════════════════════════════════════╝
```

## Core Components

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   main.py       │      │  extractor/     │      │    parsers/     │
│                 │      │                 │      │                 │
│ ┌─────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │ Click CLI   │ │─────►│ │TagExtractor │ │─────►│ │frontmatter  │ │
│ │ Interface   │ │      │ │   Engine    │ │      │ │   parser    │ │
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
│     utils/       │      │output_formatter │      │ tag-analysis/   │
│                  │      │                 │      │                 │
│ ┌──────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │file_discovery│ │      │ │ JSON Format │ │      │ │co-occurrence│ │
│ │              │ │      │ │             │ │      │ │  analyzer   │ │
│ └──────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │
│                  │      │                 │      │                 │
│ ┌──────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │
│ │tag_normalizer│ │      │ │ CSV & Text  │ │      │ │ migration   │ │
│ │& validation  │ │      │ │  Formats    │ │      │ │  analysis   │ │
│ └──────────────┘ │      │ └─────────────┘ │      │ └─────────────┘ │
└──────────────────┘      └─────────────────┘      └─────────────────┘
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
│ • CLI interface using Click framework       │
│ • Console script entry point (tagex)        │
│ • Tag filtering by default (--no-filter)    │
│ • Orchestrates extraction workflow          │
│ • Handles logging configuration             │
│ • Error reporting and exit codes            │
│ • Output file management                    │
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

# Run with system-wide command
tagex /path/to/vault

# Extract with filtering (default)
tagex /vault/path -o tags.json

# Extract raw tags (no filtering)
tagex /vault/path --no-filter -o raw_tags.json
```

## Extension Points

The architecture supports extension through:

1. **Additional Parsers**: New tag sources can be added by implementing the parser interface
2. **Output Formats**: New formatters can be added to `output_formatter.py`  
3. **Analysis Modules**: The `tag-analysis/` directory demonstrates advanced processing
4. **File Filters**: Pattern-based exclusion system can be extended
5. **Statistics**: The statistics tracking system can be enhanced for additional metrics
6. **Tag Validation**: Validation rules can be customized in `utils/tag_normalizer.py`
7. **Console Integration**: Script entry points defined in `pyproject.toml`
