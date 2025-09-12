# Obsidian Tag Management Tool - Analytics Modules Documentation

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                      TAG ANALYTICS ENGINE                     ║
    ║                                                               ║
    ║    Process raw tags through                                   ║
    ║    co-occurrence analysis, clustering, and migration sim.     ║
    ╚═══════════════════════════════════════════════════════════════╝
```

## Overview

The `tag-analysis/` directory contains analytical tools that perform co-occurrence analysis, graph-based clustering, and migration impact simulation on tag data extracted from markdown files.

```
tag-analysis/
├── cooccurrence_analyzer.py    ← Core engine: finds tag relationships with filtering (CLI)
├── migration_analysis.py       ← Impact simulator: what-if scenarios (CLI)
└── tag_migration.py           ← Migration mappings (legacy)
```

---

## Quick Start Guide

### Prerequisites

Before running tag analysis, extract tags from your vault:

```bash
# Extract filtered tags to JSON file (recommended for analysis)
tagex extract /path/to/vault -o tags.json

# Or extract raw tags if needed for analysis
tagex extract /path/to/vault --no-filter -o raw_tags.json

# Using uv run (alternative)
uv run main.py extract /path/to/vault -o tags.json
```

The analysis scripts expect tag data in JSON format by default.

### Analysis Workflow

1. **Co-occurrence Analysis** - Find which tags frequently appear together:
   ```bash
   # Basic analysis with filtering (default behavior)
   uv run tag-analysis/cooccurrence_analyzer.py tags.json
   
   # Custom minimum threshold with filtering
   uv run tag-analysis/cooccurrence_analyzer.py tags.json --min-cooccurrence 5
   
   # Analysis without noise filtering
   uv run tag-analysis/cooccurrence_analyzer.py tags.json --no-filter
   ```

3. **Migration Analysis** - Assess impact of proposed tag changes:
   ```bash
   uv run tag-analysis/migration_analysis.py tags.json
   ```

### Expected Output

Each analysis tool generates reports showing:

- Tag frequency statistics
- Tag relationship patterns  
- Impact assessments for tag changes
- Recommendations for tag organization

The analysis helps identify:

- Singleton tags (used only once)
- Hub tags (appearing in multiple combinations)
- Related tag clusters
- Potential tag consolidation opportunities

---

## Co-occurrence Analyzer (`cooccurrence_analyzer.py`)

**Function:** Calculates frequency of tag pairs that appear together in the same files. Now includes built-in tag filtering to remove noise.

### Filtering Options

- **Default behavior**: Filters out technical noise using `is_valid_tag()` from `utils/tag_normalizer.py`
- **--no-filter flag**: Analyzes all tags including technical artifacts
- **Integrated filtering**: Single script handles both filtered and raw analysis

```
    File 1: [work, notes, ideas]         ┌─────────────────┐
    File 2: [work, notes, tasks]         │     work (150)  │◄─── Hub Tag
    File 3: [work, ideas, draft]         └─────────┬───────┘      
             │                                     │              
             │  Co-occurrence Matrix:              │              
             │  ┌─────────────────────────────┐    │              
             └─►│ work + notes:     45        │◄───┘              
                │ work + ideas:     25        │                        
                │ work + tasks:     20        │                        
                │ notes + ideas:    15        │                        
                └─────────────────────────────┘                        
```

### Algorithm Flow:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Load JSON      │───►│ Build File→Tags  │───►│ Generate Pairs  │
│  Tag Data       │    │     Mapping      │    │   (All combos)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Find Clusters   │◄───│  Calculate Hub   │◄───│   Count Co-     │
│  (Graph DFS)    │    │   Centrality     │    │  occurrences    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Functions:

**`build_file_to_tags_map(filter_noise=False)`**
- Creates reverse index: `file_path → {tag1, tag2, tag3...}`
- Optionally filters invalid tags using `is_valid_tag()`
- Allows efficient pair generation per file

**`calculate_cooccurrence()`**
```python
for file_path, tags in file_to_tags.items():
    for tag1, tag2 in combinations(sorted(tags), 2):
        cooccurrence[(tag1, tag2)] += 1
```
- Uses `itertools.combinations()` for all unique pairs
- Filters by minimum threshold (default: 2 co-occurrences)

**`find_tag_clusters()`**
- Builds adjacency graph from co-occurrence data
- Uses DFS traversal to find connected components
- Only includes "strong" connections (≥3 co-occurrences)

### Sample Output:
```bash
# Run with command line interface (with filtering)
$ uv run tag-analysis/cooccurrence_analyzer.py tags.json --min-cooccurrence 3

# Run without filtering (show all tag pairs)
$ uv run tag-analysis/cooccurrence_analyzer.py tags.json --no-filter --min-cooccurrence 3

Top 20 Co-occurring Tag Pairs:
 45  notes + work
 25  ideas + work  
 20  tasks + work
 15  notes + ideas
 12  reference + articles

Found 4 natural tag clusters:
Cluster 1 (8 tags):
  - work
  - notes
  - ideas
  - tasks
  - draft

Most Connected Tags (hub tags):
150  work
120  notes  
85   ideas
75   reference
60   articles
```

---

## Tag Filtering Integration

The `cooccurrence_analyzer.py` includes integrated tag filtering.

### Built-in Filtering

```
    Raw Tag Stream:                     Filtered Stream:
    ┌─────────────────┐                ┌─────────────────┐
    │ work            │──────────────► │ work            │
    │ notes           │──────────────► │ notes           │
    │ 123             │────────X       │ ideas           │
    │ dispatcher_util │────────X       │ reference       │
    │ ideas           │──────────────► │ tasks           │
    │ dom-element     │────────X       │ articles        │
    │ reference       │──────────────► └─────────────────┘
    │ tasks           │──────────────►      │
    │ fs_operation    │────────X            │
    │ articles        │─────────────────────┘
    └─────────────────┘
         Comprehensive Filter Applied
```

### Enhanced Filtering Rules

The analyzer now uses the `is_valid_tag()` function with:

- **Pure numbers**: Filtered out (123, 456789)
- **Technical patterns**: Hex strings, UUIDs, version numbers
- **HTML/Unicode noise**: Entities, zero-width characters
- **Short tags**: 1-2 character tags filtered
- **Invalid characters**: Only alphanumeric, underscore, dash, slash allowed
- **Nested tag validation**: Proper slash-separated structure required

### Usage Examples

```bash
# Filtered analysis (recommended)
uv run tag-analysis/cooccurrence_analyzer.py tags.json

# Raw analysis (all tags)
uv run tag-analysis/cooccurrence_analyzer.py tags.json --no-filter

# Filtered with custom threshold
uv run tag-analysis/cooccurrence_analyzer.py tags.json --min-cooccurrence 5
```

---

## Migration Analysis (`migration_analysis.py`)

**Function:** Calculates statistics for proposed tag consolidation mappings.

```
    BEFORE Migration:              AFTER Migration:
    ╭─────────────────╮           ╭─────────────────╮
    │ 4,620 tags      │    ═══►   │ 4,490 tags      │  (-2.8%)
    │ 11,416 usages   │           │ 11,280 usages   │  (-1.2%)
    ╰─────────────────╯           ╰─────────────────╯
           │                             │
           │                             │
    ┌─────────────────┐           ┌─────────────────┐
    │ work            │           │ category/       │
    │ notes           │    ═══►   │   work          │
    │ personal-note   │           │   notes         │  
    │ diary-entry     │           │   writing       │
    └─────────────────┘           └─────────────────┘
         Flat Tags                 Hierarchical Tags
```

### Analysis Pipeline:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Load Original│───►│Apply Mappings│───►│Calculate     │
│  Tag Data    │    │& Deletions   │    │ Before/After │
└──────────────┘    └──────────────┘    └──────────────┘
                             │                   │
                             ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Show Hierarchy│◄───│Find Big      │◄───│Identify      │
│  Structure   │    │Consolidations│    │ Issues       │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Risk Assessment Matrix:

```
                   RISK LEVEL
                   ┌────────────────────────────┐
    High Impact    │     DANGER ZONE            │  
    (>100 files)   │                            │  
                   │  1,632 files affected      │  
                   │  Major disruption risk     │  
                   ├────────────────────────────┤
    Medium Impact  │    CAUTION ZONE            │  
    (10-100 files) │                            │  
                   │  Moderate risk/reward      │  
                   ├────────────────────────────┤
    Low Impact     │      SAFE ZONE             │  
    (<10 files)    │                            │  
                   │  Low risk operations       │  
                   └────────────────────────────┘
                    Low         High
                        BENEFIT LEVEL
```

### Consolidation Analysis:

```
BIGGEST CONSOLIDATIONS:

category/reference → 450 total usages
  ← reference (375)
  ← articles (45) 
  ← research (30)

category/work → 340 total usages  
  ← work (150)
  ← notes (120)
  ← tasks (70)

tech/development → 280 total usages
  ← code (120)
  ← dev (85)
  ← project (75)
```

---

## Key Insights from Analysis

### Success Stories:

1. **Hub Detection Works**: Correctly identified `work` and `reference` as organizational centers
2. **Tag Clustering**: Found groupings (personal, reference, tech) using graph traversal algorithms  
3. **Noise Filtering**: Successfully separated content tags from technical artifacts
4. **Risk Assessment**: Correctly predicted high-risk/low-benefit ratio for migration

### Why Migration Was Rejected:

```
╔═════════════════════════════════════════════════════════════╗
║                     DECISION MATRIX                         ║
║                                                             ║
║   Benefit: 2.8% tag reduction (130 tags)        [LOW]       ║
║   Risk:    1,632 files modified                 [HIGH]      ║  
║   Effort:  Frontmatter parsing, backup/restore  [HIGH]      ║
║   Value:   Mostly cosmetic hierarchy changes    [LOW]       ║
║                                                             ║
║   CONCLUSION: Risk >> Benefit                               ║
║   RECOMMENDATION: Preserve existing system                  ║
╚═════════════════════════════════════════════════════════════╝
```

### Statistical Findings:

- **36% singleton tags** - indicates rich, specific tagging (good for personal knowledge)
- **Natural clusters emerge** - system self-organizes without forced hierarchy  
- **Hub tags provide structure** - centralized organization around `work`, `reference`
- **Long-tail distribution normal** - 95% of tags used ≤5 times (expected in personal systems)

---

## Completed Improvements

### Tag Filtering Integration

- **Consolidated analysis**: Single script handles both filtered and raw analysis
- **Command-line control**: `--no-filter` flag for complete analysis
- **Improved accuracy**: Better noise filtering reduces false relationships
- **Simplified workflow**: Single script with optional filtering control

### Enhanced Validation

- **Comprehensive rules**: Filters technical artifacts, HTML entities, short tags
- **Pattern matching**: Detects and removes hex strings, UUIDs, version numbers
- **Character validation**: Ensures tags use valid character sets
- **Nested tag support**: Proper validation for hierarchical tags

## Future Applications

The analytical foundation supports additional functionality:

```
    Current Analysis              Future Applications
    ┌─────────────────┐          ┌─────────────────┐
    │ Filtered Co-    │─────────►│ Smart Tag       │
    │ occurrence      │          │ Suggestions     │
    └─────────────────┘          └─────────────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Clean Cluster   │─────────►│ Content         │
    │ Detection       │          │ Discovery       │  
    └─────────────────┘          └─────────────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Validated Hub   │─────────►│ Knowledge Graph │
    │ Identification  │          │ Visualization   │
    └─────────────────┘          └─────────────────┘
```

The filtering shows that tag validation supports relationship analysis in personal knowledge systems.
