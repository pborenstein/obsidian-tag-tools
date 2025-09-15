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
├── merge_analyzer.py           ← Tag merge suggestion engine with embeddings (CLI)
└── SEMANTIC_ANALYSIS.md        ← Technical documentation on semantic similarity
```

---

## Quick Start Guide

### Prerequisites

Before running tag analysis, extract tags from your vault or view comprehensive statistics:

```bash
# View comprehensive vault statistics (quick overview)
tagex /path/to/vault stats

# Extract filtered tags to JSON file (recommended for detailed analysis)
tagex /path/to/vault extract -o tags.json

# Or extract raw tags if needed for analysis
tagex /path/to/vault extract --no-filter -o raw_tags.json

# Extract specific tag types for targeted analysis
tagex --tag-types frontmatter /path/to/vault extract -o frontmatter_tags.json
tagex --tag-types inline /path/to/vault extract -o inline_tags.json

# Using uv run (alternative)
uv run main.py /path/to/vault extract -o tags.json
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

### Analyzing Different Tag Types

The analytics tools work with any extracted tag data, enabling specialized analysis:

```bash
# Compare frontmatter vs inline tag patterns
tagex --tag-types frontmatter /vault extract -o fm_tags.json
tagex --tag-types inline /vault extract -o inline_tags.json

uv run tag-analysis/pair_analyzer.py fm_tags.json
uv run tag-analysis/pair_analyzer.py inline_tags.json

# Merge analysis for specific tag types
uv run tag-analysis/merge_analyzer.py fm_tags.json
uv run tag-analysis/merge_analyzer.py inline_tags.json
```

This enables insights into:
- **Frontmatter patterns**: Formal categorization and metadata
- **Inline patterns**: Contextual and content-driven tagging
- **Usage differences**: How different tag types are used organizationally

---

## Vault Statistics (`tagex stats`)

**Function:** Provides comprehensive analytical overview of tag usage patterns, distribution, and vault health metrics.

### Core Metrics

The stats command calculates and displays:

**Basic Metrics:**
- Total unique tags and total tag uses
- Tag density (average tags per file)
- File coverage (percentage of files with tags)

**Distribution Analysis:**
- **Singletons**: Tags used exactly once
- **Doubletons**: Tags used exactly twice
- **Tripletons**: Tags used exactly three times
- **Frequent tags**: Tags used 4+ times

**Health Metrics:**
- **Diversity score**: Shannon entropy measuring tag distribution balance
- **Concentration score**: Gini-like coefficient showing usage concentration
- **Health assessment**: Automated recommendations based on patterns

### Understanding the Health Assessment

The stats command provides automated health assessment using these indicators:

**Tag Coverage Assessment:**
- `+ Excellent` (≥80%): Most files are tagged
- `+ Good` (≥60%): Majority of files tagged
- `* Moderate` (≥40%): Consider tagging more files
- `- Low` (<40%): Many files lack tags

**Singleton Analysis:**
- `+ Good` (<30%): Low singleton ratio, good tag reuse
- `* Moderate` (30-50%): Some cleanup opportunities exist
- `- High` (≥50%): Many tags used only once, consider consolidation

**Diversity Assessment:**
- `+ High` (≥80% of maximum): Well-distributed usage across tags
- `+ Good` (≥60% of maximum): Reasonably balanced distribution
- `* Moderate` (≥40% of maximum): Some tags dominate others
- `- Low` (<40% of maximum): Heavily concentrated on few tags

### Interpreting Diversity Scores

**Shannon Entropy (Diversity Score):**
- **Range**: 0 to log₂(number_of_tags)
- **Higher values**: More even distribution across all tags
- **Lower values**: Usage concentrated in fewer tags
- **Example**: A vault with 100 tags has maximum diversity of ~6.6

**Concentration Score:**
- **Range**: 0 to 1
- **Lower values**: More balanced tag usage
- **Higher values**: Usage concentrated in few dominant tags
- **0.0**: Perfect balance (all tags used equally)
- **1.0**: Maximum concentration (one tag dominates completely)

### Usage Examples

```bash
# Basic stats overview
tagex /path/to/vault stats

# Focus on top 10 tags with JSON output
tagex /path/to/vault stats --top 10 --format json

# Stats for frontmatter tags only
tagex --tag-types frontmatter /path/to/vault stats

# Include unfiltered tags (show technical noise)
tagex /path/to/vault stats --no-filter

# Stats with custom top tag count
tagex /path/to/vault stats --top 25
```

### Sample Output Interpretation

```
Vault Tag Statistics
==================================================

Vault Overview:
   Path: /Users/example/vault
   Tag types: both
   Files processed: 2,081
   Processing errors: 0

Tag Metrics:
   Total unique tags: 831
   Total tag uses: 2,864
   Average tags per file: 1.38

Tag Coverage:
   Files with tags: 1,262 (60.6%)
   Files without tags: 819

Tag Distribution:
   Singletons (used once): 563 (67.7%)
   Doubletons (used twice): 106 (12.8%)
   Tripletons (used 3x): 52 (6.3%)
   Frequent tags (4+ uses): 110 (13.2%)

Vault Health:
   Diversity score: 7.55 (higher = more diverse)
   Concentration score: 0.65 (lower = more balanced)

Health Assessment:
   + Good tag coverage - majority of files tagged
   - High singleton ratio - many tags used only once (consider consolidation)
   + Good tag diversity - reasonably balanced
```

**Interpretation:**
- **Good coverage**: 60.6% of files have tags (above 60% threshold)
- **High singletons**: 67.7% singleton ratio suggests cleanup opportunities
- **Balanced diversity**: Score of 7.55 out of ~9.7 maximum shows good distribution
- **Recommendations**: Focus on consolidating singleton tags while maintaining current tagging practices

### Actionable Insights

**High Singleton Ratio (>50%):**
- Run merge analyzer to find consolidation opportunities
- Consider standardizing similar tags
- Review tags used only once for typos or alternatives

**Low Tag Coverage (<60%):**
- Implement consistent tagging for new files
- Review untagged files for tagging opportunities
- Consider batch tagging workflows

**Low Diversity Score:**
- Indicates few tags dominate the system
- Consider diversifying tag vocabulary
- Break down overly broad tags into more specific ones

**High Concentration Score (>0.7):**
- Usage heavily skewed toward few tags
- Review dominant tags for over-use
- Develop more balanced tagging strategy

### Integration with Analysis Tools

Stats output helps prioritize analysis workflows:

```bash
# 1. Get overview and identify issues
tagex /vault stats

# 2. If high singleton ratio, run merge analysis
uv run tag-analysis/merge_analyzer.py tags.json

# 3. If low diversity, run pair analysis for clustering insights
uv run tag-analysis/pair_analyzer.py tags.json

# 4. Apply suggested consolidations
tagex /vault merge old-tag1 old-tag2 --into new-tag --dry-run
```

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
             └─►│ Filtered pair analysis      │◄───┘              
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
│ Find Clusters   │◄───│  Calculate Hub   │◄───│   Count Pairs   │
│  (Graph DFS)    │    │   Centrality     │    │                 │
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

## Key Insights from Pair Analysis

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

**2. SEMANTIC DUPLICATES** - TF-IDF embedding analysis with morphological fallback
- **Primary method**: Character-level n-gram embeddings (2-4 character patterns)
- Calculates cosine similarity between tag vectors for conceptual relationships
- Identifies semantically related tags beyond string matching
- Examples: `music/audio`, `family/relatives`, `work/employment`
- **Fallback method**: Dynamic morphological pattern matching for environments without scikit-learn
- Detects plural/singular, verb forms, and common suffix patterns
- `--no-sklearn` flag available to test fallback behavior

**3. HIGH FILE OVERLAP** - Pair analysis
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
  Command: tagex /path/to/vault merge writers writering --into writing
  Total usage: 45
  Similarity scores: 0.72, 0.68

HIGH FILE OVERLAP:
  neurotype + neurodivergence
  Overlap: 85.2% (23/27 files)
  Suggest keeping: neurotype
  Command: tagex /path/to/vault rename neurodivergence neurotype

VARIANT PATTERNS:
  Keep: parenting
  Merge: parents
  Command: tagex /path/to/vault merge parents --into parenting
  Total usage: 28
```

### Character N-gram Approach

The embedding method uses character-level n-grams instead of word-level features because:

- **Short text optimization**: Tags are typically 1-3 words, character patterns more informative
- **Morphological sensitivity**: Captures shared roots and affixes (`neuro-`, `-ing`, `-ed`)
- **Typo robustness**: Similar character patterns even with spelling variations
- **Language independence**: Works across different languages and naming conventions
- **Semantic detection**: Identifies conceptual relationships that morphological patterns cannot capture

See [tag-analysis/SEMANTIC_ANALYSIS.md](../tag-analysis/SEMANTIC_ANALYSIS.md) for detailed technical implementation.

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
tagex /path/to/vault merge writers writering --into writing --dry-run
```

### Dependencies and Fallback Strategy

**Required Dependencies:** The merge analyzer includes scikit-learn as a dependency for TF-IDF embedding analysis:

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

This **dynamic approach** works with any English tag vocabulary without requiring vault-specific configuration, ensuring the analyzer remains universally applicable while providing a robust fallback when embedding-based analysis is unavailable.
ailable.
