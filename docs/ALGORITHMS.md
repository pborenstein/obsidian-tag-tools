# Tag Analysis Algorithms - Technical Reference

This document provides detailed technical explanations of the algorithms used in tagex's analysis modules. For user-focused documentation, see [ANALYTICS.md](ANALYTICS.md).

**Audience:** Developers, contributors, and those interested in understanding the mathematics and implementation details.

## Table of Contents

1. [Semantic Similarity Detection](#semantic-similarity-detection)
2. [Plural Variant Detection](#plural-variant-detection)
3. [Synonym Detection](#synonym-detection)
4. [Overbroad Tag Detection](#overbroad-tag-detection)
5. [Pair Analysis](#pair-analysis)
6. [Singleton Tag Analysis](#singleton-tag-analysis)
7. [Content-Based Tag Suggestions](#content-based-tag-suggestions)
8. [Performance Characteristics](#performance-characteristics)
9. [References](#references)

---

## Semantic Similarity Detection

**Module:** `tagex/analysis/merge_analyzer.py`

**Key Functions:**
- `find_semantic_duplicates_embedding()` - tagex/analysis/merge_analyzer.py:175
- `find_similar_tags()` - tagex/analysis/merge_analyzer.py:85

**Purpose:** Detect semantically similar tags using character-level pattern analysis and TF-IDF embeddings.

### Algorithm: TF-IDF with Character N-grams

The merge analyzer uses **character-level n-gram analysis** rather than word-level features because tags are typically short (1-3 words) and character patterns are more informative for detecting morphological relationships.

#### Step 1: Character N-gram Extraction

For each tag, extract all contiguous character sequences of length 2-4:

```
Tag: "writing"
┌───────────────────────────────────────────────┐
│ 2-grams: [wr][ri][it][ti][in][ng]             │
│ 3-grams: [wri][rit][iti][tin][ing]            │
│ 4-grams: [writ][riti][itin][ting]             │
└───────────────────────────────────────────────┘
```

**Implementation** (tagex/analysis/merge_analyzer.py:197):
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    analyzer='char_wb',     # Character analysis with word boundaries
    ngram_range=(2, 4),     # Use 2, 3, and 4 character n-grams
    lowercase=True,         # Case normalization
    max_features=1000       # Limit feature space
)
```

**Why character n-grams?**
- Captures morphological relationships (shared roots, affixes)
- Robust to typos and spelling variations
- Language-agnostic (works across naming conventions)
- Better for short text than word-level features

#### Step 2: TF-IDF Vectorization

Convert character n-grams to weighted numerical vectors:

**TF (Term Frequency):** How often does pattern `p` appear in tag `t`?
```
TF(p, t) = count(p in t) / total_patterns(t)
```

**IDF (Inverse Document Frequency):** How rare is pattern `p` across all tags?
```
IDF(p) = log(total_tags / tags_containing(p))
```

**TF-IDF Score:**
```
TF-IDF(p, t) = TF(p, t) × IDF(p)
```

**Effect:** Common patterns (like "ing", "er") get lower weights; distinctive patterns get higher weights.

**Example:**
```
Tag: "writing"
Vector: [
  ("wr", 0.42),    # Distinctive → high weight
  ("wri", 0.51),   # Very distinctive → higher weight
  ("ing", 0.08),   # Common → low weight
  ("tin", 0.35),   # Moderately distinctive
  ...
]
```

#### Step 3: Cosine Similarity

Calculate similarity between tag vectors using cosine of the angle between them:

```
             A · B
cos(θ) = ─────────────
          ||A|| × ||B||

Where:
  A · B     = dot product (Σ Aᵢ × Bᵢ)
  ||A||     = magnitude (√Σ Aᵢ²)
  ||B||     = magnitude (√Σ Bᵢ²)
```

**Range:** 0.0 (orthogonal/unrelated) to 1.0 (identical)

**Example** (tagex/analysis/merge_analyzer.py:207):
```python
from sklearn.metrics.pairwise import cosine_similarity

# Tags: ["writing", "writers", "music"]
tfidf_matrix = vectorizer.fit_transform(tags)
# Result: 3×1000 matrix (3 tags, up to 1000 features)

similarity_matrix = cosine_similarity(tfidf_matrix)
# Result: 3×3 matrix showing all pairwise similarities
# [[1.00, 0.72, 0.12],    # writing vs [writing, writers, music]
#  [0.72, 1.00, 0.15],    # writers vs [writing, writers, music]
#  [0.12, 0.15, 1.00]]    # music vs [writing, writers, music]
```

#### Step 4: Threshold Filtering

Tags with similarity ≥ 0.6 are considered semantic duplicates:

```
Similarity Scale:
1.0 ████████████████████ Identical
0.9 ██████████████████▒▒
0.8 ████████████████▒▒▒▒ Very similar
0.7 ██████████████▒▒▒▒▒▒ ← "writing" vs "writers"
0.6 ████████████▒▒▒▒▒▒▒▒ ← THRESHOLD
0.5 ██████████▒▒▒▒▒▒▒▒▒▒
0.4 ████████▒▒▒▒▒▒▒▒▒▒▒▒ ← "music" vs "audio"
0.3 ██████▒▒▒▒▒▒▒▒▒▒▒▒▒▒
```

**Threshold rationale:**
- 0.8+: Too conservative, misses valid duplicates
- 0.6-0.7: Balanced, catches semantic relationships
- <0.5: Too aggressive, false positives

### Fallback: Morphological Pattern Matching

When scikit-learn is unavailable (`--no-sklearn`), use rule-based stem extraction (tagex/analysis/merge_analyzer.py:248):

```python
def find_semantic_duplicates_pattern(tag_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract morphological stems by removing common suffixes."""
    stems = set()
    tag_lower = tag.lower()

    # Remove suffixes to find base forms
    if tag_lower.endswith('s'):      stems.add(tag_lower[:-1])    # plural
    if tag_lower.endswith('ing'):    stems.add(tag_lower[:-3])    # present participle
    if tag_lower.endswith('er'):     stems.add(tag_lower[:-2])    # agent noun
    if tag_lower.endswith('ed'):     stems.add(tag_lower[:-2])    # past tense
    if tag_lower.endswith('tion'):   stems.add(tag_lower[:-4])    # abstract noun
    if tag_lower.endswith('ly'):     stems.add(tag_lower[:-2])    # adverb

    return stems
```

**Examples:**
- `write, writing, writer, writers` → stem: `writ`
- `organize, organization` → stem: `organiz`
- `quick, quickly` → stem: `quick`

**Grouping:** Tags sharing stems are grouped as variants.

### Complexity Analysis

**Time Complexity:**
- N-gram extraction: O(n × m) where n = number of tags, m = avg tag length
- TF-IDF vectorization: O(n × f) where f = feature count (max 1000)
- Similarity matrix: O(n²) - all pairwise comparisons
- **Overall: O(n²)** - dominated by similarity calculation

**Space Complexity:**
- TF-IDF matrix: O(n × f) - sparse matrix, typically <10MB for 1000 tags
- Similarity matrix: O(n²) - dense matrix, grows quadratically
- **Overall: O(n²)** for similarity matrix storage

**Practical Performance:**
- 100 tags: <1s, <1MB
- 1,000 tags: 5-10s, ~8MB
- 10,000 tags: 60-120s, ~800MB

---

## Plural Variant Detection

**Module:** `tagex/analysis/plural_normalizer.py`

**Key Functions:**
- `normalize_plural_forms()` - tagex/analysis/plural_normalizer.py:40
- `normalize_compound_plurals()` - tagex/analysis/plural_normalizer.py:98
- `get_preferred_form()` - tagex/analysis/plural_normalizer.py:137

**Purpose:** Detect singular/plural variants using irregular plural dictionary and pattern-based rules.

### Algorithm: Multi-Strategy Normalization

The plural detector uses three complementary approaches:

#### Strategy 1: Irregular Plural Dictionary

Hardcoded lookup table for English irregular plurals (tagex/analysis/plural_normalizer.py:13):

```python
IRREGULAR_PLURALS = {
    'child': 'children',
    'person': 'people',
    'man': 'men',
    'woman': 'women',
    'tooth': 'teeth',
    'foot': 'feet',
    'mouse': 'mice',
    'goose': 'geese',
    'ox': 'oxen',
    'crisis': 'crises',
    'analysis': 'analyses',
    'thesis': 'theses',
    'phenomenon': 'phenomena',
    'criterion': 'criteria',
    # ... 34 total pairs
}

# Reverse mapping for lookup
IRREGULAR_SINGULARS = {v: k for k, v in IRREGULAR_PLURALS.items()}
```

**Lookup:** O(1) dictionary lookup

#### Strategy 2: Pattern-Based Rules

Apply regular English pluralization patterns:

**Pattern: -ies/-y**
```
family → families
category → categories
```
**Rule:** If word ends in consonant+y, change -y to -ies

**Pattern: -ves/-f(e)**
```
life → lives
knife → knives
shelf → shelves
```
**Rule:** If word ends in -f or -fe, change to -ves

**Pattern: -es**
```
watch → watches
box → boxes
```
**Rule:** Words ending in -s, -x, -ch, -sh, -z add -es

**Pattern: -s (regular)**
```
tag → tags
book → books
```
**Rule:** Default pluralization adds -s

**Implementation:**
```python
def normalize_plural_forms(tag: str) -> Set[str]:
    """Generate all possible singular/plural forms."""
    normalized = {tag}
    tag_lower = tag.lower()

    # Check irregular dictionary first
    if tag_lower in IRREGULAR_PLURALS:
        normalized.add(IRREGULAR_PLURALS[tag_lower])
    elif tag_lower in IRREGULAR_SINGULARS:
        normalized.add(IRREGULAR_SINGULARS[tag_lower])

    # Apply pattern rules
    if len(tag_lower) > 4:
        # -ies/-y pattern
        if tag_lower.endswith('ies'):
            normalized.add(tag[:-3] + 'y')
        elif tag_lower.endswith('y') and not tag_lower.endswith('ay'):
            normalized.add(tag[:-1] + 'ies')

        # -ves/-f(e) pattern
        if tag_lower.endswith('ves'):
            normalized.add(tag[:-3] + 'fe')
            normalized.add(tag[:-3] + 'f')
        elif tag_lower.endswith('f') or tag_lower.endswith('fe'):
            base = tag[:-2] if tag_lower.endswith('fe') else tag[:-1]
            normalized.add(base + 'ves')

        # -es pattern
        if tag_lower.endswith('es'):
            normalized.add(tag[:-2])

        # -s pattern (regular)
        if tag_lower.endswith('s') and not tag_lower.endswith('ss'):
            normalized.add(tag[:-1])
        else:
            normalized.add(tag + 's')

    return normalized
```

#### Strategy 3: Compound Word Handling

Handle plurals in hyphenated and nested tags:

**Hyphenated compounds:**
```python
def normalize_compound_plurals(tag: str) -> Set[str]:
    """Handle plurals in compound tags."""
    normalized = {tag}

    # Hyphenated: "tax-break" → "tax-breaks"
    if '-' in tag:
        parts = tag.split('-')
        last_part_forms = normalize_plural_forms(parts[-1])
        for form in last_part_forms:
            normalized.add('-'.join(parts[:-1] + [form]))

    # Nested: "child/development" → "children/development"
    if '/' in tag:
        parts = tag.split('/')
        for i, part in enumerate(parts):
            part_forms = normalize_plural_forms(part)
            for form in part_forms:
                new_parts = parts[:i] + [form] + parts[i+1:]
                normalized.add('/'.join(new_parts))

    return normalized
```

**Examples:**
- `tax-break` → `{tax-break, tax-breaks}`
- `self-help` → `{self-help, selves-help}` (irregular on first component)
- `child/development` → `{child/development, children/development}`

### Grouping and Preference

**Variant Grouping:**
```python
def find_plural_variants(tags: Iterable[str]) -> Dict[str, List[str]]:
    """Group tags by their normalized forms."""
    variant_groups = defaultdict(set)

    for tag in tags:
        forms = normalize_plural_forms(tag)
        forms.update(normalize_compound_plurals(tag))

        # Prefer plural form as canonical
        canonical = max(forms, key=lambda t: (
            t.lower().endswith('s') or t.lower() in IRREGULAR_PLURALS.values(),
            len(t),
            t.lower()
        ))
        variant_groups[canonical.lower()].add(tag)

    return {k: list(v) for k, v in variant_groups.items() if len(v) > 1}
```

**Preference Logic:**
1. Prefer plural forms (ends with 's' or in irregular plural values)
2. Prefer longer forms (plurals are usually longer)
3. Alphabetical tiebreaker

### Complexity Analysis

**Time Complexity:**
- Dictionary lookup: O(1)
- Pattern matching: O(m) where m = tag length
- Compound handling: O(m × k) where k = number of components
- **Per tag: O(m × k)** - linear in tag structure

**Space Complexity:**
- Irregular dictionary: O(1) - fixed 34 pairs
- Normalized forms set: O(k) - bounded by number of components
- **Overall: O(1)** per tag

---

## Synonym Detection

**Module:** `tagex/analysis/synonym_analyzer.py`

**Key Functions:**
- `find_synonyms_by_cooccurrence()` - tagex/analysis/synonym_analyzer.py:20
- `find_acronym_expansions()` - tagex/analysis/synonym_analyzer.py:111

**Purpose:** Detect tags with equivalent meanings using contextual co-occurrence patterns.

### Algorithm: Jaccard Similarity on Co-occurrence Sets

Tags that mean the same thing tend to appear with the same other tags. The synonym analyzer exploits this property.

#### Step 1: Build Co-occurrence Sets

For each tag, build a set of tags it appears with:

```python
def build_cooccurrence_sets(tag_stats: Dict) -> Dict[str, Set[str]]:
    """Build co-occurrence sets for each tag."""
    cooccurrence = {}

    for tag in tag_stats.keys():
        cooccurrence[tag] = set()
        for other_tag, stats in tag_stats.items():
            if other_tag != tag:
                shared_files = tag_stats[tag]['files'] & stats['files']
                if len(shared_files) >= 3:  # Minimum overlap threshold
                    cooccurrence[tag].add(other_tag)

    return cooccurrence
```

**Example:**
```
python appears with: {data, jupyter, pandas, visualization, numpy, scikit-learn, ml}
py appears with:     {data, jupyter, pandas, visualization, numpy, scikit-learn, ml}
music appears with:  {production, mixing, daw, recording, synthesis}
audio appears with:  {production, mixing, daw, recording, synthesis}
```

#### Step 2: Calculate Jaccard Similarity

Measure overlap between co-occurrence sets:

```
                  |A ∩ B|
J(A, B) = ─────────────────
           |A ∪ B|

Where:
  A ∩ B = intersection (tags both appear with)
  A ∪ B = union (tags either appears with)
```

**Example:**
```python
python_context = {data, jupyter, pandas, visualization, numpy, scikit-learn, ml}
py_context =     {data, jupyter, pandas, visualization, numpy, scikit-learn, ml}

intersection = {data, jupyter, pandas, visualization, numpy, scikit-learn, ml}  # 7 tags
union =        {data, jupyter, pandas, visualization, numpy, scikit-learn, ml}  # 7 tags

J(python, py) = 7/7 = 1.0  # Perfect synonym match!
```

**Another example:**
```python
music_context = {production, mixing, daw, recording, synthesis, guitar}        # 6 tags
audio_context = {production, mixing, daw, recording, synthesis, mastering}     # 6 tags

intersection = {production, mixing, daw, recording, synthesis}                 # 5 tags
union =        {production, mixing, daw, recording, synthesis, guitar, mastering}  # 7 tags

J(music, audio) = 5/7 = 0.71  # High similarity → likely synonyms
```

#### Step 3: Threshold Filtering

Tags with Jaccard similarity ≥ 0.70 are considered synonym candidates:

```
Similarity Scale:
1.0 ████████████████████ Perfect overlap (identical usage)
0.9 ██████████████████▒▒
0.8 ████████████████▒▒▒▒ Very high overlap
0.7 ██████████████▒▒▒▒▒▒ ← THRESHOLD (good synonym candidates)
0.6 ████████████▒▒▒▒▒▒▒▒
0.5 ██████████▒▒▒▒▒▒▒▒▒▒ Moderate overlap
0.4 ████████▒▒▒▒▒▒▒▒▒▒▒▒
```

**Why 0.70?**
- High enough to avoid false positives (unrelated tags)
- Low enough to catch abbreviations and variations
- Empirically validated on real vaults

#### Step 4: Transitive Grouping

Build synonym groups by transitive closure:

```python
def group_synonyms(synonym_pairs: List[Tuple[str, str, float]]) -> List[Set[str]]:
    """Group synonyms transitively."""
    # Build adjacency graph
    graph = defaultdict(set)
    for tag1, tag2, score in synonym_pairs:
        if score >= 0.70:
            graph[tag1].add(tag2)
            graph[tag2].add(tag1)

    # Find connected components via DFS
    visited = set()
    groups = []

    def dfs(tag, group):
        visited.add(tag)
        group.add(tag)
        for neighbor in graph[tag]:
            if neighbor not in visited:
                dfs(neighbor, group)

    for tag in graph:
        if tag not in visited:
            group = set()
            dfs(tag, group)
            groups.append(group)

    return groups
```

**Example:**
```
Pairs: (ai, ml, 0.78), (ml, machine-learning, 0.72)

Graph:
  ai ←→ ml ←→ machine-learning

Transitive closure:
  Group: {ai, ml, machine-learning}
```

### Acronym Detection

Special handling for acronyms via first-letter matching:

```python
def find_acronym_expansions(tags: Iterable[str]) -> List[Tuple[str, str]]:
    """Find acronym-expansion pairs."""
    matches = []

    for short_tag in tags:
        if len(short_tag) <= 3:  # Likely acronym
            for long_tag in tags:
                if len(long_tag) > len(short_tag):
                    # Check first-letter match
                    parts = long_tag.replace('-', ' ').replace('_', ' ').split()
                    acronym = ''.join(p[0].lower() for p in parts)

                    if acronym == short_tag.lower():
                        matches.append((short_tag, long_tag))

    return matches
```

**Examples:**
- `ai` ↔ `artificial-intelligence`
- `ml` ↔ `machine-learning`
- `nlp` ↔ `natural-language-processing`

### Complexity Analysis

**Time Complexity:**
- Build co-occurrence sets: O(n²) - compare all tag pairs
- Jaccard calculation: O(n² × k) where k = avg co-occurrence set size
- Transitive grouping: O(n + e) where e = number of synonym edges
- **Overall: O(n² × k)**

**Space Complexity:**
- Co-occurrence sets: O(n × k) - each tag has up to k co-occurring tags
- Graph for grouping: O(n + e)
- **Overall: O(n × k)**

**Practical Performance:**
- Fast for typical vaults (hundreds of tags)
- Dominated by co-occurrence set construction

---

## Overbroad Tag Detection

**Module:** `tagex/analysis/breadth_analyzer.py`

**Key Functions:**
- `calculate_specificity()` - tagex/analysis/breadth_analyzer.py:65
- `analyze_tag_quality()` - tagex/analysis/breadth_analyzer.py:137

**Purpose:** Identify tags that appear in too many files to be useful for organization.

### Algorithm: Composite Specificity Scoring

The quality analyzer combines multiple metrics into a single specificity score.

#### Metric 1: Coverage Ratio

What percentage of files contain this tag?

```
coverage_ratio = files_with_tag / total_files
```

**Thresholds:**
- High: 30%+ (appears in 30%+ of files)
- Very High: 50%+ (appears in half of files)
- Extreme: 70%+ (appears in most files)

**Rationale:** Tags appearing in >50% of files are too broad to distinguish content.

#### Metric 2: Information Content (Shannon Entropy)

How much information does this tag provide? (tagex/analysis/breadth_analyzer.py:89-91)

```
IC = -log₂(P(tag))
   = -log₂(files_with_tag / total_files)
```

**Interpretation:**
- Higher IC = rarer tag = more specific = more informative
- Lower IC = common tag = less specific = less informative

**Example:**
```
Tag "notes" appears in 892/1306 files (68.3%)
IC = -log₂(892/1306) = -log₂(0.683) = 0.55

Tag "python/pandas" appears in 12/1306 files (0.9%)
IC = -log₂(12/1306) = -log₂(0.009) = 6.79
```

**Range:**
- log₂(1306) ≈ 10.35 (maximum, tag appears once)
- 0 (minimum, tag appears in all files)

#### Metric 3: Structural Depth

Does the tag have hierarchical structure?

```python
def calculate_structural_depth(tag: str) -> int:
    """Calculate depth based on nesting and compounds."""
    depth = 0

    # Nested tags: work/meetings/standup
    if '/' in tag:
        depth += len(tag.split('/'))
    else:
        depth += 1

    # Compound tags: machine-learning
    if '-' in tag or '_' in tag:
        depth += 1

    return depth
```

**Examples:**
- `notes` → depth = 1 (flat)
- `machine-learning` → depth = 2 (compound)
- `work/meetings/standup` → depth = 3 (nested)

**Rationale:** More structured tags are more specific.

#### Metric 4: Generic Word Penalty

Is the tag itself a generic word?

```python
GENERIC_WORDS = {
    'notes', 'ideas', 'misc', 'general', 'stuff', 'things',
    'temp', 'draft', 'random', 'other', 'various'
}

generic_penalty = -5 if tag.lower() in GENERIC_WORDS else 0
```

**Rationale:** Generic words are inherently non-specific.

#### Metric 5: Co-occurrence Diversity

How many different tags does this tag appear with?

```python
def calculate_diversity_penalty(tag, tag_stats, all_tags) -> int:
    """Penalize tags that appear with too many other tags."""
    cooccurring_tags = set()

    for other_tag in all_tags:
        if other_tag != tag:
            shared = len(tag_stats[tag]['files'] & tag_stats[other_tag]['files'])
            if shared > 0:
                cooccurring_tags.add(other_tag)

    diversity_ratio = len(cooccurring_tags) / max(len(all_tags) - 1, 1)

    # Penalize if appears with >50% of all tags
    return -2 if diversity_ratio > 0.5 else 0
```

**Rationale:** Tags appearing with most other tags are used indiscriminately.

#### Composite Score

Combine all metrics:

```
Specificity Score = IC + Structural Depth + Generic Penalty + Diversity Penalty
```

**Assessment Ranges:**
- **Highly Specific:** ≥ 5.0
- **Appropriately Specific:** 3.0 - 5.0
- **Moderately Specific:** 1.0 - 3.0
- **Too Broad:** < 1.0

**Example Calculations:**

**Tag: "notes" (overbroad)**
```
IC = 0.55 (appears in 68% of files)
Structural Depth = 1 (flat tag)
Generic Penalty = -5 (generic word)
Diversity Penalty = -2 (appears with 78% of tags)
─────────────────────
Total Score = 0.55 + 1 - 5 - 2 = -5.45 (too_broad)
```

**Tag: "python/data-analysis/pandas" (highly specific)**
```
IC = 6.79 (appears in 0.9% of files)
Structural Depth = 3 (nested tag)
Generic Penalty = 0 (not generic)
Diversity Penalty = 0 (appears with <20% of tags)
─────────────────────
Total Score = 6.79 + 3 + 0 + 0 = 9.79 (highly_specific)
```

### Complexity Analysis

**Time Complexity:**
- Coverage calculation: O(1) per tag
- IC calculation: O(1) per tag
- Diversity calculation: O(n) per tag (check all other tags)
- **Overall: O(n²)** for full analysis

**Space Complexity:**
- Metrics storage: O(n) per tag
- **Overall: O(n)**

---

## Pair Analysis

**Module:** `tagex/analysis/pair_analyzer.py`

**Key Functions:**
- `analyze_tag_pairs()` - tagex/analysis/pair_analyzer.py:13
- `find_hub_tags()` - tagex/analysis/pair_analyzer.py:97
- `find_tag_clusters()` - tagex/analysis/pair_analyzer.py:135

**Purpose:** Detect tag co-occurrence patterns, identify hub tags, and find natural clusters.

### Algorithm: Combinatorial Pair Counting

#### Step 1: Build File-to-Tags Mapping

Create reverse index for efficient pair generation:

```python
def build_file_to_tags_map(tag_data: Dict) -> Dict[str, Set[str]]:
    """Create mapping: file_path → {tag1, tag2, ...}"""
    file_to_tags = defaultdict(set)

    for tag, metadata in tag_data.items():
        for file_path in metadata['files']:
            file_to_tags[file_path].add(tag)

    return file_to_tags
```

**Result:**
```
{
  'notes/project.md': {'work', 'ideas', 'draft'},
  'notes/meeting.md': {'work', 'notes', 'tasks'},
  'notes/brainstorm.md': {'work', 'ideas', 'notes'}
}
```

#### Step 2: Generate All Pairs

For each file, generate all unique tag pairs:

```python
from itertools import combinations

def calculate_pairs(file_to_tags: Dict) -> Counter:
    """Count co-occurrences for all tag pairs."""
    pairs = Counter()

    for file_path, tags in file_to_tags.items():
        # Generate all unique pairs
        for tag1, tag2 in combinations(sorted(tags), 2):
            pairs[(tag1, tag2)] += 1

    return pairs
```

**Mathematical basis:**
- For n tags in a file, there are C(n,2) = n(n-1)/2 unique pairs
- `combinations(tags, 2)` generates all unique pairs without duplicates

**Example:**
```
File with tags: {'work', 'ideas', 'draft'}
Pairs: (draft, ideas), (draft, work), (ideas, work)
```

#### Step 3: Hub Tag Identification

Count how many different tags each tag pairs with:

```python
def find_hub_tags(pairs: Counter) -> Dict[str, int]:
    """Identify tags that appear in many pairs."""
    hub_counts = Counter()

    for (tag1, tag2), count in pairs.items():
        hub_counts[tag1] += count
        hub_counts[tag2] += count

    return hub_counts.most_common()
```

**Hub score:** Sum of all pair counts involving this tag

**Example:**
```
Pairs:
  (work, ideas): 25
  (work, tasks): 20
  (work, draft): 15
  (ideas, notes): 12

Hub scores:
  work: 25+20+15 = 60 ← Central hub
  ideas: 25+12 = 37
  tasks: 20
  draft: 15
  notes: 12
```

#### Step 4: Cluster Detection

Find connected components in the tag graph:

```python
def find_tag_clusters(pairs: Counter, min_strength: int = 3) -> List[Set[str]]:
    """Find natural tag groupings using graph DFS."""
    # Build adjacency graph
    graph = defaultdict(set)
    for (tag1, tag2), count in pairs.items():
        if count >= min_strength:  # Strong connections only
            graph[tag1].add(tag2)
            graph[tag2].add(tag1)

    # Find connected components
    visited = set()
    clusters = []

    def dfs(tag, cluster):
        visited.add(tag)
        cluster.add(tag)
        for neighbor in graph[tag]:
            if neighbor not in visited:
                dfs(neighbor, cluster)

    for tag in graph:
        if tag not in visited:
            cluster = set()
            dfs(tag, cluster)
            if len(cluster) > 1:  # Ignore singleton clusters
                clusters.append(cluster)

    return sorted(clusters, key=len, reverse=True)
```

**Algorithm:** Depth-First Search (DFS) for connected components

**Example:**
```
Strong pairs (≥3 co-occurrences):
  work ←→ ideas (25)
  work ←→ tasks (20)
  work ←→ draft (15)
  ideas ←→ notes (12)

Graph:
        ideas ←→ notes
          ↕
        work
          ↕
        tasks
          ↕
        draft

Cluster found: {work, ideas, tasks, draft, notes}
```

### Complexity Analysis

**Time Complexity:**
- File-to-tags mapping: O(n × m) where n = tags, m = avg files per tag
- Pair generation: O(f × t²) where f = files, t = avg tags per file
- Hub calculation: O(p) where p = number of pairs
- Cluster detection: O(n + p) via DFS
- **Overall: O(f × t² + n × m)**

**Space Complexity:**
- File-to-tags map: O(f × t)
- Pairs counter: O(p) where p ≤ C(n,2) = n(n-1)/2
- Graph: O(n + p)
- **Overall: O(n² + f × t)** in worst case

**Practical Performance:**
- Fast for typical vaults
- Most expensive operation: pair generation from files

---

## Singleton Tag Analysis

**Module:** `tagex/analysis/singleton_analyzer.py`

**Key Functions:**
- `SingletonAnalyzer.analyze()` - tagex/analysis/singleton_analyzer.py:58
- `_calculate_string_similarity()` - tagex/analysis/singleton_analyzer.py:98
- `_find_semantic_matches()` - tagex/analysis/singleton_analyzer.py:120

**Purpose:** Identify singleton tags (used only once) and suggest merging them into established frequent tags.

### Algorithm: Dual-Strategy Singleton Reduction

The singleton analyzer specifically targets tags appearing only once and suggests one-directional merges into frequent tags (count ≥ threshold). This consolidates rare tags into established taxonomy.

#### Strategy 1: String Similarity (Typo Detection)

Uses SequenceMatcher for character-level similarity (tagex/analysis/singleton_analyzer.py:98):

```python
from difflib import SequenceMatcher

def _calculate_string_similarity(self, tag1: str, tag2: str) -> float:
    """Calculate string similarity ratio (0-1)."""
    return SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()
```

**Threshold:** 0.90 (very high similarity required)

**Catches:**
- Typos: `machne-learning` → `machine-learning`
- Minor variations: `python-programming` → `python-programing`
- Case differences: `Python` → `python`

#### Strategy 2: Semantic Similarity (True Synonyms)

Uses sentence-transformers for semantic matching (tagex/analysis/singleton_analyzer.py:120):

```python
from sentence_transformers import SentenceTransformer

def _find_semantic_matches(self, singleton_tag: str) -> List[Tuple[str, float]]:
    """Find semantically similar frequent tags using embeddings."""
    if self.semantic_model is None:
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

    singleton_embedding = self.semantic_model.encode([singleton_tag])
    frequent_embeddings = self.semantic_model.encode(list(self.frequent_tags.keys()))

    similarities = cosine_similarity(singleton_embedding, frequent_embeddings)[0]
    # ... threshold filtering
```

**Threshold:** 0.70 (semantic similarity)

**Catches:**
- Abbreviations: `ai` → `artificial-intelligence`
- Synonyms: `ml` → `machine-learning`
- Related concepts: `notes` → `writing`

#### Merge Direction

**Important:** Only singleton → frequent, never frequent → singleton

```
✓ Correct: "machne-learning" (1 use) → "machine-learning" (47 uses)
✗ Wrong:   "machine-learning" (47 uses) → "machne-learning" (1 use)
```

This prevents established taxonomy from being corrupted by typos.

### Why Not TF-IDF or Co-occurrence?

Earlier versions used TF-IDF and co-occurrence analysis for singletons, but these were removed (noted in tagex/analysis/singleton_analyzer.py:14):

> "Note: TF-IDF and co-occurrence methods were removed as they produced too many false positives."

**Reasons:**
- TF-IDF requires multiple occurrences for meaningful vectorization
- Co-occurrence needs shared context (impossible with single use)
- String + semantic similarity are more accurate for singletons

### Complexity Analysis

**Time Complexity:**
- String similarity: O(s × f × m) where s = singletons, f = frequent tags, m = avg tag length
- Semantic similarity: O(s × f) with embedding cache
- **Overall: O(s × f × m)** for string matching

**Space Complexity:**
- Embeddings: O((s + f) × d) where d = embedding dimensions (384 for MiniLM)
- **Overall: O((s + f) × d)**

---

## Content-Based Tag Suggestions

**Module:** `tagex/analysis/content_analyzer.py`

**Key Functions:**
- `ContentAnalyzer.analyze()` - tagex/analysis/content_analyzer.py:83
- `_extract_note_content()` - tagex/analysis/content_analyzer.py:200
- `_suggest_tags_for_note()` - tagex/analysis/content_analyzer.py:232

**Command:** `tagex analyze suggest`

**Purpose:** Suggest relevant tags for untagged or lightly-tagged notes based on semantic content analysis.

### Algorithm: Content-to-Tag Semantic Matching

The content analyzer reads note content and matches it against established tags using sentence embeddings.

#### Step 1: Filter Candidate Notes

Identify notes needing tag suggestions (tagex/analysis/content_analyzer.py:83):

```python
def analyze(self) -> List[Dict[str, Any]]:
    """Find notes with few tags and suggest additions."""
    candidate_files = []

    for file_path in find_markdown_files(str(self.vault_path)):
        # Extract existing tags
        existing_tags = self._extract_existing_tags(file_path)

        # Filter by tag count
        if self.min_tag_count <= len(existing_tags) <= (self.max_tag_count or float('inf')):
            candidate_files.append((file_path, existing_tags))
```

**Criteria:**
- Notes with 0-2 tags (configurable with `--min-tags`)
- Excludes already well-tagged notes
- Only suggests from frequent tags (≥2 uses by default)

#### Step 2: Extract Note Content

Read and clean note text (tagex/analysis/content_analyzer.py:200):

```python
def _extract_note_content(self, file_path: Path) -> str:
    """Extract meaningful content from note."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Remove code blocks
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

    # Remove links and formatting
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    content = re.sub(r'[#*_`]', '', content)

    return content.strip()
```

**Cleaning steps:**
- Remove YAML frontmatter
- Remove code blocks
- Remove markdown formatting
- Remove links (keep text)

#### Step 3: Encode Content and Tags

Use sentence-transformers for semantic embeddings (tagex/analysis/content_analyzer.py:232):

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Encode note content
content_embedding = model.encode([note_content])

# Encode all candidate tags
tag_embeddings = model.encode(list(self.candidate_tags.keys()))

# Calculate similarity
similarities = cosine_similarity(content_embedding, tag_embeddings)[0]
```

**Model:** `all-MiniLM-L6-v2` (384 dimensions, fast inference)

#### Step 4: Rank and Filter Suggestions

Return top matching tags above threshold:

```python
# Rank tags by similarity
tag_scores = list(zip(self.candidate_tags.keys(), similarities))
tag_scores.sort(key=lambda x: x[1], reverse=True)

# Filter by threshold and limit
suggestions = [
    (tag, float(score))
    for tag, score in tag_scores[:max_suggestions]
    if score >= similarity_threshold
]
```

**Default threshold:** 0.3 (lower than synonym/singleton because content matching is harder)

**Default max_suggestions:** 5 tags per note

### Example

**Note content:**
```markdown
# Machine Learning Project

Working on a classification model using scikit-learn.
Need to tune hyperparameters for better accuracy.
```

**Existing tags:** (none)

**Suggested tags:**
- `machine-learning` (similarity: 0.78)
- `python` (similarity: 0.65)
- `data-science` (similarity: 0.58)
- `scikit-learn` (similarity: 0.54)
- `classification` (similarity: 0.47)

### Exclusions

The analyzer respects exclusion config (tagex/analysis/content_analyzer.py:54):

```python
# Load exclusions config
self.exclusions = ExclusionsConfig(vault_path)

# Filter to frequent tags only, excluding auto-generated tags
self.candidate_tags = {
    tag: stats for tag, stats in tag_stats.items()
    if stats['count'] >= min_tag_frequency
    and not self.exclusions.is_suggestion_excluded(tag)
}
```

**Excludes:**
- Date tags (`2024`, `2024-01-15`)
- Auto-generated tags from plugins
- Tags in `.tagex/exclusions.yaml`

### Complexity Analysis

**Time Complexity:**
- Note extraction: O(n × c) where n = notes, c = avg content length
- Embedding: O(n × c) for content + O(t) for tags (cached)
- Similarity: O(n × t) where t = candidate tags
- **Overall: O(n × (c + t))**

**Space Complexity:**
- Content embeddings: O(n × d) where d = 384
- Tag embeddings: O(t × d) - computed once
- **Overall: O((n + t) × d)**

**Practical Performance:**
- 100 notes: ~15s (includes model load)
- 1,000 notes: ~60s
- Model cache speeds up repeated runs

---

## Performance Characteristics

### Scalability Summary

| Algorithm | Time Complexity | Space Complexity | Bottleneck |
|:----------|:---------------|:-----------------|:-----------|
| Semantic Similarity | O(n²) | O(n²) | Similarity matrix calculation |
| Plural Detection | O(n × m) | O(1) per tag | Pattern matching |
| Synonym Detection | O(n² × k) | O(n × k) | Co-occurrence comparison |
| Overbroad Detection | O(n²) | O(n) | Diversity calculation |
| Pair Analysis | O(f × t² + n×m) | O(n² + f×t) | Pair generation |
| Singleton Analysis | O(s × f × m) | O((s+f) × d) | String similarity or embeddings |
| Content Suggestions | O(n × (c + t)) | O((n+t) × d) | Content embedding |

**Legend:**
- n = number of tags
- m = average tag length
- f = number of files
- t = average tags per file (or total tags for content analysis)
- k = average co-occurrence set size
- s = number of singleton tags
- c = average note content length
- d = embedding dimensions (384 for all-MiniLM-L6-v2)

### Real-World Performance

**Test vault: 1,306 files, 831 tags**

| Analysis | Time | Memory | Output |
|:---------|:-----|:-------|:-------|
| Extract | 2.3s | 45MB | JSON file |
| Stats | 0.8s | 12MB | Text report |
| Pairs | 1.2s | 18MB | 150 pair relationships |
| Merge | 8.4s | 92MB | 23 merge suggestions |
| Quality | 1.5s | 15MB | 12 overbroad tags |
| Synonyms | 2.1s | 24MB | 8 synonym groups |
| Plurals | 0.4s | 8MB | 15 variant groups |
| Singletons | 3.2s | 78MB | 45 singleton merges (with embeddings) |
| Suggest | 12.5s | 125MB | 150 content-based suggestions (100 notes) |

**Observations:**
- Content suggestion is slowest (sentence-transformers model + note content)
- Merge analysis is second slowest (TF-IDF + similarity matrix)
- Plural analysis is fastest (simple pattern matching)
- Memory usage dominated by similarity matrices and embeddings
- Singleton and content analysis require sentence-transformers (~400MB model)

### Optimization Strategies

**For large vaults (10,000+ tags):**

1. **Sparse matrix representation** for TF-IDF (already implemented)
2. **Sampling:** Analyze subset of most-used tags first
3. **Incremental analysis:** Cache previous results, only analyze new tags
4. **Parallel processing:** Vectorize similarity calculations
5. **Threshold pre-filtering:** Skip unlikely pairs before similarity calc

**Code example (sampling):**
```python
# Only analyze tags with ≥10 uses
filtered_tags = {t: s for t, s in tag_stats.items() if s['count'] >= 10}
```

---

## References

### Academic Papers

- **TF-IDF:** Salton, G., & Buckley, C. (1988). "Term-weighting approaches in automatic text retrieval"
- **Cosine Similarity:** Singhal, A. (2001). "Modern Information Retrieval: A Brief Overview"
- **Jaccard Index:** Jaccard, P. (1912). "The distribution of the flora in the alpine zone"
- **Shannon Entropy:** Shannon, C. E. (1948). "A Mathematical Theory of Communication"

### Technical References

- **scikit-learn TfidfVectorizer:** https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- **scikit-learn Cosine Similarity:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html
- **sentence-transformers:** https://www.sbert.net/
- **all-MiniLM-L6-v2 Model:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **Character N-grams:** https://en.wikipedia.org/wiki/N-gram
- **Graph Connected Components:** https://en.wikipedia.org/wiki/Component_(graph_theory)
- **Python difflib.SequenceMatcher:** https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher

### Linguistic Resources

- **English Pluralization:** https://en.wikipedia.org/wiki/English_plurals
- **Morphological Analysis:** https://en.wikipedia.org/wiki/Morphology_(linguistics)
- **Information Theory:** https://en.wikipedia.org/wiki/Information_content

### Implementation Libraries

- **NumPy:** https://numpy.org/doc/stable/
- **scikit-learn:** https://scikit-learn.org/stable/
- **sentence-transformers:** https://www.sbert.net/
- **PyTorch** (required by sentence-transformers): https://pytorch.org/
- **Python itertools:** https://docs.python.org/3/library/itertools.html
- **Python collections.Counter:** https://docs.python.org/3/library/collections.html#collections.Counter
- **Python difflib:** https://docs.python.org/3/library/difflib.html

---

**Document Version:** 2.0
**Last Updated:** 2025-10-30
**Related Documentation:** [ANALYTICS.md](ANALYTICS.md)
