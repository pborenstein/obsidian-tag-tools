# Obsidian Tag Management Tool - Analytics Modules Documentation

## Overview

The `tagex analyze` command provides analytical tools that perform tag pair analysis and merge suggestions on tag data extracted from markdown files.

```
tagex analyze pairs     ← Tag co-occurrence and clustering analysis
tagex analyze merge     ← Tag merge suggestion engine with embeddings

See semantic-analysis.md for technical documentation on semantic similarity.
```

---

## Quick Start Guide

### Prerequisites

Extract tags before running analysis:

| Command | Purpose | Output |
|:--------|:--------|:-------|
| `tagex /vault stats` | Quick vault overview | Console statistics |
| `tagex /vault extract -o tags.json` | Filtered tags for analysis | JSON file |
| `tagex /vault extract --no-filter -o raw_tags.json` | Raw tags with noise | JSON file |
| `tagex --tag-types both /vault extract -o all_tags.json` | Both frontmatter and inline | JSON file |

The analysis scripts expect tag data in JSON format by default.

### Analysis Workflow

| Analysis Type | Command | Purpose |
|:--------------|:--------|:---------|
| **Pair Analysis** | `tagex analyze pairs tags.json` | Find tags that appear together |
| **Merge Analysis** | `tagex analyze merge tags.json` | Get consolidation suggestions |

**Common Options:**
- `--min-pairs N` / `--min-usage N`: Set minimum thresholds
- `--no-filter`: Include technical noise
- `--no-sklearn`: Use pattern-based fallback (merge only)

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

### Tag Type Analysis

| Tag Type | Extract Command | Analysis Focus |
|:---------|:----------------|:---------------|
| **Frontmatter** | `tagex /vault extract -o fm_tags.json` | Formal categorization |
| **Inline** | `tagex --tag-types inline /vault extract -o inline_tags.json` | Content-driven tagging |
| **Both** | `tagex --tag-types both /vault extract -o all_tags.json` | Complete pattern analysis |

Run pair or merge analysis on any extracted tag file to compare patterns across tag types.

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

### Health Assessment Criteria

| Metric | Excellent | Good | Moderate | Low |
|:-------|:----------|:-----|:---------|:----|
| **Tag Coverage** | ≥80% files tagged | ≥60% files tagged | ≥40% files tagged | <40% files tagged |
| **Singleton Ratio** | <30% singletons | 30-50% singletons | 50-70% singletons | ≥70% singletons |
| **Diversity Score** | ≥80% of maximum | ≥60% of maximum | ≥40% of maximum | <40% of maximum |

**Assessment Indicators:**
- `+ Excellent/Good`: Healthy patterns
- `* Moderate`: Consider improvements
- `- Low`: Action recommended

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

| Command | Description |
|:--------|:------------|
| `tagex /vault stats` | Basic vault overview |
| `tagex /vault stats --top 10 --format json` | Top 10 tags in JSON format |
| `tagex /vault stats --no-filter` | Include technical noise |
| `tagex /vault stats --top 25` | Custom top tag count |

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

| Issue | Threshold | Recommended Actions |
|:------|:----------|:--------------------|
| **High Singleton Ratio** | >50% | Run merge analyzer, standardize similar tags, review for typos |
| **Low Tag Coverage** | <60% | Implement consistent tagging, review untagged files, batch workflows |
| **Low Diversity Score** | <40% of max | Diversify vocabulary, break down overly broad tags |
| **High Concentration** | >0.7 | Review dominant tags for over-use, develop balanced strategy |

### Analysis Integration Workflow

| Step | Command | When to Use |
|:-----|:--------|:------------|
| 1. Overview | `tagex /vault stats` | Always start here |
| 2. Merge analysis | `tagex analyze merge tags.json` | High singleton ratio |
| 3. Pair analysis | `tagex analyze pairs tags.json` | Low diversity score |
| 4. Apply changes | `tagex /vault merge tag1 tag2 --into new-tag --dry-run` | After analysis review |

---

## Pair Analyzer (`pair_analyzer.py`)

**Function:** Calculates frequency of tag pairs that appear together in the same files. Now includes built-in tag filtering to remove noise.

### Filtering Options

- **Default behavior**: Filters out technical noise using `is_valid_tag()` from `tagex/utils/tag_normalizer.py`
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
$ tagex analyze pairs tags.json --min-pairs 3

# Run without filtering (show all tag pairs)
$ tagex analyze pairs tags.json --no-filter --min-pairs 3

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

| Command | Description |
|:--------|:------------|
| `tagex analyze pairs tags.json` | Filtered analysis (recommended) |
| `tagex analyze pairs tags.json --no-filter` | Raw analysis (all tags) |
| `tagex analyze pairs tags.json --min-pairs 5` | Custom threshold |

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

| Method | Threshold | Description | Examples |
|:-------|:----------|:------------|:---------|
| **Similar Names** | 85%+ similarity | String similarity for typos and variations | `writing/writng`, `tech/technology` |
| **Semantic Duplicates** | 0.6+ cosine similarity | TF-IDF embedding analysis for conceptual relationships | `music/audio`, `family/relatives` |
| **High File Overlap** | 80%+ co-occurrence | Tags appearing together in most files | Functional equivalence detection |
| **Variant Patterns** | Morphological rules | Plural/singular and verb form detection | `parent/parents`, `writing/writers` |

**Semantic Analysis**: Uses character-level n-gram embeddings (2-4 chars) with morphological fallback when scikit-learn unavailable (`--no-sklearn` flag).

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
$ tagex analyze merge tags.json

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

See [semantic-analysis.md](semantic-analysis.md) for detailed technical implementation.

### Usage Examples

| Command | Description |
|:--------|:------------|
| `tagex analyze merge tags.json` | Standard embedding analysis |
| `tagex analyze merge tags.json --min-usage 10` | Higher usage threshold |
| `tagex analyze merge tags.json --no-filter` | Include all tags |
| `tagex analyze merge tags.json --no-sklearn` | Pattern-based fallback |
| `tagex /vault merge writers writering --into writing --dry-run` | Execute suggestions |

### Dependencies and Fallback Strategy

**Required Dependencies:** The merge analyzer includes scikit-learn as a dependency for TF-IDF embedding analysis. Dependencies are installed automatically with the tool.

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
