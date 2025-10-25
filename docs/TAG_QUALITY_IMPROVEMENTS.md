# Tag Quality Improvements - Implementation Plan

**Status:** Planning
**Created:** 2025-10-25
**Target Features:** Singular/plural normalization, synonym detection, overbroad tag analysis

---

## Overview

This document outlines planned enhancements to tagex's tag quality analysis capabilities. While the current system handles basic morphological variants and semantic similarity, there are three major categories of tag quality issues that need better detection and remediation:

1. **Singular/Plural Normalization** - Enhanced detection of count variants
2. **Synonym Detection** - Identifying conceptually equivalent tags with different names
3. **Overbroad Tag Analysis** - Detecting tags that are too generic to be useful

## Current State

### What We Have

**Existing capabilities in `tagex/analysis/merge_analyzer.py`:**

- ✅ Basic plural detection (simple `-s` suffix removal)
- ✅ Morphological variants (`-ing`, `-ed`, `-er`, `-tion`, `-ly`)
- ✅ TF-IDF character n-gram embeddings for semantic similarity
- ✅ High file overlap detection (80%+ co-occurrence)
- ✅ String similarity matching (85%+ threshold)

### What We're Missing

**Gaps in current implementation:**

- ❌ Irregular plurals (child/children, person/people)
- ❌ Complex plural forms (-ies/-y, -ves/-f, -es)
- ❌ Synonym detection beyond character similarity
- ❌ Overbroad tag detection (tags used too generally)
- ❌ Tag specificity scoring
- ❌ User-defined synonym mappings
- ❌ Interactive synonym learning

---

## Feature 1: Enhanced Singular/Plural Detection

### Problem Statement

Current implementation only handles simple `-s` suffix removal. This misses:

```
child → children         (irregular)
family → families        (-ies/-y pattern)
life → lives             (-ves/-f pattern)
watch → watches          (-es pattern)
tax-break → tax-breaks   (compound words)
```

### Proposed Solution

#### A. Irregular Plural Dictionary

```python
# tagex/utils/plural_normalizer.py

IRREGULAR_PLURALS = {
    'child': 'children',
    'person': 'people',
    'man': 'men',
    'woman': 'women',
    'tooth': 'teeth',
    'foot': 'feet',
    'mouse': 'mice',
    'goose': 'geese',
    'life': 'lives',
    'knife': 'knives',
    'leaf': 'leaves',
    'self': 'selves',
    'elf': 'elves',
    'half': 'halves',
    'ox': 'oxen',
    'crisis': 'crises',
    'analysis': 'analyses',
    'thesis': 'theses',
    'phenomenon': 'phenomena',
    'criterion': 'criteria',
}

# Build reverse mapping
IRREGULAR_SINGULARS = {v: k for k, v in IRREGULAR_PLURALS.items()}
```

#### B. Pattern-Based Normalization

```python
def normalize_plural_forms(tag: str) -> Set[str]:
    """Generate all possible singular/plural forms of a tag.

    Returns:
        Set of normalized forms (both singular and plural)
    """
    normalized = {tag}
    tag_lower = tag.lower()

    # Check irregular forms first
    if tag_lower in IRREGULAR_PLURALS:
        normalized.add(IRREGULAR_PLURALS[tag_lower])
    elif tag_lower in IRREGULAR_SINGULARS:
        normalized.add(IRREGULAR_SINGULARS[tag_lower])

    # Pattern-based detection
    if len(tag_lower) > 4:
        # -ies/-y pattern (families → family)
        if tag_lower.endswith('ies'):
            normalized.add(tag[:-3] + 'y')
        elif tag_lower.endswith('y') and not tag_lower.endswith('ay'):
            normalized.add(tag[:-1] + 'ies')

        # -ves/-f pattern (lives → life)
        if tag_lower.endswith('ves'):
            normalized.add(tag[:-3] + 'fe')
            normalized.add(tag[:-3] + 'f')
        elif tag_lower.endswith('f') or tag_lower.endswith('fe'):
            base = tag[:-2] if tag_lower.endswith('fe') else tag[:-1]
            normalized.add(base + 'ves')

        # -es pattern (watches → watch)
        if tag_lower.endswith('es'):
            normalized.add(tag[:-2])

        # -s pattern (simple plural)
        if tag_lower.endswith('s') and not tag_lower.endswith('ss'):
            normalized.add(tag[:-1])
        else:
            normalized.add(tag + 's')

    return normalized
```

#### C. Compound Word Handling

```python
def normalize_compound_plurals(tag: str) -> Set[str]:
    """Handle plurals in compound/nested tags.

    Examples:
        tax-break → tax-breaks
        child/development → children/development
    """
    normalized = {tag}

    # Handle hyphenated compounds
    if '-' in tag:
        parts = tag.split('-')
        last_part_forms = normalize_plural_forms(parts[-1])
        for form in last_part_forms:
            normalized.add('-'.join(parts[:-1] + [form]))

    # Handle nested tags
    if '/' in tag:
        parts = tag.split('/')
        # Try pluralizing each component
        for i, part in enumerate(parts):
            part_forms = normalize_plural_forms(part)
            for form in part_forms:
                new_parts = parts[:i] + [form] + parts[i+1:]
                normalized.add('/'.join(new_parts))

    return normalized
```

#### D. Integration with Merge Analyzer

```python
# Update find_variant_patterns() in merge_analyzer.py

def find_plural_variants(tags: Iterable[str]) -> Dict[str, List[str]]:
    """Find singular/plural variants using enhanced detection."""
    from tagex.utils.plural_normalizer import normalize_plural_forms, normalize_compound_plurals

    variant_groups = defaultdict(set)

    for tag in tags:
        # Get all normalized forms
        forms = normalize_plural_forms(tag)
        forms.update(normalize_compound_plurals(tag))

        # Use alphabetically first form as canonical key
        canonical = sorted(forms)[0].lower()
        variant_groups[canonical].add(tag)

    # Return only groups with multiple variants
    return {k: list(v) for k, v in variant_groups.items() if len(v) > 1}
```

### Command Interface

```bash
# Detect all singular/plural variants
tagex analyze plurals /vault

Output:
  Plural Variant Groups:
    family (45 uses) / families (3 uses) → Suggest: merge into 'family'
    child (12 uses) / children (8 uses) → Suggest: merge into 'children'
    tax-break (5 uses) / tax-breaks (2 uses) → Suggest: merge into 'tax-break'

# Auto-merge with most common form
tagex normalize plurals /vault --dry-run
tagex normalize plurals /vault --apply
```

---

## Feature 2: Synonym Detection

### Problem Statement

Tags that mean the same thing but use different words create fragmentation:

```
tech (89 uses) ~ technology (5 uses)
music (45 uses) ~ audio (12 uses)
ai (34 uses) ~ artificial-intelligence (3 uses) ~ ml (8 uses)
```

Current TF-IDF embeddings catch some cases, but we need:
- User-defined synonym mappings
- Domain-specific synonym detection
- Interactive synonym learning
- Co-occurrence based synonym detection

### Proposed Solution

#### A. User-Defined Synonym Files

```yaml
# .tagex-synonyms.yaml (in vault root)

# Each group represents equivalent tags
# First tag in each group becomes the canonical form

synonyms:
  - [neuro, neurodivergent, neurodivergence, neurotype]
  - [adhd, add, attention-deficit]
  - [tech, technology, technical]
  - [ai, artificial-intelligence, ml, machine-learning]
  - [music, audio, sound]
  - [writing, blog, article, post]

# Hierarchical equivalence (all map to first)
prefer:
  python: [py, python3]
  javascript: [js, ecmascript]
```

#### B. Synonym File Parser

```python
# tagex/config/synonym_config.py

import yaml
from pathlib import Path
from typing import Dict, List, Set

class SynonymConfig:
    """Manage user-defined synonym mappings."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.config_file = vault_path / '.tagex-synonyms.yaml'
        self.synonym_groups: List[List[str]] = []
        self.canonical_map: Dict[str, str] = {}  # tag → canonical form

        if self.config_file.exists():
            self.load()

    def load(self) -> None:
        """Load synonym configuration from YAML."""
        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        # Process synonym groups
        if 'synonyms' in config:
            for group in config['synonyms']:
                if len(group) > 1:
                    canonical = group[0]
                    self.synonym_groups.append(group)
                    for tag in group:
                        self.canonical_map[tag] = canonical

        # Process prefer mappings
        if 'prefer' in config:
            for canonical, variants in config['prefer'].items():
                group = [canonical] + variants
                self.synonym_groups.append(group)
                for tag in group:
                    self.canonical_map[tag] = canonical

    def get_canonical(self, tag: str) -> str:
        """Get canonical form of a tag."""
        return self.canonical_map.get(tag, tag)

    def get_synonyms(self, tag: str) -> Set[str]:
        """Get all synonyms for a tag."""
        canonical = self.get_canonical(tag)
        for group in self.synonym_groups:
            if canonical in group:
                return set(group) - {tag}
        return set()

    def add_synonym_group(self, tags: List[str]) -> None:
        """Add a new synonym group and save."""
        if len(tags) > 1:
            canonical = tags[0]
            self.synonym_groups.append(tags)
            for tag in tags:
                self.canonical_map[tag] = canonical
            self.save()

    def save(self) -> None:
        """Save synonym configuration to YAML."""
        config = {'synonyms': self.synonym_groups}
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

#### C. Co-occurrence Based Synonym Detection

```python
# tagex/analysis/synonym_analyzer.py

def detect_synonyms_by_context(tag_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect potential synonyms based on shared context.

    Tags that appear with similar sets of other tags are likely synonyms.
    Uses Jaccard similarity on co-occurring tags.
    """
    synonym_candidates = []
    tags = list(tag_stats.keys())

    # Build co-occurrence sets for each tag
    cooccurrence = {}
    for tag in tags:
        # Find all other tags that appear in same files
        cooccurrence[tag] = set()
        for other_tag, stats in tag_stats.items():
            if other_tag != tag:
                shared_files = tag_stats[tag]['files'] & stats['files']
                if len(shared_files) >= 3:  # Minimum overlap
                    cooccurrence[tag].add(other_tag)

    # Compare co-occurrence sets
    for i, tag1 in enumerate(tags):
        for tag2 in tags[i+1:]:
            if not cooccurrence[tag1] or not cooccurrence[tag2]:
                continue

            # Jaccard similarity
            intersection = len(cooccurrence[tag1] & cooccurrence[tag2])
            union = len(cooccurrence[tag1] | cooccurrence[tag2])
            similarity = intersection / union if union > 0 else 0

            # High context similarity suggests synonymy
            if similarity >= 0.7:
                synonym_candidates.append({
                    'tag1': tag1,
                    'tag2': tag2,
                    'context_similarity': similarity,
                    'shared_context': intersection,
                    'suggestion': f"merge {tag2} → {tag1}" if tag_stats[tag1]['count'] > tag_stats[tag2]['count'] else f"merge {tag1} → {tag2}"
                })

    return sorted(synonym_candidates, key=lambda x: x['context_similarity'], reverse=True)
```

#### D. Interactive Synonym Learning

```python
# tagex/commands/learn_synonyms.py

def interactive_synonym_learning(vault_path: Path, tag_data_file: str) -> None:
    """Interactively review and confirm synonym relationships."""

    from tagex.config.synonym_config import SynonymConfig
    from tagex.analysis.synonym_analyzer import detect_synonyms_by_context

    config = SynonymConfig(vault_path)
    tag_data = load_tag_data(tag_data_file)
    tag_stats = build_tag_stats(tag_data)

    # Get candidates from multiple sources
    embedding_candidates = find_semantic_duplicates_embedding(tag_stats)
    context_candidates = detect_synonyms_by_context(tag_stats)

    print("=== Interactive Synonym Learning ===\n")

    new_groups = []

    # Review embedding-based candidates
    for candidate in embedding_candidates[:20]:  # Top 20
        tags = candidate['tags']
        print(f"\nCandidate synonym group:")
        for tag in tags:
            print(f"  - {tag} ({tag_stats[tag]['count']} uses)")

        response = input("Are these synonyms? [y/n/skip]: ").strip().lower()

        if response == 'y':
            new_groups.append(tags)
            print(f"  ✓ Added to synonym config")
        elif response == 'n':
            print(f"  ✗ Skipped")
        else:
            print(f"  → Skipped")

    # Save all new synonym groups
    if new_groups:
        for group in new_groups:
            config.add_synonym_group(group)
        print(f"\n✓ Saved {len(new_groups)} synonym groups to {config.config_file}")
    else:
        print("\nNo new synonyms added.")
```

### Command Interface

```bash
# Analyze potential synonyms
tagex analyze synonyms /vault

Output:
  Synonym Candidates (by semantic similarity):
    tech (89) ~ technology (5) [score: 0.72]
    music (45) ~ audio (12) [score: 0.65]

  Synonym Candidates (by context):
    python (67) ~ py (23) [context similarity: 0.85]
    ai (34) ~ ml (8) [context similarity: 0.78]

# Interactive learning session
tagex learn synonyms /vault tags.json

# Apply configured synonyms
tagex apply synonyms /vault --dry-run
tagex apply synonyms /vault --apply
```

---

## Feature 3: Overbroad Tag Detection

### Problem Statement

Some tags are used so broadly they lose meaning:

```
notes (892 files, 68% coverage) - what kind of notes?
ideas (654 files, 50% coverage) - ideas about what?
misc (234 files, 18% coverage) - catchall tag
work (432 files, 33% coverage) - too general
```

Overbroad tags create noise and reduce the value of the tagging system.

### Proposed Solution

#### A. Usage Pattern Analysis

```python
# tagex/analysis/breadth_analyzer.py

def detect_overbroad_tags(
    tag_stats: Dict[str, Dict[str, Any]],
    total_files: int,
    thresholds: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    """Detect tags that appear in too many files to be meaningful.

    Args:
        tag_stats: Tag usage statistics
        total_files: Total number of files in vault
        thresholds: Configuration for detection thresholds

    Returns:
        List of overbroad tags with analysis
    """
    if thresholds is None:
        thresholds = {
            'high_coverage': 0.30,      # Appears in >30% of files
            'very_high_coverage': 0.50, # Appears in >50% of files
            'extreme_coverage': 0.70    # Appears in >70% of files
        }

    overbroad = []

    for tag, stats in tag_stats.items():
        usage_ratio = len(stats['files']) / total_files

        severity = None
        if usage_ratio >= thresholds['extreme_coverage']:
            severity = 'extreme'
        elif usage_ratio >= thresholds['very_high_coverage']:
            severity = 'very_high'
        elif usage_ratio >= thresholds['high_coverage']:
            severity = 'high'

        if severity:
            overbroad.append({
                'tag': tag,
                'severity': severity,
                'file_count': len(stats['files']),
                'file_ratio': usage_ratio,
                'total_files': total_files,
            })

    return sorted(overbroad, key=lambda x: x['file_ratio'], reverse=True)
```

#### B. Specificity Scoring

```python
def calculate_tag_specificity(tag: str, tag_stats: Dict[str, Dict[str, Any]], total_files: int) -> Dict[str, Any]:
    """Calculate specificity score for a tag.

    Uses multiple metrics:
    - Information content (inverse probability)
    - Structural depth (nested tags are more specific)
    - Generic word detection
    - Co-occurrence diversity
    """

    # 1. Information Content
    p_tag = len(tag_stats[tag]['files']) / total_files
    ic_score = -math.log2(p_tag) if p_tag > 0 else 0

    # 2. Structural depth
    depth = len(tag.split('/'))
    has_compound = '-' in tag or '_' in tag
    structure_score = depth + (1 if has_compound else 0)

    # 3. Generic word penalty
    generic_words = {
        'notes', 'ideas', 'misc', 'general', 'stuff', 'things',
        'temp', 'draft', 'random', 'other', 'various'
    }
    is_generic = tag.lower() in generic_words
    generic_penalty = -5 if is_generic else 0

    # 4. Co-occurrence diversity (how many different tags does it appear with?)
    cooccurring_tags = set()
    for other_tag, stats in tag_stats.items():
        if other_tag != tag:
            if len(tag_stats[tag]['files'] & stats['files']) > 0:
                cooccurring_tags.add(other_tag)

    # High diversity might indicate overuse
    diversity_ratio = len(cooccurring_tags) / max(len(tag_stats) - 1, 1)
    diversity_penalty = -2 if diversity_ratio > 0.5 else 0

    # Combined specificity score
    total_score = ic_score + structure_score + generic_penalty + diversity_penalty

    return {
        'tag': tag,
        'specificity_score': total_score,
        'ic_score': ic_score,
        'structure_score': structure_score,
        'is_generic': is_generic,
        'cooccurrence_diversity': diversity_ratio,
        'assessment': _assess_specificity(total_score)
    }

def _assess_specificity(score: float) -> str:
    """Assess specificity level."""
    if score >= 5.0:
        return 'highly_specific'
    elif score >= 3.0:
        return 'appropriately_specific'
    elif score >= 1.0:
        return 'moderately_specific'
    else:
        return 'too_broad'
```

#### C. Refinement Suggestions

```python
def suggest_tag_refinements(
    tag: str,
    tag_stats: Dict[str, Dict[str, Any]],
    all_tags: Set[str]
) -> List[str]:
    """Suggest more specific alternatives to an overbroad tag.

    Analyzes what other tags commonly appear with this tag to suggest
    natural breakdowns.
    """
    suggestions = []

    # Find frequently co-occurring tags
    cooccurrence = Counter()
    for other_tag in all_tags:
        if other_tag != tag and not other_tag.startswith(tag + '/'):
            shared = len(tag_stats[tag]['files'] & tag_stats[other_tag]['files'])
            if shared >= 5:
                cooccurrence[other_tag] = shared

    # Suggest hierarchical breakdowns
    top_cooccurring = [t for t, _ in cooccurrence.most_common(10)]

    if top_cooccurring:
        suggestions.append(f"Consider breaking down '{tag}' into:")
        for related_tag in top_cooccurring[:5]:
            suggestions.append(f"  - {tag}/{related_tag}")

    # Check if nested versions already exist
    existing_nested = [t for t in all_tags if t.startswith(tag + '/')]
    if existing_nested:
        suggestions.append(f"\nExisting specific tags (consider using these instead):")
        for nested in existing_nested[:5]:
            suggestions.append(f"  - {nested}")

    return suggestions
```

#### D. Quality Report Generation

```python
def generate_tag_quality_report(
    vault_path: Path,
    tag_data_file: str,
    output_format: str = 'text'
) -> None:
    """Generate comprehensive tag quality analysis report."""

    tag_data = load_tag_data(tag_data_file)
    tag_stats = build_tag_stats(tag_data)
    total_files = len(set(f for stats in tag_stats.values() for f in stats['files']))

    # Analyze all aspects
    overbroad = detect_overbroad_tags(tag_stats, total_files)
    specificity_scores = {
        tag: calculate_tag_specificity(tag, tag_stats, total_files)
        for tag in tag_stats.keys()
    }

    if output_format == 'text':
        print("=== TAG QUALITY REPORT ===\n")

        # Overbroad tags
        if overbroad:
            print("OVERBROAD TAGS (used too generally):\n")
            for item in overbroad[:10]:
                print(f"  {item['tag']}")
                print(f"    Coverage: {item['file_ratio']:.1%} ({item['file_count']}/{item['total_files']} files)")
                print(f"    Severity: {item['severity']}")

                # Get refinement suggestions
                suggestions = suggest_tag_refinements(item['tag'], tag_stats, set(tag_stats.keys()))
                if suggestions:
                    for suggestion in suggestions[:3]:
                        print(f"    {suggestion}")
                print()

        # Specificity analysis
        print("\nSPECIFICITY ANALYSIS:\n")

        # Group by assessment
        by_assessment = defaultdict(list)
        for tag, score_data in specificity_scores.items():
            by_assessment[score_data['assessment']].append((tag, score_data))

        for assessment in ['too_broad', 'moderately_specific', 'appropriately_specific', 'highly_specific']:
            if assessment in by_assessment:
                print(f"\n{assessment.replace('_', ' ').title()}:")
                for tag, data in sorted(by_assessment[assessment], key=lambda x: x[1]['specificity_score'])[:5]:
                    print(f"  {tag} [score: {data['specificity_score']:.2f}]")

    elif output_format == 'json':
        report = {
            'overbroad_tags': overbroad,
            'specificity_scores': specificity_scores,
            'summary': {
                'total_tags': len(tag_stats),
                'overbroad_count': len(overbroad),
                'too_broad_count': len(by_assessment['too_broad'])
            }
        }
        print(json.dumps(report, indent=2))
```

### Command Interface

```bash
# Analyze tag breadth/specificity
tagex analyze quality /vault

Output:
  Tag Quality Analysis
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  OVERBROAD TAGS:
    notes (892 files, 68% coverage) - EXTREME
      Consider breaking down into:
        - notes/meeting
        - notes/research
        - notes/personal

    ideas (654 files, 50% coverage) - VERY HIGH
      Existing specific tags (use these instead):
        - ideas/project
        - ideas/writing

    misc (234 files, 18% coverage) - HIGH
      Recommendation: Eliminate this tag, use specific categories

  SPECIFICITY SCORES:
    Too Broad:
      misc [score: -2.3]
      notes [score: 0.2]
      ideas [score: 0.8]

    Appropriately Specific:
      python/data-analysis [score: 4.2]
      neuroscience/memory [score: 3.8]

    Highly Specific:
      neuroscience/memory/working-memory [score: 6.1]
      python/data-analysis/pandas [score: 5.7]

# Generate detailed report
tagex analyze quality /vault --output report.json --format json

# Suggest refinements for specific tag
tagex suggest-refinements /vault --tag "notes"
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Files to create:**
- `tagex/utils/plural_normalizer.py` - Plural detection logic
- `tagex/config/synonym_config.py` - Synonym configuration management
- `tagex/analysis/synonym_analyzer.py` - Synonym detection algorithms
- `tagex/analysis/breadth_analyzer.py` - Overbroad tag detection

**Tests to create:**
- `tests/test_plural_normalizer.py`
- `tests/test_synonym_config.py`
- `tests/test_synonym_analyzer.py`
- `tests/test_breadth_analyzer.py`

### Phase 2: Integration (Week 3)

**Updates needed:**
- `tagex/analysis/merge_analyzer.py` - Integrate plural normalizer
- `tagex/main.py` - Add new commands

**New commands:**
```python
# Add to main.py CLI

@app.command()
def analyze_quality(vault: Path, ...):
    """Analyze tag quality (plurals, synonyms, overbroad tags)."""
    ...

@app.command()
def learn_synonyms(vault: Path, tag_data: str, ...):
    """Interactive synonym learning session."""
    ...

@app.command()
def normalize_plurals(vault: Path, ...):
    """Normalize singular/plural variants."""
    ...

@app.command()
def apply_synonyms(vault: Path, ...):
    """Apply synonym mappings from config."""
    ...
```

### Phase 3: Documentation (Week 4)

**Documentation to update:**
- `docs/ANALYTICS.md` - Add sections for each new analysis type
- `README.md` - Update command reference
- `CLAUDE.md` - Update development commands

**New documentation:**
- `docs/TAG_QUALITY.md` - Comprehensive guide to quality analysis

### Phase 4: Testing & Refinement (Week 5)

- Comprehensive test suite
- Real-world vault testing
- Performance optimization
- Edge case handling

---

## Priority Recommendations

### High Priority (Implement First)

1. **Overbroad Tag Detection** - Most novel, addresses real pain point
2. **Enhanced Plural Detection** - Quick win, extends existing functionality
3. **Quality Report Command** - Integrates all analyses into actionable output

### Medium Priority

4. **User-Defined Synonyms** - High value for power users
5. **Co-occurrence Synonym Detection** - Complements existing semantic analysis

### Low Priority (Nice to Have)

6. **Interactive Learning** - Great UX but requires more polish
7. **Refinement Suggestions** - Helpful but requires good heuristics

---

## Testing Strategy

### Unit Tests

```python
# tests/test_plural_normalizer.py

def test_irregular_plurals():
    assert normalize_plural_forms('child') == {'child', 'children'}
    assert normalize_plural_forms('person') == {'person', 'people'}

def test_pattern_plurals():
    assert normalize_plural_forms('family') == {'family', 'families'}
    assert normalize_plural_forms('life') == {'life', 'lives'}

def test_compound_plurals():
    assert 'tax-breaks' in normalize_compound_plurals('tax-break')
    assert 'children/development' in normalize_compound_plurals('child/development')
```

```python
# tests/test_breadth_analyzer.py

def test_overbroad_detection():
    tag_stats = {
        'notes': {'files': set(range(700)), 'count': 700},  # 70% coverage
        'specific': {'files': set(range(10)), 'count': 10}   # 1% coverage
    }
    total_files = 1000

    overbroad = detect_overbroad_tags(tag_stats, total_files)
    assert len(overbroad) == 1
    assert overbroad[0]['tag'] == 'notes'
    assert overbroad[0]['severity'] == 'extreme'

def test_specificity_scoring():
    # Test that nested tags score higher
    nested_score = calculate_tag_specificity('work/meetings/standup', ...)
    flat_score = calculate_tag_specificity('notes', ...)
    assert nested_score['specificity_score'] > flat_score['specificity_score']
```

### Integration Tests

```python
# tests/test_quality_integration.py

def test_quality_analysis_workflow(tmp_vault):
    """Test complete quality analysis workflow."""
    # Extract tags
    # Run quality analysis
    # Verify all three analyses run
    # Check report generation
```

---

## Success Metrics

### Quantitative

- [ ] Detect 90%+ of irregular plurals in test corpus
- [ ] Identify overbroad tags with <5% false positive rate
- [ ] Synonym detection precision >80%
- [ ] Performance: Handle 10K tags in <2 minutes

### Qualitative

- [ ] Clear, actionable recommendations in reports
- [ ] Intuitive command interface
- [ ] Comprehensive documentation
- [ ] Positive user feedback on usefulness

---

## Future Enhancements

### Beyond Initial Implementation

- **Machine learning**: Train custom models on user's vault for better synonym detection
- **Language detection**: Support non-English pluralization rules
- **Auto-refinement**: Automatically suggest nested tag hierarchies
- **Visualization**: Generate tag quality dashboards
- **Batch operations**: Apply all quality improvements in one command

---

## References

### Linguistic Resources

- **English Pluralization**: https://en.wikipedia.org/wiki/English_plurals
- **Information Content**: https://en.wikipedia.org/wiki/Pointwise_mutual_information
- **Jaccard Similarity**: https://en.wikipedia.org/wiki/Jaccard_index

### Related Work

- **NLTK Stemming**: https://www.nltk.org/howto/stem.html
- **spaCy Lemmatization**: https://spacy.io/usage/linguistic-features#lemmatization
- **WordNet Synsets**: https://wordnet.princeton.edu/

---

**Document Status:** Ready for implementation
**Next Step:** Begin Phase 1 - Foundation implementation
