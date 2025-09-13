# Obsidian Tag Management Tool - Analytics Modules Documentation

```
    ╔═══════════════════════════════════════════════════════════════╗
    ║                      TAG ANALYTICS ENGINE                     ║
    ║                                                               ║
    ║    Process raw tags through                                   ║
    ║    tag pair analysis and clustering detection.                ║
    ╚═══════════════════════════════════════════════════════════════╝
```

## Overview

The `tag-analysis/` directory contains analytical tools that perform tag pair analysis and graph-based clustering on tag data extracted from markdown files.

```
tag-analysis/
├── pair_analyzer.py            ← Core analysis engine with filtering (CLI)
├── merge_analyzer.py           ← Tag merge suggestion engine (CLI)
└── README.md                   ← Analysis experiment results and findings
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

1. **Tag Pair Analysis** - Find which tags frequently appear together:
   ```bash
   # Basic analysis with filtering (default behavior)
   uv run tag-analysis/pair_analyzer.py tags.json
   
   # Custom minimum threshold with filtering
   uv run tag-analysis/pair_analyzer.py tags.json --min-pairs 5
   
   # Analysis without noise filtering
   uv run tag-analysis/pair_analyzer.py tags.json --no-filter
   ```

2. **Tag Merge Analysis** - Get suggestions for tag consolidation:
   ```bash
   # Basic merge analysis with embedding-based semantic detection
   uv run tag-analysis/merge_analyzer.py tags.json
   
   # Custom minimum usage threshold
   uv run tag-analysis/merge_analyzer.py tags.json --min-usage 5
   
   # Analysis without noise filtering
   uv run tag-analysis/merge_analyzer.py tags.json --no-filter
   
   # Force pattern-based fallback (test without sklearn)
   uv run tag-analysis/merge_analyzer.py tags.json --no-sklearn
   ```

### Expected Output

The analysis tool generates reports showing:

- Tag frequency statistics
- Tag relationship patterns  
- Natural clustering information
- Hub tag identification

The analysis helps identify:

- Singleton tags (used only once)
- Hub tags (appearing in multiple combinations)
- Related tag clusters
- Natural groupings and relationships

---

## Pair Analyzer (`pair_analyzer.py`)

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

**`calculate_pairs()`**
```python
for file_path, tags in file_to_tags.items():
    for tag1, tag2 in combinations(sorted(tags), 2):
        pairs[(tag1, tag2)] += 1
```
- Uses `itertools.combinations()` for all unique pairs
- Filters by minimum threshold (default: 2 occurrences)

**`find_tag_clusters()`**
- Builds adjacency graph from tag pair data
- Uses DFS traversal to find connected components
- Only includes "strong" connections (≥3 occurrences)

### Sample Output:
```bash
# Run with command line interface (with filtering)
$ uv run tag-analysis/pair_analyzer.py tags.json --min-pairs 3

# Run without filtering (show all tag pairs)
$ uv run tag-analysis/pair_analyzer.py tags.json --no-filter --min-pairs 3

Top 20 Tag Pairs:
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

The `pair_analyzer.py` includes integrated tag filtering.

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
uv run tag-analysis/pair_analyzer.py tags.json

# Raw analysis (all tags)
uv run tag-analysis/pair_analyzer.py tags.json --no-filter

# Filtered with custom threshold
uv run tag-analysis/pair_analyzer.py tags.json --min-pairs 5
```

---

## Key Insights from Co-occurrence Analysis

### What the Analysis Reveals:

1. **Hub Detection**: Identifies tags that appear frequently with others, indicating organizational centers
2. **Tag Clustering**: Finds natural groupings using graph traversal algorithms  
3. **Noise Filtering**: Separates meaningful content tags from technical artifacts
4. **Relationship Mapping**: Shows which tags co-occur, revealing content connections

### Typical Statistical Patterns:

- **Singleton tags** - Often 30-40% of tags are used only once (indicates rich, specific tagging)
- **Natural clusters emerge** - Related tags group together without forced hierarchy  
- **Hub tags provide structure** - A few highly-connected tags organize the system
- **Long-tail distribution** - Most tags used infrequently (normal in personal systems)

### Practical Applications:

- **Content Discovery**: Find related notes through tag relationships  
- **Tagging Consistency**: Identify similar tags that could be standardized
- **System Understanding**: Visualize how your knowledge is organized
- **Quality Assessment**: Spot potential tagging issues or opportunities

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

---

## Merge Analyzer (`merge_analyzer.py`)

**Function:** Analyzes tag usage patterns to suggest consolidation opportunities using multiple detection methods including embedding-based semantic similarity.

### Detection Methods

**1. SIMILAR NAMES** - String similarity analysis (85%+ threshold)
- Catches likely typos and minor spelling variations
- Examples: `writing/writng`, `tech/technology`

**2. SEMANTIC DUPLICATES** - TF-IDF embedding analysis
- Uses character-level n-gram embeddings (2-4 character patterns)
- Calculates cosine similarity between tag vectors
- Identifies conceptually related tags beyond string matching
- Examples: `music/audio`, `family/relatives`, `work/employment`
- Falls back to dynamic morphological patterns if sklearn unavailable
- `--no-sklearn` flag available to test fallback behavior

**3. HIGH FILE OVERLAP** - Co-occurrence analysis
- Finds tags appearing together in 80%+ of files
- Suggests functional equivalence or subsumption
- Shows overlap ratios and shared file counts

**4. VARIANT PATTERNS** - Morphological analysis
- Detects plural/singular forms: `parent/parents`
- Identifies verb variations: `writing/writers`
- Catches common suffix patterns

### Embedding Algorithm

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Tag List        │───►│ TF-IDF Vectorizer│───►│ Similarity      │
│ [work, writing, │    │ char n-grams     │    │ Matrix          │
│  writers, music]│    │ (2-4 chars)      │    │ (cosine)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Merge           │◄───│ Group Similar    │◄───│ Threshold       │
│ Suggestions     │    │ Tags (0.6+)      │    │ Filter          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Sample Output

```bash
$ uv run tag-analysis/merge_analyzer.py tags.json

=== TAG MERGE SUGGESTIONS ===

SEMANTIC DUPLICATES:
  Keep: writing
  Merge: writers, writering
  Command: tagex merge /path/to/vault writers writering --into writing
  Total usage: 45
  Similarity scores: 0.72, 0.68

HIGH FILE OVERLAP:
  neurotype + neurodivergence
  Overlap: 85.2% (23/27 files)
  Suggest keeping: neurotype
  Command: tagex rename /path/to/vault neurodivergence neurotype

VARIANT PATTERNS:
  Keep: parenting
  Merge: parents
  Command: tagex merge /path/to/vault parents --into parenting
  Total usage: 28
```

### Character N-gram Approach

The embedding method uses character-level n-grams instead of word-level features because:

- **Short text optimization**: Tags are typically 1-3 words, character patterns more informative
- **Morphological sensitivity**: Captures shared roots and affixes (`neuro-`, `-ing`, `-ed`)
- **Typo robustness**: Similar character patterns even with spelling variations
- **Language independence**: Works across different languages and naming conventions

### Usage Examples

```bash
# Standard analysis with embeddings
uv run tag-analysis/merge_analyzer.py tags.json

# Higher usage threshold (ignore rare tags)
uv run tag-analysis/merge_analyzer.py tags.json --min-usage 10

# Include all tags (no noise filtering)
uv run tag-analysis/merge_analyzer.py tags.json --no-filter

# Test pattern-based fallback instead of embeddings
uv run tag-analysis/merge_analyzer.py tags.json --no-sklearn

# Manual execution of suggestions
tagex merge /path/to/vault writers writering --into writing --dry-run
```

### Dependencies and Fallback Strategy

**Required Dependencies:** The merge analyzer now includes scikit-learn as a dependency for TF-IDF embedding analysis:

```bash
# scikit-learn is included in pyproject.toml dependencies
uv sync  # installs scikit-learn>=1.7.2
```

**Fallback Behavior:** If scikit-learn is unavailable or disabled with `--no-sklearn`, the system uses **dynamic morphological analysis** with generic English patterns:

```python
def find_semantic_duplicates_pattern(tag_stats):
    """Dynamic morphological pattern detection."""
    stem_groups = defaultdict(list)
    
    for tag in tag_stats.keys():
        stems = set()
        tag_lower = tag.lower()
        
        # Remove common suffixes to find stems
        if tag_lower.endswith('s'):      stems.add(tag_lower[:-1])    # plural
        if tag_lower.endswith('ing'):    stems.add(tag_lower[:-3])    # present participle
        if tag_lower.endswith('er'):     stems.add(tag_lower[:-2])    # agent noun
        if tag_lower.endswith('ed'):     stems.add(tag_lower[:-2])    # past tense
        if tag_lower.endswith('tion'):   stems.add(tag_lower[:-4])    # abstract noun
        if tag_lower.endswith('ly'):     stems.add(tag_lower[:-2])    # adverb
        
        # Group tags by shared stems
        for stem in stems:
            stem_groups[stem].append(tag)
```

**Examples of morphological pattern detection:**
- `write, writing, writer, writers` → stem: `writ`
- `parent, parents, parenting` → stem: `parent`
- `quick, quickly` → stem: `quick`
- `organize, organization` → stem: `organiz`

This **dynamic approach** works with any English tag vocabulary without requiring vault-specific configuration, ensuring the analyzer remains universally applicable.
