# Design Considerations for Future Iterations

This document captures areas of the current design that may benefit from reconsideration in future versions. These are not bugs or critical issues, but design decisions that could be revisited to improve user experience or architectural clarity.

**Status:** Discussion document
**Created:** 2025-10-25
**Context:** Identified during comprehensive documentation review

---

## 1. Command Structure Inconsistency

**Current State:**

Commands mix vault-based and JSON-file-based interfaces:

```bash
# Vault-based commands
tagex stats /vault                     # Works on vault directory
tagex rename /vault old new            # Works on vault directory

# JSON-based commands
tagex analyze pairs tags.json          # Works on extracted JSON
tagex analyze merge tags.json          # Works on extracted JSON
tagex analyze quality tags.json        # Works on extracted JSON
```

**Issues:**

- **User confusion:** Not clear when to use vault path vs JSON file
- **Workflow complexity:** Requires manual extraction step before analysis
- **Inconsistent mental model:** Some commands "see" the vault directly, others don't
- **Discoverability:** Users might expect all commands to work on vaults

**Potential Solutions:**

**Option A: Unify on vault-based commands**
```bash
# All commands work directly on vaults
tagex stats /vault
tagex analyze pairs /vault
tagex analyze merge /vault
tagex analyze quality /vault

# JSON export becomes optional flag
tagex analyze pairs /vault --export pairs.json
```

**Pros:**
- Consistent interface
- Simpler workflow (no manual extraction)
- Matches user expectation

**Cons:**
- Slower (re-scans vault each time)
- Can't analyze saved snapshots
- Loses comparison capability

**Option B: Unify on JSON-based commands**
```bash
# All commands require extraction first
tagex extract /vault -o tags.json
tagex stats tags.json
tagex analyze pairs tags.json
tagex analyze merge tags.json
```

**Pros:**
- Fast analysis (scan once)
- Snapshot comparison possible
- Predictable workflow

**Cons:**
- Extra step for every workflow
- Stats command becomes less immediate

**Option C: Support both modes**
```bash
# Commands accept either vault or JSON
tagex stats /vault              # Scan and analyze
tagex stats tags.json           # Analyze extracted data

tagex analyze pairs /vault      # Scan and analyze
tagex analyze pairs tags.json   # Analyze extracted data
```

**Pros:**
- Maximum flexibility
- Supports both workflows
- Backward compatible

**Cons:**
- More code complexity
- Potential confusion about which to use

**Recommendation:** Option C (support both) with clear documentation about when to use each mode.

---

## 2. Plural Preference Convention

**Current State:**

The tool has an undocumented preference for plural forms:

- Documented in archived TAG_QUALITY_IMPROVEMENTS.md planning document
- Implemented in `plural_normalizer.py` preference logic
- Not surfaced in user-facing documentation until recent update
- Not configurable by users

**Issues:**

- **Hidden convention:** Users don't know the tool prefers plurals
- **No user control:** Can't override on a vault-wide basis
- **Potentially controversial:** Some users may prefer singular forms
- **Inconsistent with Obsidian:** No standard Obsidian convention exists

**Examples:**
```python
# Current behavior (prefers plural)
normalize_plural_forms("book") → recommends "books"
normalize_plural_forms("idea") → recommends "ideas"

# User might want singular
"Use 'book' as canonical (represents the concept)"
"Use 'idea' as canonical (singular is more abstract)"
```

**Potential Solutions:**

**Option A: Make it configurable**
```yaml
# .tagex-config.yaml
plural_preference: plural  # or: singular, usage-based
```

**Option B: Usage-based preference**
```python
# Prefer whichever form has more uses
if uses("books") > uses("book"):
    canonical = "books"
else:
    canonical = "book"
```

**Option C: Explicit user choice**
```bash
# Require user to specify
tagex analyze plurals tags.json --prefer plural
tagex analyze plurals tags.json --prefer singular
tagex analyze plurals tags.json --prefer usage
```

**Option D: Remove the preference**
```bash
# Just report variants, let user decide
"Found variants: book (67), books (12)"
"Suggestions:"
"  - Merge book → books (plural form)"
"  - Merge books → book (singular form)"
"Choose based on your vault's conventions"
```

**Recommendation:** Option B (usage-based) with Option A (configurable override). Most users want the most-used form as canonical.

---

## 3. Synonym Configuration Discovery

**Current State:**

`.tagex-synonyms.yaml` functionality exists but:

- No initialization command
- No validation feedback
- No example file in repository
- Users won't discover it exists without reading docs
- No error messages if file is malformed

**Issues:**

- **Poor discoverability:** Users won't know this feature exists
- **No onboarding:** No way to bootstrap a config file
- **Silent failures:** Invalid YAML may be silently ignored
- **No examples:** Users must write from scratch

**Potential Solutions:**

**Option A: Add init command**
```bash
tagex init /vault

# Creates:
# - .tagex-synonyms.yaml (with template and examples)
# - .tagex-config.yaml (for future configuration)
# - README.md explaining the files
```

**Option B: Interactive configuration**
```bash
tagex config synonyms /vault

# Interactive prompts:
# "Found tags: python (67), py (23)"
# "Are these synonyms? [y/n]"
# "Which should be canonical? [1] python [2] py"
#
# Saves to .tagex-synonyms.yaml
```

**Option C: Validation command**
```bash
tagex validate /vault

# Checks:
# - .tagex-synonyms.yaml syntax
# - Tag references exist in vault
# - No conflicting definitions
# - Reports issues clearly
```

**Option D: Example file in repo**
```
.tagex-synonyms.example.yaml

# Copy to vault and customize
cp .tagex-synonyms.example.yaml /vault/.tagex-synonyms.yaml
```

**Recommendation:** Combine A, C, and D:
- Add example file to repo
- Add `tagex init` command
- Add `tagex validate` command

---

## 4. Analysis Workflow Fragmentation

**Current State:**

Complete tag cleanup requires:

1. Extract to JSON
2. Run multiple separate analyze commands
3. Manually correlate results
4. Remember which vault the JSON came from
5. Apply changes based on scattered output

```bash
# Current workflow (6 separate commands)
tagex extract /vault -o tags.json
tagex analyze quality tags.json > quality.txt
tagex analyze plurals tags.json > plurals.txt
tagex analyze synonyms tags.json > synonyms.txt
tagex analyze merge tags.json > merge.txt
tagex analyze pairs tags.json > pairs.txt

# Then manually review 5 text files
```

**Issues:**

- **Cognitive overhead:** Track multiple outputs
- **No prioritization:** Which issues to fix first?
- **No integration:** Can't see connections between analyses
- **Lost context:** What vault does this JSON represent?
- **No unified report:** Have to synthesize findings

**Potential Solutions:**

**Option A: Unified analysis command**
```bash
tagex analyze all tags.json

# Runs all analyses, generates unified report:
# - Executive summary
# - Issue prioritization
# - Integrated recommendations
# - Cross-analysis insights
```

**Option B: Health check command**
```bash
tagex health /vault

# Runs everything, generates actionable report:
# ===== VAULT HEALTH REPORT =====
#
# Critical Issues (fix first):
#   - 3 overbroad tags (notes, misc, ideas)
#   - 12 plural variants
#
# Moderate Issues:
#   - 8 synonym groups
#   - 15 morphological variants
#
# Recommended Actions:
#   1. Merge plurals (12 consolidations)
#   2. Fix overbroad tags (3 refinements)
#   3. ...
```

**Option C: Interactive cleanup wizard**
```bash
tagex cleanup /vault

# Interactive workflow:
# "Found 12 plural variants. Review? [y/n]"
# "book (67) / books (12) → Merge into books? [y/n/skip]"
# "Applied 10 merges, skipped 2"
# "Next: 8 synonym groups. Continue? [y/n]"
```

**Option D: Report generation**
```bash
tagex report /vault -o report.html

# Generates comprehensive HTML report:
# - Visual graphs of tag relationships
# - Issue breakdown by category
# - Click to apply suggestions
# - Before/after projections
```

**Recommendation:** Option B (health check) + Option D (report generation). Provides both quick overview and detailed analysis.

---

## 5. Module Organization

**Current State:**

Related functionality is split across directories:

```
tagex/
├── analysis/
│   ├── pair_analyzer.py
│   ├── merge_analyzer.py
│   ├── synonym_analyzer.py
│   └── breadth_analyzer.py
├── config/
│   └── synonym_config.py
└── utils/
    ├── tag_normalizer.py
    └── plural_normalizer.py    ← Why here and not in analysis/?
```

**Issues:**

- **Organizational inconsistency:** Why is `plural_normalizer` in `utils/`?
- **Unclear boundaries:** What belongs in `utils/` vs `analysis/`?
- **Import confusion:** Where to look for analysis-related code?
- **Poor cohesion:** Related analysis code in different directories

**Rationale Questions:**

- Is plural normalization a "utility" or an "analysis"?
- Should `tag_normalizer` (validation) be separate from analysis?
- Should `synonym_config` be in `config/` or `analysis/`?

**Potential Solutions:**

**Option A: Consolidate all analysis code**
```
tagex/analysis/
├── pair_analyzer.py
├── merge_analyzer.py
├── synonym_analyzer.py
├── breadth_analyzer.py
├── plural_normalizer.py       ← Move here
└── synonym_config.py           ← Move here
```

**Option B: Create submodules**
```
tagex/analysis/
├── patterns/
│   ├── plural_normalizer.py
│   ├── synonym_detector.py
│   └── morphology.py
├── metrics/
│   ├── specificity.py
│   ├── similarity.py
│   └── cooccurrence.py
└── analyzers/
    ├── pair_analyzer.py
    ├── merge_analyzer.py
    └── quality_analyzer.py
```

**Option C: Keep current, document rationale**
```
# Document in ARCHITECTURE.md:
# utils/ - Reusable components used by multiple modules
# analysis/ - Analysis commands and algorithms
# config/ - Configuration file loading/parsing
```

**Recommendation:** Option A (consolidate). `plural_normalizer` is primarily used by analysis, should live with analysis code. Keep `tag_normalizer` in utils (it's truly cross-cutting).

---

## 6. Dependency Transparency

**Current State:**

The merge analyzer uses TF-IDF embeddings via scikit-learn, with a fallback to pattern-based detection when sklearn is unavailable:

```python
# User runs:
tagex analyze merge tags.json

# Which algorithm is running?
# - TF-IDF embeddings (if sklearn available)
# - Pattern-based fallback (if sklearn missing)
# - No indication to user which mode is active
```

**Issues:**

- **Mode ambiguity:** Users don't know which algorithm is running
- **Result differences:** TF-IDF and pattern-based produce different results
- **Silent degradation:** Missing sklearn silently changes behavior
- **No performance indication:** TF-IDF is slower, should users know?
- **Comparison difficulty:** Can't easily compare modes

**Potential Solutions:**

**Option A: Runtime mode indicator**
```bash
tagex analyze merge tags.json

# Output:
# Using TF-IDF embeddings (sklearn available)
# Found 15 merge suggestions...

# Or:
# Using pattern-based fallback (sklearn not available)
# Found 12 merge suggestions...
```

**Option B: Explicit mode selection**
```bash
# Require explicit choice
tagex analyze merge tags.json --mode tfidf
tagex analyze merge tags.json --mode pattern

# Error if sklearn missing:
# "Error: TF-IDF mode requires scikit-learn"
# "Install: uv add scikit-learn"
# "Or use: --mode pattern"
```

**Option C: Performance/accuracy hints**
```bash
tagex analyze merge tags.json

# Output:
# Mode: Pattern-based (faster, less accurate)
# Tip: Install scikit-learn for TF-IDF mode (slower, more accurate)
# Run: uv add scikit-learn
```

**Option D: Comparison mode**
```bash
tagex analyze merge tags.json --compare

# Runs both algorithms, shows differences:
# TF-IDF found: 15 suggestions
# Pattern found: 12 suggestions
#
# Only in TF-IDF (3):
#   - music / audio (0.65 similarity)
#   - ...
#
# In both (12):
#   - write / writing / writer
#   - ...
```

**Recommendation:** Option A (runtime indicator) + Option C (performance hints). Users should know which mode is active and how to get better results.

---

## Summary of Recommendations

| Issue | Recommendation | Effort | Impact |
|:------|:--------------|:-------|:-------|
| 1. Command Structure | Support both vault and JSON modes | Medium | High - Better UX |
| 2. Plural Preference | Usage-based with config override | Low | Medium - User control |
| 3. Synonym Discovery | Add init + validate + example file | Medium | High - Discoverability |
| 4. Workflow Fragmentation | Add health + report commands | High | High - Usability |
| 5. Module Organization | Consolidate analysis code | Low | Low - Code clarity |
| 6. Dependency Transparency | Runtime indicator + hints | Low | Medium - User awareness |

## Next Steps

These considerations should be:

1. **Discussed:** Get user feedback on which issues matter most
2. **Prioritized:** Rank by impact and effort
3. **Prototyped:** Try solutions in branches
4. **Documented:** Update design docs with decisions
5. **Implemented:** Build the improvements

**Not urgent:** Current design works well. These are quality-of-life improvements for future iterations.

---

**Document Status:** Discussion/Planning
**Next Review:** After gathering user feedback
