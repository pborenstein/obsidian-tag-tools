# Obsidian Tag Management Tool - Analytics Modules Documentation

## Overview

The `tagex analyze` command provides comprehensive analytical tools for understanding tag usage patterns, identifying consolidation opportunities, and improving tag quality across your Obsidian vault.

```
# Unified recommendations workflow (RECOMMENDED)
tagex analyze recommendations /vault --export ops.yaml  ← Consolidate all analyzer suggestions
tagex apply ops.yaml                                    ← Preview changes (safe default)
tagex apply ops.yaml --execute                          ← Apply changes (explicit flag required)

# Individual analyzers
tagex analyze pairs      ← Tag co-occurrence and clustering analysis
tagex analyze merge      ← Tag merge suggestion engine with embeddings
tagex analyze quality    ← Overbroad tag detection and specificity scoring
tagex analyze synonyms   ← Semantic synonym detection using sentence-transformers
tagex analyze plurals    ← Singular/plural variant detection
tagex analyze suggest    ← Content-based tag suggestions for untagged/lightly-tagged notes

# Singleton reduction (via recommendations)
tagex analyze recommendations /vault --analyzers singletons --export ops.yaml

# Configuration and health commands
tagex init /vault        ← Initialize .tagex/ configuration directory
tagex validate /vault    ← Validate configuration files
tagex health /vault      ← Comprehensive vault health report

See SEMANTIC_ANALYSIS.md for technical documentation on semantic similarity.
```

---

## Which Analysis Should I Use?

Use this decision tree to find the right analysis command for your needs:

```
┌─────────────────────────────────────────────────────────────────┐
│  What do you want to understand about your tags?                │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Overall      │    │ Find         │    │ Improve      │
│ Health?      │    │ Duplicates?  │    │ Quality?     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   │                   │
  tagex stats /vault        │                   │
                            │                   │
        ┌───────────────────┼───────────────────┘
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ What kind    │    │ Too generic? │
│ of duplicates│    │ Too broad?   │
└──────────────┘    └──────────────┘
        │                   │
        │                   ▼
        │           tagex analyze
        │           quality tags.json
        │
        ├─────────┬─────────┬─────────┬─────────┐
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
    ┌────┐   ┌────┐   ┌────┐   ┌────┐   ┌────┐
    │Sing│   │Same│   │Spell│  │Morph│  │Rela│
    │/Pl │   │Mean│   │Varia│  │Vari │  │tion│
    │    │   │Diff │   │tions│  │ants │  │ship│
    │    │   │Name │   │     │  │     │  │    │
    └────┘   └────┘   └────┘  └────┘  └────┘
      │        │        │       │        │
      ▼        ▼        │       │        ▼
   analyze  analyze     │       │     analyze
   plurals  synonyms    └───┬───┘     pairs
                            ▼
                         analyze
                          merge


Legend:
  Sing/Pl    = Singular/plural (book/books, child/children)
  Same Mean  = Same meaning (python/py, music/audio)
  Spell Var  = Spelling variations (writng/writing)
  Morph Var  = Morphological variants (write/writing/writer)
  Relation   = Which tags appear together?
```

### Quick Reference

**I want to...**

| Goal | Command |
|:-----|:--------|
| **Get unified recommendations and apply them** | **`tagex analyze recommendations /vault --export ops.yaml`** |
| Get overall vault health metrics | `tagex stats /vault` |
| Get comprehensive health report with all analyses | `tagex health /vault` |
| Initialize tagex configuration | `tagex init /vault` |
| Validate configuration files | `tagex validate /vault` |
| Find singular/plural splits (book/books) | `tagex analyze plurals /vault` |
| Find semantic synonyms (film/movies, tech/technology) | `tagex analyze synonyms /vault` |
| Find related tags (co-occurrence patterns) | `tagex analyze synonyms /vault --show-related` |
| Find spelling/morphological variants (writing/writers) | `tagex analyze merge /vault` |
| Find tags that are too generic (notes, misc) | `tagex analyze quality /vault` |
| Understand which tags appear together | `tagex analyze pairs /vault` |
| Reduce singleton tags (used only once) | `tagex analyze recommendations /vault --analyzers singletons --export ops.yaml` |
| Suggest tags for untagged/lightly-tagged notes | `tagex analyze suggest --vault-path /vault --min-tags 2` |
| Clean up all duplicates systematically | Use `recommendations` command or run all: plurals, synonyms, singletons |

**Note:** All `analyze` commands now accept either a vault path (auto-extracts tags) or a JSON file (pre-extracted tags).

---

## Quick Start Guide

### Prerequisites

Extract tags before running analysis:

| Command | Purpose | Output |
|:--------|:--------|:-------|
| `tagex stats /vault` | Quick vault overview | Console statistics |
| `tagex extract /vault -o tags.json` | Filtered tags for analysis | JSON file |
| `tagex extract /vault --no-filter -o raw_tags.json` | Raw tags with noise | JSON file |
| `tagex extract /vault --tag-types both -o all_tags.json` | Both frontmatter and inline | JSON file |

The analysis scripts expect tag data in JSON format by default.

### Analysis Workflow

All analysis commands now support **dual input modes**:
- **Vault path**: Automatically extracts tags before analysis
- **JSON file**: Uses pre-extracted tag data

| Analysis Type | Command (Vault) | Command (JSON) | Purpose |
|:--------------|:----------------|:---------------|:---------|
| **Pair Analysis** | `tagex analyze pairs /vault` | `tagex analyze pairs tags.json` | Find tags that appear together |
| **Merge Analysis** | `tagex analyze merge /vault` | `tagex analyze merge tags.json` | Get consolidation suggestions |
| **Quality Analysis** | `tagex analyze quality /vault` | `tagex analyze quality tags.json` | Detect overbroad and generic tags |
| **Synonym Analysis** | `tagex analyze synonyms /vault` | `tagex analyze synonyms tags.json` | Find semantic synonym candidates |
| **Plural Analysis** | `tagex analyze plurals /vault` | `tagex analyze plurals tags.json` | Detect singular/plural variants |

**Common Options:**
- `--min-pairs N` / `--min-usage N` / `--min-shared N`: Set minimum thresholds
- `--no-filter`: Include technical noise
- `--no-sklearn`: Use pattern-based fallback (merge only)
- `--no-transformers`: Use pattern-based fallback (synonyms only)
- `--show-related`: Show related tags based on co-occurrence (synonyms only)
- `--prefer usage|plural|singular`: Override plural preference (plurals only)

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
| **Frontmatter** | `tagex extract /vault -o fm_tags.json` | Formal categorization |
| **Inline** | `tagex --tag-types inline /vault extract -o inline_tags.json` | Content-driven tagging |
| **Both** | `tagex extract /vault --tag-types both -o all_tags.json` | Complete pattern analysis |

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
| `tagex stats /vault` | Basic vault overview |
| `tagex stats /vault --top 10 --format json` | Top 10 tags in JSON format |
| `tagex stats /vault --no-filter` | Include technical noise |
| `tagex stats /vault --top 25` | Custom top tag count |

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

### Complete Analysis Integration Workflow

| Step | Command | When to Use |
|:-----|:--------|:------------|
| 1. Overview | `tagex stats /vault` | Always start here - get baseline metrics |
| 2. Extract | `tagex extract /vault -o tags.json` | Create snapshot for analysis |
| 3. Quality check | `tagex analyze quality tags.json` | Identify overbroad/generic tags |
| 4. Find plurals | `tagex analyze plurals tags.json` | Detect singular/plural splits |
| 5. Find synonyms | `tagex analyze synonyms tags.json` | Context-based duplicate detection |
| 6. Merge analysis | `tagex analyze merge tags.json` | Semantic/morphological duplicates |
| 7. Pair analysis | `tagex analyze pairs tags.json` | Understand tag relationships |
| 8. Apply changes | `tagex merge /vault tag1 tag2 --into new-tag` | Preview (safe by default) |
| 9. Verify | `tagex stats /vault` | Confirm improvements |

**Recommended Workflow for Tag Cleanup:**

```bash
# Step 1: Baseline
tagex stats /vault --top 20

# Step 2: Extract current state
tagex extract /vault -o tags.json

# Step 3: Run all analyses
tagex analyze quality tags.json > quality-report.txt
tagex analyze plurals tags.json > plurals-report.txt
tagex analyze synonyms tags.json --min-shared 3 > synonyms-report.txt
tagex analyze merge tags.json > merge-report.txt
tagex analyze pairs tags.json --min-pairs 3 > pairs-report.txt

# Step 4: Review reports and plan consolidations

# Step 5: Apply merges (safe by default)
tagex merge /vault tag1 tag2 --into target              # Preview changes
tagex merge /vault tag1 tag2 --into target --execute    # Apply changes

# Step 6: Verify improvements
tagex extract /vault -o tags-after.json
tagex stats /vault --top 20
```

---

## Pair Analyzer (`pair_analyzer.py`)

**Function:** Calculates frequency of tag pairs that appear together in the same files. Now includes built-in tag filtering to remove noise.

### Why This Matters

Pair analysis reveals the hidden structure of your knowledge system - showing how tags naturally cluster and which tags serve as organizational hubs:

**Problems solved:**
- **Understanding relationships:** Which tags actually appear together vs. which you think do
- **Finding natural categories:** Discover emergent tag clusters you didn't plan
- **Identifying hub tags:** Find the 5-10 tags that organize everything else
- **Improving tagging:** See which combinations work and which don't

**Real impact:**
- Discover that "work" appears with 150 different tags → it's a hub
- Find natural clusters: {python, data, jupyter, pandas} always appear together
- Identify orphan tags that never pair with others → candidates for deletion
- Guide creation of nested tags: high pair frequency suggests hierarchy

**Strategic insights:**
- **Hub tags** (high pair count) are architectural - they organize your vault
- **Cluster detection** shows natural topic groupings in your knowledge
- **Singleton tags** that never pair might be too specific or unused
- **Pair frequency** indicates topic coherence and note relationships

This is the only analysis that shows how tags work together rather than in isolation.

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

### Why This Matters

The merge analyzer is your most powerful tool for tag consolidation - it catches duplicates that plurals and synonyms miss by understanding morphological and semantic relationships:

**Problems solved:**
- **Spelling variations:** "writng" vs "writing" (typos)
- **Morphological variants:** "write", "writing", "writer", "writers" (same root)
- **Semantic similarity:** Tags that share character patterns and meaning
- **Compound detection:** All of the above for hyphenated and nested tags

**Real impact:**
- Detect typos you didn't know existed: "writting" → "writing"
- Consolidate word families: {organize, organizing, organization} → one canonical form
- Find semantic relationships: "music" and "audio" share character patterns
- Clean up 15-20% of tags in typical vaults through consolidation

**Why TF-IDF embeddings work:** Character-level analysis captures shared roots, affixes, and patterns that indicate morphological relationships. Tags like "writing" and "writers" share most character n-grams, scoring 0.72 similarity despite different endings.

**Unique strength:** Only analysis that combines multiple detection methods (string similarity, semantic embeddings, file overlap, morphological patterns) for comprehensive duplicate detection.

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
| `tagex merge /vault writers writering --into writing` | Preview suggestions |

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

---

## Quality Analyzer (`breadth_analyzer.py`)

**Function:** Detects tags that are used so broadly they lose specificity and usefulness. Provides specificity scoring and refinement suggestions.

### Why This Matters

Overbroad tags are silent killers of knowledge organization. When a tag appears in 50-70% of your notes, it becomes meaningless - clicking it returns hundreds of results instead of surfacing related content. This analysis helps you:

**Problems solved:**
- **Search overload:** Tags returning too many results to be useful
- **Organization breakdown:** Generic tags don't help you find related notes
- **Cognitive overhead:** Vague tags require mental effort to categorize
- **Lost specificity:** Broad tags mask the actual topic of notes

**Real impact:**
- Transform "notes" (892 uses) into "notes/meeting", "notes/research", "notes/personal"
- Replace "misc" (234 uses) with specific categories
- Identify when tags have lost their semantic value
- Guide creation of hierarchical tag systems that actually work

### The Overbroad Tag Problem

Some tags appear in so many files that they become meaningless for organization:

```
notes (892 files, 68% coverage) - What kind of notes?
ideas (654 files, 50% coverage) - Ideas about what?
misc (234 files, 18% coverage) - Catchall with no semantic value
work (432 files, 33% coverage) - Too general to be useful
```

Overbroad tags create noise and reduce the value of your tagging system. The quality analyzer identifies these problems and suggests specific alternatives.

### Detection Methods

| Method | Threshold | Description |
|:-------|:----------|:------------|
| **High Coverage** | 30%+ of files | Tag appears in too many files |
| **Very High Coverage** | 50%+ of files | Tag is significantly overused |
| **Extreme Coverage** | 70%+ of files | Tag has become nearly universal |
| **Specificity Score** | Combined metric | Information content + structure + diversity |

### Algorithm Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Tag Usage Data  │───►│ Calculate        │───►│ Assess          │
│ (files per tag) │    │ Coverage Ratio   │    │ Severity Level  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Specificity      │───►│ Refinement      │
                       │ Scoring          │    │ Suggestions     │
                       └──────────────────┘    └─────────────────┘
```

### Specificity Scoring

The analyzer calculates a composite specificity score using:

**1. Information Content (IC):** How rare is this tag?
```python
ic_score = -log₂(tag_usage / total_files)
```
- Higher scores = more specific (rarer) tags
- Lower scores = more generic (common) tags

**2. Structural Depth:** Does the tag have hierarchy?
- Nested tags: `work/meetings/standup` → higher specificity
- Compound tags: `machine-learning` → moderate specificity
- Flat tags: `notes` → lower specificity

**3. Generic Word Penalty:** Is the tag itself generic?
- Penalized words: notes, ideas, misc, general, stuff, things, temp, draft, random, other, various
- Penalty: -5 points for generic words

**4. Co-occurrence Diversity:** How many different tags does it appear with?
- High diversity (>50% of all tags) suggests overuse
- Penalty: -2 points for excessive diversity

**Combined Score:**
```
Total Score = IC + Structural Depth + Generic Penalty + Diversity Penalty
```

### Sample Output

```bash
$ tagex analyze quality tags.json

=== TAG QUALITY ANALYSIS ===

OVERBROAD TAGS (by severity):

  notes
    Coverage: 68.3% (892/1306 files)
    Severity: extreme
    Specificity score: 0.2 (too_broad)

    Suggested refinements:
      Consider breaking down 'notes' into:
        - notes/meeting
        - notes/research
        - notes/personal
        - notes/class
        - notes/project

  ideas
    Coverage: 50.1% (654/1306 files)
    Severity: very_high
    Specificity score: 0.8 (moderately_specific)

    Existing nested tags (use these instead):
        - ideas/project
        - ideas/writing
        - ideas/business

  misc
    Coverage: 17.9% (234/1306 files)
    Severity: high
    Specificity score: -2.3 (too_broad)

    Recommendation: Eliminate this tag entirely. Use specific categories instead.


SPECIFICITY ANALYSIS:

  Too Broad (score < 1.0):
    misc [-2.3]
    notes [0.2]
    ideas [0.8]

  Appropriately Specific (score 3.0-5.0):
    python/data-analysis [4.2]
    neuroscience/memory [3.8]
    web-development [3.5]

  Highly Specific (score >= 5.0):
    neuroscience/memory/working-memory [6.1]
    python/data-analysis/pandas [5.7]
    machine-learning/transformers/bert [5.4]
```

### Usage Examples

| Command | Description |
|:--------|:------------|
| `tagex analyze quality tags.json` | Standard quality analysis |
| `tagex analyze quality tags.json --no-filter` | Include all tags |
| `tagex analyze quality tags.json --min-usage 10` | Only analyze tags with 10+ uses |

### Actionable Insights

The quality analyzer helps you:

1. **Identify overly generic tags** that need refinement
2. **Discover natural breakdowns** from co-occurrence patterns
3. **Find existing specific alternatives** you should be using
4. **Prioritize cleanup efforts** with severity levels
5. **Measure tag system health** with specificity scores

---

## Synonym Analyzer (`synonym_analyzer.py`)

**Function:** Detects tags with similar meanings using semantic embeddings from sentence-transformers. Distinguishes between true synonyms (alternative names for the same concept) and related tags (co-occurring topics).

### Why This Matters

Synonyms fragment your knowledge graph, splitting conceptually related notes across multiple tags. This silently degrades your vault's usefulness over time:

**Problems solved:**
- **Fragmented searches:** Looking for "film" misses notes tagged "movies"
- **Incomplete context:** Related notes scattered across synonym tags
- **Duplicate effort:** Creating multiple tags for the same concept
- **Lost connections:** Graph view shows separate clusters that should be connected

**Real impact:**
- Consolidate "tech" (89 uses) + "technology" (5 uses) = 94 uses under one tag
- Unite "film" (67) + "movies" (23) = 90 uses for better discoverability
- Merge semantic equivalents: "poem" + "poetry", "mcps" + "mcp"
- Strengthen tag-based relationships by eliminating semantic duplicates

**Key improvement:** Previous co-occurrence based detection was fundamentally flawed - it suggested "parenting + sons" as synonyms just because they appeared together. The new semantic approach correctly identifies tags that are **alternatives** for the same concept, not just related topics.

### The Synonym Problem

Tags with different names but equivalent meanings fragment your knowledge graph:

```
tech (89 uses) ~ technology (5 uses)
film (45 uses) ~ movies (12 uses)
poem (34 uses) ~ poetry (8 uses)
mcps (67 uses) ~ mcp (23 uses)
```

These duplicates reduce discoverability and make tag-based searches less effective.

### Detection Methods

| Method | Approach | Strength |
|:-------|:---------|:---------|
| **Semantic Similarity** | Sentence-transformer embeddings on tag names | Identifies true alternatives |
| **Co-occurrence Filtering** | Excludes pairs that appear together frequently | Filters related topics |
| **Pattern Matching** | Morphological analysis fallback | Works without transformers |
| **Acronym Detection** | First-letter matching | Catches common abbreviations |

### Algorithm: Semantic Detection

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Tag Names       │───►│ Embed with       │───►│ Calculate       │
│ (not contexts)  │    │ all-MiniLM-L6-v2 │    │ Cosine Similarity│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ "film" embedding │───►│ Similarity ≥ 0.7│
                       │ "movies" embed.  │    │ AND co-occur <30%│
                       │                  │    │ → Synonyms      │
                       └──────────────────┘    └─────────────────┘
```

**Key difference from old approach:**
- **Old:** Analyzed which tags appeared **together** (co-occurrence) → found related topics
- **New:** Analyzes tag **names** for semantic similarity → finds alternative names

**Semantic Similarity:**
```
cosine_similarity(embed("film"), embed("movies")) = 0.872
```

**Co-occurrence Filter:**
```
If film and movies appear together in >30% of files → related topics, not synonyms
If film and movies rarely appear together → true alternatives (synonyms)
```

### Sample Output

```bash
$ tagex analyze synonyms /vault --min-similarity 0.7

=== SYNONYM ANALYSIS ===
Detected using: sentence-transformers (semantic similarity)

SEMANTIC SYNONYMS (similarity ≥ 0.70, co-occurrence ≤ 30%):

  Group 1:
    film (67 uses) ≈ movies (23 uses)
    Semantic similarity: 0.872
    Co-occurrence: 8% (appear together in 5/65 files)
    Suggestion: Merge 'movies' → 'film'

  Group 2:
    poem (34 uses) ≈ poetry (8 uses)
    Semantic similarity: 0.849
    Co-occurrence: 12% (appear together in 3/42 files)
    Suggestion: Merge 'poetry' → 'poem'

  Group 3:
    mcps (12 uses) ≈ mcp (45 uses)
    Semantic similarity: 0.941
    Co-occurrence: 5% (appear together in 2/57 files)
    Suggestion: Merge 'mcps' → 'mcp'


RELATED TAGS (high co-occurrence - NOT synonyms):
(Use --show-related to display these)

  parenting + sons
    Semantic similarity: 0.45 (not synonyms)
    Co-occurrence: 78% (related topics, not alternatives)
    Recommendation: Keep separate - these are related concepts, not duplicates

  reddit + rodeo
    Semantic similarity: 0.23 (not synonyms)
    Co-occurrence: 12% (coincidental co-occurrence)
    Recommendation: Keep separate - unrelated tags
```

### User-Defined Synonyms

You can create a `.tagex/synonyms.yaml` file in your vault to define explicit synonym relationships:

```yaml
# .tagex/synonyms.yaml

# Canonical form as key, synonyms as list values
python:
  - py
  - python3

javascript:
  - js
  - ecmascript

neuro:
  - neurodivergent
  - neurodivergence
  - neurotype

tech:
  - technology
  - technical
```

**Initialize configuration:**
```bash
# Create .tagex/ directory with template files
tagex init /vault

# Edit .tagex/synonyms.yaml with your mappings
# Then validate the configuration
tagex validate /vault
```

**Loading configuration:**
```python
from tagex.config.synonym_config import SynonymConfig

config = SynonymConfig(vault_path)
canonical = config.get_canonical("py")  # Returns "python"
synonyms = config.get_synonyms("python")  # Returns {"py", "python3"}
```

### Usage Examples

| Command | Description |
|:--------|:------------|
| `tagex analyze synonyms /vault` | Auto-extract and detect synonyms |
| `tagex analyze synonyms tags.json` | Analyze pre-extracted tags |
| `tagex analyze synonyms /vault --min-similarity 0.8` | Higher similarity threshold |
| `tagex analyze synonyms /vault --show-related` | Show related tags (co-occurrence) |
| `tagex analyze synonyms /vault --no-transformers` | Pattern-based fallback |
| `tagex analyze synonyms /vault --no-filter` | Include all tags |

### Why Semantic Similarity Works

The new approach analyzes tag names directly to understand meaning:

1. **Embeds tag names** using pre-trained language models
2. **Measures semantic distance** between tag meanings
3. **Filters co-occurring pairs** to exclude related topics
4. **Identifies true alternatives** that mean the same thing

This approach correctly identifies synonyms that the old co-occurrence method missed:
- `film` and `movies` have similar meanings (0.872 similarity)
- `poem` and `poetry` are semantic equivalents (0.849 similarity)
- `tech` and `technology` are alternative names (0.885 similarity)

**What it correctly rejects:**
- `parenting` and `sons` appear together but aren't synonyms (related topics)
- `reddit` and `rodeo` coincidentally co-occur but are unrelated

---

## Plural Analyzer (`plural_normalizer.py`)

**Function:** Detects singular/plural variants of the same tag using irregular plural dictionaries and pattern-based analysis. Supports configurable preference modes.

### Why This Matters

Singular/plural splits are the most common and insidious form of tag fragmentation. They happen naturally as you create notes, but silently weaken your organization:

**Problems solved:**
- **Split tag power:** "book" (67 uses) + "books" (12 uses) = artificially divided
- **Inconsistent tagging:** Using both forms creates mental overhead
- **Weakened relationships:** Related notes split across variant forms
- **Search incompleteness:** Searching one form misses the other

**Real impact:**
- Consolidate "parent" (23) + "parents" (8) = 31 uses under consistent form
- Merge "child" (12) + "children" (8) = 20 uses with proper irregular plural
- Unite "family" (45) + "families" (3) = 48 uses in most-used form
- Eliminate 12-15 unnecessary variant tags in typical vaults

**Why this matters more than it seems:** Plural splits affect 20-30% of tags in most vaults. They're created unconsciously as you type, making them perfect candidates for automated detection and cleanup.

**Preference modes (configurable):**
- **usage** (default): Prefer the most commonly used form (smart default)
- **plural**: Always prefer plural forms (`books`, `ideas`, `projects`)
- **singular**: Always prefer singular forms (`book`, `idea`, `project`)

Configure in `.tagex/config.yaml` or override per-command with `--prefer`.

### The Plural Problem

Tags split between singular and plural forms dilute their organizational power:

```
parent (23 uses) / parents (8 uses)  → Keep 'parent' (usage mode, more common)
child (12 uses) / children (8 uses)  → Keep 'child' (usage mode, more common)
family (45 uses) / families (3 uses) → Keep 'family' (usage mode, more common)
tax-break (5 uses) / tax-breaks (2 uses) → Keep 'tax-break' (usage mode)
```

**Default behavior:** The analyzer uses **usage-based preference** - it recommends keeping whichever form is used more often. This is the most practical default for real vaults.

### Detection Methods

| Method | Examples | Coverage |
|:-------|:---------|:---------|
| **Irregular Plurals** | child→children, person→people, life→lives | 34 common pairs |
| **Pattern: -ies/-y** | family→families, category→categories | Common -y words |
| **Pattern: -ves/-f(e)** | life→lives, knife→knives, self→selves | -f/-fe words |
| **Pattern: -es** | watch→watches, box→boxes | -s,-x,-ch,-sh words |
| **Pattern: -s** | tag→tags, note→notes | Regular plurals |
| **Compound Words** | tax-break→tax-breaks, child/development→children/development | Nested/hyphenated |

### Algorithm Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Input Tag       │───►│ Check Irregular  │───►│ Apply Pattern   │
│ "family"        │    │ Dictionary       │    │ Rules           │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ No match         │───►│ -y → -ies       │
                       │                  │    │ "family" →      │
                       │                  │    │ "families"      │
                       └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Group Variants  │
                                               │ {family,        │
                                               │  families}      │
                                               └─────────────────┘
```

### Irregular Plurals Dictionary

The analyzer includes 34 common irregular plural pairs:

```python
IRREGULAR_PLURALS = {
    'child': 'children',
    'person': 'people',
    'man': 'men',
    'woman': 'women',
    'tooth': 'teeth',
    'foot': 'feet',
    'mouse': 'mice',
    'life': 'lives',
    'knife': 'knives',
    'leaf': 'leaves',
    'self': 'selves',
    'half': 'halves',
    'ox': 'oxen',
    'crisis': 'crises',
    'analysis': 'analyses',
    # ... and more
}
```

### Sample Output

```bash
$ tagex analyze plurals /vault

=== PLURAL VARIANT ANALYSIS ===
Using preference mode: usage (from .tagex/config.yaml)

DETECTED VARIANTS (usage-based preference):

  Irregular Plurals:
    child (12 uses) / children (8 uses)
      Recommendation: Merge into 'child' (more common, 60%)
      Command: tagex merge /vault children --into child

    person (5 uses) / people (23 uses)
      Recommendation: Merge into 'people' (more common, 82%)
      Command: tagex merge /vault person --into people

  Pattern: -ies/-y
    family (45 uses) / families (3 uses)
      Recommendation: Merge into 'family' (more common, 94%)
      Command: tagex merge /vault families --into family

    category (12 uses) / categories (34 uses)
      Recommendation: Merge into 'categories' (more common, 74%)
      Command: tagex merge /vault category --into categories

  Pattern: -ves/-f
    life (8 uses) / lives (3 uses)
      Recommendation: Merge into 'life' (more common, 73%)
      Command: tagex merge /vault lives --into life

  Pattern: -s (regular)
    parent (23 uses) / parents (8 uses)
      Recommendation: Merge into 'parent' (more common, 74%)
      Command: tagex merge /vault parents --into parent

    book (67 uses) / books (12 uses)
      Recommendation: Merge into 'book' (more common, 85%)
      Command: tagex merge /vault books --into book

  Compound Words:
    tax-break (5 uses) / tax-breaks (2 uses)
      Recommendation: Merge into 'tax-break' (more common, 71%)
      Command: tagex merge /vault tax-breaks --into tax-break


SUMMARY:
  Total variant groups: 12
  Total tags affected: 24
  Potential consolidations: 12 merges
  Preference mode: usage (configurable in .tagex/config.yaml)
```

### Usage Examples

| Command | Description |
|:--------|:------------|
| `tagex analyze plurals /vault` | Auto-extract and analyze with usage-based preference |
| `tagex analyze plurals tags.json` | Analyze pre-extracted tags |
| `tagex analyze plurals /vault --prefer plural` | Override to always prefer plurals |
| `tagex analyze plurals /vault --prefer singular` | Override to always prefer singulars |
| `tagex analyze plurals /vault --min-usage 5` | Only show variants with 5+ total uses |
| `tagex analyze plurals /vault --no-filter` | Include technical tags |

### Compound Word Handling

The analyzer handles plurals in compound and nested tags:

**Hyphenated compounds:**
- `tax-break` → `tax-breaks` (pluralize last component)
- `self-help` → `selves-help` (irregular plural on first component)

**Nested tags:**
- `child/development` → `children/development`
- `category/science` → `categories/science`

### Preference Mode Configuration

Configure plural preference in `.tagex/config.yaml`:

```yaml
plural:
  preference: usage          # usage, plural, or singular
  usage_ratio_threshold: 2.0 # Minimum ratio to prefer most-used form
```

**Preference modes:**

| Mode | Behavior | Best For |
|:-----|:---------|:---------|
| **usage** | Prefer the most-used form | Most practical (default) |
| **plural** | Always prefer plurals (`books`, `ideas`) | Collection-oriented tagging |
| **singular** | Always prefer singulars (`book`, `idea`) | Abstract concepts |

**Why usage mode is the default:**
- Respects existing tagging patterns in your vault
- Minimal disruption to established workflows
- Naturally consolidates under the familiar form
- No need to decide philosophical plural vs singular debates

**When to use other modes:**
- **plural**: Starting fresh with collection-oriented system
- **singular**: Vault focused on abstract concepts and theories

You can always override per-command with `--prefer` flag.

---

## Singleton Analyzer (`singleton_analyzer.py`)

### Purpose

The singleton analyzer identifies tags that appear only once (singletons) and suggests merging them into established frequent tags. This is particularly effective for reducing tag proliferation from typos, abbreviations, and one-off experimental tags.

**Why target singletons specifically?**
- **High noise-to-signal ratio**: Tags used once often don't serve a useful organizational purpose
- **Easy wins**: Clear merge targets when similar frequent tags exist
- **Vault health**: High singleton ratios (>50%) indicate poor tag reuse
- **Previous gap**: Other analyzers (synonyms, plurals, merge) filter out low-usage tags, missing singletons

### How It Works

The analyzer uses multiple similarity detection methods to match each singleton tag to potential frequent tag targets:

1. **String Similarity** (threshold: 0.85)
   - Catches typos: `machne-learning` → `machine-learning`
   - Detects abbreviations: `prog` → `programming`

2. **Character N-gram Similarity** (TF-IDF, threshold: 0.60)
   - Morphological relationships: `writer` → `writing`
   - Variations: `tech` → `technology`

3. **Semantic Similarity** (sentence-transformers, threshold: 0.70)
   - True synonyms: `ai` → `artificial-intelligence`
   - Related concepts: `audio` → `music`

4. **Co-occurrence** (threshold: 0.70)
   - If singleton appears in file that also has a frequent tag
   - Suggests contextual relationship

**Key constraint**: Only suggests merging singletons into tags with 5+ uses, ensuring we consolidate into established taxonomy, not the reverse.

### Usage

The singleton analyzer is **only available via the recommendations command**:

```bash
# Run singleton analyzer only
tagex analyze recommendations /vault --analyzers singletons --export cleanup.yaml

# Combine with other analyzers
tagex analyze recommendations /vault --analyzers synonyms,plurals,singletons --export ops.yaml

# Skip semantic analysis (faster, but less accurate)
tagex analyze recommendations /vault --analyzers singletons --no-transformers --export ops.yaml

# Review and apply
tagex apply cleanup.yaml          # Preview
tagex apply cleanup.yaml --execute  # Apply
```

### Output Format

Example operations in the generated YAML file:

```yaml
operations:
- type: merge
  source:
  - machne-learning  # singleton (1 use)
  target: machine-learning  # frequent (50 uses)
  reason: 'Singleton → frequent tag (String similarity: 0.952)'
  enabled: true
  metadata:
    confidence: 0.952
    source_analyzer: singletons
    method: string_similarity
    target_usage: 50

- type: merge
  source:
  - ai  # singleton (1 use)
  target: artificial-intelligence  # frequent (25 uses)
  reason: 'Singleton → frequent tag (Semantic similarity: 0.823)'
  enabled: true
  metadata:
    confidence: 0.823
    source_analyzer: singletons
    method: semantic
    target_usage: 25
```

### Configuration

The analyzer respects standard configuration:
- **Exclusions** (`.tagex/exclusions.yaml`): Excluded tags won't be suggested for merging
- **User synonyms** (`.tagex/synonyms.yaml`): User-defined mappings take priority

### Thresholds

| Method | Default Threshold | Purpose |
|:-------|:-----------------|:--------|
| String similarity | 0.85 | High precision for typo detection |
| TF-IDF similarity | 0.60 | Catch morphological variants |
| Semantic similarity | 0.70 | True synonym detection |
| Co-occurrence | 0.70 | Contextual relationship |
| Frequent threshold | 5 uses | Minimum to be considered "established" |

### When to Use

**Good for:**
- High singleton ratios (>50% from `tagex stats`)
- Post-initial-tagging cleanup
- Consolidating experimental tags
- Finding typos and abbreviations

**Not ideal for:**
- New vaults with few tags
- When you want to keep unique categorical tags
- Tags that are legitimately one-off references

### Example Workflow

```bash
# 1. Check singleton ratio
tagex stats /vault
# Output: Singletons (used once): 563 (67.7%)

# 2. Generate singleton reduction recommendations
tagex analyze recommendations /vault --analyzers singletons --export singleton-cleanup.yaml

# 3. Review the generated file
# Edit singleton-cleanup.yaml:
# - Set enabled: false for suggestions you disagree with
# - Modify target tags if needed
# - Delete operations you don't want

# 4. Preview changes
tagex apply singleton-cleanup.yaml

# 5. Apply changes
tagex apply singleton-cleanup.yaml --execute

# 6. Verify improvement
tagex stats /vault
# Output: Singletons (used once): 127 (23.4%)  ← Much better!
```

### Comparison to Other Analyzers

| Analyzer | Focus | Minimum Usage |
|:---------|:------|:--------------|
| **synonyms** | Semantic similarity between any tags | 3+ uses |
| **plurals** | Singular/plural variants | 2+ uses |
| **merge** | String/TF-IDF similarity | 3+ uses |
| **singletons** | Single-use tags → frequent tags | Singleton (1 use) → Frequent (5+ uses) |

The singleton analyzer is the **only analyzer** that specifically targets tags used exactly once, filling a critical gap in tag consolidation workflows.

---

## Content Analyzer (`content_analyzer.py`)

### Purpose

The content analyzer suggests relevant tags for notes based on their text content. It helps you discover appropriate existing tags for untagged or lightly-tagged notes by analyzing semantic similarity between note content and tag usage patterns.

**Why suggest tags from content?**
- **Improve discoverability**: Untagged notes are invisible to tag-based navigation
- **Maintain consistency**: Suggests existing tags rather than creating new ones
- **Save time**: Automated suggestions for bulk tagging workflows
- **Surface connections**: Reveals thematic relationships in content

### How It Works

The analyzer uses semantic similarity to match note content against the usage patterns of existing tags:

1. **Content Extraction**
   - Extracts text from note body (excluding frontmatter)
   - Cleans and processes markdown formatting

2. **Tag Context Building**
   - For each existing tag, builds a "context" from all notes using that tag
   - Aggregates content from tagged notes to represent tag meaning

3. **Semantic Matching** (when transformers available)
   - Embeds note content using sentence-transformers (all-MiniLM-L6-v2)
   - Embeds tag contexts using the same model
   - Calculates cosine similarity between note and each tag context
   - Suggests tags with highest similarity scores

4. **Keyword Fallback** (when transformers unavailable)
   - Uses TF-IDF to extract key terms from note content
   - Matches against tag names and usage patterns
   - Scores based on keyword overlap

**Key constraint**: Only suggests existing tags (doesn't create new ones), ensuring consistency with your established taxonomy.

### Usage

```bash
# Suggest tags for notes with < 2 tags
tagex analyze suggest --vault-path /vault --min-tags 2

# Suggest for specific files or directories
tagex analyze suggest /vault/projects/ --vault-path /vault --min-tags 1

# Export suggestions to YAML for review
tagex analyze suggest --vault-path /vault --min-tags 2 --export suggestions.yaml

# Higher confidence threshold
tagex analyze suggest --vault-path /vault --min-confidence 0.5

# More suggestions per note
tagex analyze suggest --vault-path /vault --top-n 5

# Skip semantic analysis (faster, keyword-based only)
tagex analyze suggest --vault-path /vault --no-transformers
```

### Output Format

**Console output:**
```
TAG SUGGESTIONS (15 notes)
======================================================================

1. /vault/projects/machine-learning-notes.md
   Current tags: (none)
   Suggested tags:
     - machine-learning (confidence: 0.78)
     - python (confidence: 0.65)
     - data-science (confidence: 0.52)

2. /vault/ideas/web-scraping.md
   Current tags: coding
   Suggested tags:
     - web-development (confidence: 0.71)
     - python (confidence: 0.68)
     - automation (confidence: 0.45)
```

**YAML export (for apply workflow):**
```yaml
metadata:
  generated_by: tagex analyze suggest
  timestamp: 2025-10-28T00:19:34
  vault_path: /vault
  total_suggestions: 15

operations:
- type: add_tags
  target: /vault/projects/machine-learning-notes.md
  source:
  - machine-learning
  - python
  - data-science
  reason: 'Content-based suggestion (avg confidence: 0.65)'
  enabled: true
  metadata:
    confidence: 0.65
    source_analyzer: content
    current_tags: []
    confidences: [0.78, 0.65, 0.52]
    methods: [semantic, semantic, semantic]
```

### Configuration

| Parameter | Default | Purpose |
|:----------|:--------|:--------|
| `--min-tags` | 2 | Only process notes with fewer than N tags |
| `--max-tags` | None | Also require notes have at most N tags |
| `--top-n` | 3 | Number of tags to suggest per note |
| `--min-confidence` | 0.3 | Minimum confidence threshold (0.0-1.0) |
| `--no-transformers` | False | Use keyword matching instead of semantic |

### Integration with Apply Workflow

The content analyzer generates operations compatible with `tagex apply`:

```bash
# 1. Generate suggestions
tagex analyze suggest --vault-path /vault --min-tags 2 --export suggestions.yaml

# 2. Review and edit suggestions.yaml
# - Set enabled: false for suggestions you disagree with
# - Remove specific tags from source lists
# - Delete operations entirely

# 3. Preview changes
tagex apply suggestions.yaml --vault-path /vault

# 4. Apply tags
tagex apply suggestions.yaml --vault-path /vault --execute
```

### When to Use

**Good for:**
- Vaults with many untagged or minimally tagged notes
- Bulk tagging workflows after importing content
- Ensuring consistent tag application across vault
- Discovering thematic connections in content

**Not ideal for:**
- Notes with specialized jargon not represented in existing tags
- Very short notes (<100 words) with limited content
- Notes that genuinely don't fit existing tag categories
- When you want to create new tags rather than reuse existing ones

### Example Workflow

```bash
# 1. Check how many notes lack tags
tagex stats /vault
# Output: Files without tags: 234

# 2. Generate suggestions for untagged notes
tagex analyze suggest --vault-path /vault --min-tags 1 --export tag-suggestions.yaml

# 3. Review suggestions
# - Open tag-suggestions.yaml
# - Disable suggestions you don't want
# - Modify tag lists

# 4. Preview
tagex apply tag-suggestions.yaml --vault-path /vault

# 5. Apply
tagex apply tag-suggestions.yaml --vault-path /vault --execute

# 6. Verify improvement
tagex stats /vault
# Output: Files without tags: 87  ← Much better!
```

### Comparison to Other Analyzers

| Analyzer | Input | Output | Purpose |
|:---------|:------|:-------|:--------|
| **synonyms** | Existing tags | Merge operations | Consolidate duplicate tags |
| **plurals** | Existing tags | Merge operations | Fix singular/plural splits |
| **singletons** | Existing tags | Merge operations | Reduce rarely-used tags |
| **content** | Note content | Add operations | Suggest tags for untagged notes |

The content analyzer is the **only analyzer** that adds tags to notes rather than consolidating existing tags, making it complementary to the cleanup-focused analyzers.

---

## Unified Recommendations System

### Overview

The `recommendations` command consolidates suggestions from all analyzers into a single editable YAML operations file, streamlining the tag cleanup workflow.

**Why use this instead of individual analyzers?**
- Run all analyzers in one command
- Get deduplicated recommendations
- Edit and enable/disable operations before applying
- Preview changes safely (dry-run by default)
- Apply multiple operations in sequence automatically

### Usage

```bash
# Generate recommendations from all analyzers
tagex analyze recommendations /vault --export operations.yaml

# Run specific analyzers only
tagex analyze recommendations /vault --export ops.yaml --analyzers plurals,synonyms

# Skip semantic analysis (faster, no sentence-transformers required)
tagex analyze recommendations /vault --export ops.yaml --no-transformers

# Adjust similarity thresholds
tagex analyze recommendations /vault --export ops.yaml --min-similarity 0.8
```

### Operations File Format

The generated YAML file is fully editable:

```yaml
# Tag Operations Plan
# Generated: 2025-10-26 09:35:52
# Analyzers: synonyms, plurals, merge
#
# Edit this file to customize operations:
# - Set enabled: false to skip an operation
# - Modify source/target tags as needed
# - Delete operations you don't want
# - Reorder operations (they execute top-to-bottom)
#
# Preview with: tagex apply <this-file>
# Apply with:   tagex apply <this-file> --execute

operations:
- type: merge
  source:
  - machine-learning
  - ml
  target: machine-learning
  reason: 'Semantic synonyms (similarity: 0.891)'
  enabled: true
  metadata:
    confidence: 0.891
    source_analyzer: synonyms
    co_occurrence_ratio: 0.15

- type: merge
  source:
  - book
  target: books
  reason: 'Plural variant (most-used: 23/25 uses)'
  enabled: true
  metadata:
    confidence: 0.92
    source_analyzer: plurals
    total_usage: 25
```

### Applying Operations

```bash
# Preview changes (default - safe, no modifications)
tagex apply operations.yaml

# Apply changes (requires explicit --execute flag)
tagex apply operations.yaml --execute

# Specify vault if different from working directory
tagex apply operations.yaml --vault-path /path/to/vault --execute

# Process specific tag types
tagex apply operations.yaml --tag-types both --execute
```

### Safety Features

1. **Preview mode by default**: No `--execute` flag = no file modifications
2. **Explicit execution**: Must use `--execute` to actually apply changes
3. **Editable recommendations**: Review, modify, enable/disable before applying
4. **Deduplication**: Multiple analyzers suggesting the same merge = single operation
5. **Confidence scores**: Make informed decisions about which operations to apply
6. **Metadata tracking**: See which analyzer suggested each operation
7. **Operation logs**: All modifications are logged for audit trail

### Workflow Example

```bash
# 1. Initialize configuration (first time)
tagex init /vault

# 2. Generate recommendations
tagex analyze recommendations /vault --export ops.yaml

# Output:
# Analyzing 450 tags for improvement opportunities...
# Enabled analyzers: synonyms, plurals, merge
#
#   Running synonym analyzer...
#   Running plural analyzer...
#   Running merge analyzer...
#
# RECOMMENDATIONS SUMMARY
# Total operations: 23
# By analyzer:
#   synonyms: 8
#   plurals: 12
#   merge: 3

# 3. Review and edit ops.yaml
# - Disable operations you don't want (enabled: false)
# - Modify source/target tags
# - Delete operations
# - Reorder operations

# 4. Preview changes
tagex apply ops.yaml

# 5. Apply changes
tagex apply ops.yaml --execute

# 6. Verify improvements
tagex health /vault
```

### Command Options

**`tagex analyze recommendations` options:**

| Option | Description | Default |
|:-------|:------------|:--------|
| `--export PATH` | Export operations to YAML file | None (print to stdout) |
| `--analyzers TEXT` | Comma-separated list of analyzers (synonyms,plurals,singletons) | `synonyms,plurals` |
| `--min-similarity FLOAT` | Minimum semantic similarity (0.0-1.0) | `0.7` |
| `--no-transformers` | Skip semantic analysis (faster) | False |
| `--tag-types` | Tag types to process | `frontmatter` |
| `--no-filter` | Include all raw tags | False |

**`tagex apply` options:**

| Option | Description | Default |
|:-------|:------------|:--------|
| `--execute` | **REQUIRED** to actually apply changes | False (preview mode) |
| `--vault-path PATH` | Vault path if different from working directory | Current directory |
| `--tag-types` | Tag types to process | `frontmatter` |

### Benefits

1. **Efficiency**: Run all analyzers once, get consolidated recommendations
2. **Reviewability**: See all changes before applying in a single editable file
3. **Flexibility**: Enable/disable individual operations, reorder, modify
4. **Safety**: Preview mode by default, explicit flag required to modify files
5. **Traceability**: Operation logs track all modifications
6. **Automation**: Apply multiple operations in sequence automatically

### Comparison to Individual Analyzers

**Traditional workflow:**
```bash
tagex analyze synonyms /vault     # Review output
tagex analyze plurals /vault      # Review output
tagex analyze merge /vault        # Review output
# Manually run merge commands one by one
tagex merge /vault tag1 tag2 --into target1
tagex merge /vault tag3 tag4 --into target2
# ...many more commands...
```

**Unified recommendations workflow:**
```bash
tagex analyze recommendations /vault --export ops.yaml  # All analyzers
# Edit ops.yaml once
tagex apply ops.yaml --execute                         # Apply all at once
```

The recommendations system is the **recommended approach** for systematic tag cleanup across your vault.
