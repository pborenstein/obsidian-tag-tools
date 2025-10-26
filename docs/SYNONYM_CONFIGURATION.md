# Synonym Configuration Guide

This guide explains how to create and use `.tagex-synonyms.yaml` files to define explicit synonym relationships in your Obsidian vault.

## Overview

The synonym configuration system allows you to declare that certain tags should be treated as equivalent, enabling consistent tag consolidation and canonical form enforcement.

**Use cases:**
- Define project-specific abbreviations (ai → artificial-intelligence)
- Map domain terminology to standard forms (neuro → neurodivergent)
- Enforce naming conventions (js → javascript)
- Group related tags that mean the same thing (music/audio/sound)

## File Location

Create a file named `.tagex-synonyms.yaml` in your vault root directory:

```
MyVault/
├── .tagex-synonyms.yaml  ← Configuration file
├── notes/
├── projects/
└── ...
```

## File Format

The configuration uses YAML format with two main sections:

### Basic Structure

```yaml
# Synonym groups - first tag in each list is canonical
synonyms:
  - [canonical-tag, variant1, variant2, ...]
  - [another-canonical, variant-a, variant-b]

# Preference mappings - all variants map to the key
prefer:
  canonical-tag: [variant1, variant2]
  another-canonical: [variant-a, variant-b]
```

## Section 1: `synonyms`

**Purpose:** Define groups of equivalent tags where the first tag is canonical.

**Format:** List of lists, where each inner list contains synonymous tags.

### Examples

#### Example 1: Technology Abbreviations

```yaml
synonyms:
  # Programming languages
  - [python, py, python3]
  - [javascript, js, ecmascript]
  - [typescript, ts]

  # Technologies
  - [machine-learning, ml, ai, artificial-intelligence]
  - [natural-language-processing, nlp]
  - [computer-vision, cv, image-processing]
```

**Effect:**
- `py` → treated as `python`
- `python3` → treated as `python`
- `ml` and `ai` → both treated as `machine-learning`

#### Example 2: Domain-Specific Terms

```yaml
synonyms:
  # Neurodiversity
  - [neurodivergent, neuro, neurodivergence, neurotype]
  - [adhd, add, attention-deficit]
  - [autism, asd, autistic, autism-spectrum]

  # Creative work
  - [writing, blog, article, post]
  - [music, audio, sound, sonic]
  - [video, film, movie, cinema]
```

**Effect:**
- `neuro`, `neurodivergence`, `neurotype` → all treated as `neurodivergent`
- `blog`, `article`, `post` → all treated as `writing`

#### Example 3: Project Names

```yaml
synonyms:
  # Work projects
  - [project-phoenix, phoenix, prj-phoenix]
  - [client-acme, acme, acme-corp]

  # Research areas
  - [quantum-computing, qc, quantum-comp]
  - [distributed-systems, dist-sys, distributed-computing]
```

## Section 2: `prefer`

**Purpose:** Simple one-to-many mappings where all variants map to a single canonical form.

**Format:** Dictionary where keys are canonical tags and values are lists of variants.

### Examples

#### Example 1: Common Abbreviations

```yaml
prefer:
  technology: [tech, technical]
  documentation: [docs, doc]
  configuration: [config, cfg]
  development: [dev, devel]
  production: [prod]
```

**Effect:**
- `tech` → `technology`
- `docs` → `documentation`
- `config` → `configuration`

#### Example 2: Spelling Variations

```yaml
prefer:
  organization: [organisation, organizing, organising]
  behavior: [behaviour]
  color: [colour]
```

**Effect:**
- British/American spelling variants map to American spelling

#### Example 3: Informal vs. Formal

```yaml
prefer:
  meeting: [mtg, meet]
  reference: [ref]
  example: [ex, eg]
  information: [info]
```

## Complete Example Configuration

Here's a comprehensive example combining multiple domains:

```yaml
# .tagex-synonyms.yaml

# Synonym groups (first tag is canonical)
synonyms:
  # Technology & Programming
  - [python, py, python3]
  - [javascript, js, ecmascript]
  - [typescript, ts]
  - [machine-learning, ml, ai, artificial-intelligence]
  - [deep-learning, dl, neural-networks]
  - [natural-language-processing, nlp]

  # Neurodiversity & Mental Health
  - [neurodivergent, neuro, neurodivergence, neurotype]
  - [adhd, add, attention-deficit]
  - [autism, asd, autistic, autism-spectrum]
  - [executive-function, exec-function, ef]

  # Creative & Media
  - [writing, blog, article, post]
  - [music, audio, sound]
  - [video, film, movie]
  - [photography, photo, photos]

  # Work & Projects
  - [project, prj, proj]
  - [meeting, meetings]
  - [research, rsch]

# Preference mappings (simple one-to-many)
prefer:
  # Common abbreviations
  technology: [tech, technical]
  documentation: [docs, doc]
  configuration: [config, cfg]
  development: [dev, devel]
  production: [prod]

  # Spellings
  organization: [organisation]
  behavior: [behaviour]

  # Informal to formal
  information: [info]
  reference: [ref]
  example: [ex]
```

## Using Synonym Configuration

### Programmatic Access

Load and query the configuration in Python:

```python
from pathlib import Path
from tagex.config.synonym_config import SynonymConfig

# Load configuration from vault
vault_path = Path("/path/to/vault")
config = SynonymConfig(vault_path)

# Get canonical form of a tag
canonical = config.get_canonical("py")
# Returns: "python"

canonical = config.get_canonical("ml")
# Returns: "machine-learning"

# Get all synonyms for a tag
synonyms = config.get_synonyms("python")
# Returns: {"py", "python3"}

# Get all tags in the same group
group = config.get_all_in_group("python")
# Returns: {"python", "py", "python3"}
```

### Command-Line Integration

The synonym configuration is automatically loaded when running analysis:

```bash
# Synonym detection will respect .tagex-synonyms.yaml
tagex analyze synonyms tags.json

# Future: Apply configured synonyms
tagex apply synonyms /vault --dry-run
```

## Best Practices

### 1. Choose Canonical Forms Carefully

**Good canonical forms:**
- ✅ Full, descriptive names (`machine-learning` not `ml`)
- ✅ Commonly used terms (`python` not `py`)
- ✅ Unambiguous (`javascript` not `js` which could mean "json" or "java-script")

**Poor canonical forms:**
- ❌ Abbreviations as canonical (`ml` instead of `machine-learning`)
- ❌ Ambiguous terms (`ai` could mean many things)
- ❌ Overly specific (`python-3.11` instead of `python`)

### 2. Document Your Choices

Add comments to explain non-obvious groupings:

```yaml
synonyms:
  # "Audio" encompasses music, sound design, and audio engineering
  - [audio, music, sound, sonic]

  # "Neurodivergent" is the umbrella term for all neurodiversity tags
  - [neurodivergent, neuro, neurodivergence, neurotype]
```

### 3. Start Small, Grow Incrementally

Don't try to define all synonyms upfront. Start with:
1. Clear abbreviations (py → python)
2. Known duplicates from `tagex analyze synonyms`
3. Project-specific terms

Add more as patterns emerge.

### 4. Test Before Committing

Always use dry-run mode when applying synonyms:

```bash
# Preview changes
tagex apply synonyms /vault --dry-run

# Review output, then apply
tagex apply synonyms /vault
```

### 5. Keep Groups Focused

**Good grouping:**
```yaml
synonyms:
  - [python, py, python3]           # Clear variants of same language
  - [javascript, js, ecmascript]     # Same language, different names
```

**Bad grouping:**
```yaml
synonyms:
  # Too broad - these are related but distinct concepts!
  - [programming, coding, development, software, python, javascript]
```

### 6. Align with Vault Conventions

Check your most-used tags first:

```bash
# See top tags
tagex stats /vault --top 50

# Use the most common form as canonical
# If "python" has 150 uses and "py" has 23 uses,
# make "python" canonical
```

### 7. Version Control Your Configuration

Commit `.tagex-synonyms.yaml` to git alongside your vault:

```bash
git add .tagex-synonyms.yaml
git commit -m "Add synonym configuration for tech abbreviations"
```

## Common Patterns

### Pattern 1: Programming Languages

```yaml
synonyms:
  - [python, py, python3]
  - [javascript, js, ecmascript, node, nodejs]
  - [typescript, ts]
  - [java, jdk, jvm]
  - [c-sharp, csharp, cs, dotnet]
  - [go, golang]
  - [rust, rustlang]
```

### Pattern 2: Frameworks & Libraries

```yaml
synonyms:
  - [react, reactjs, react-js]
  - [vue, vuejs, vue-js]
  - [angular, angularjs]
  - [django, django-framework]
  - [flask, flask-framework]
  - [pytorch, torch]
  - [tensorflow, tf]
```

### Pattern 3: Research Topics

```yaml
synonyms:
  - [machine-learning, ml, ai, artificial-intelligence]
  - [deep-learning, dl, neural-networks, neural-nets]
  - [natural-language-processing, nlp, text-analysis]
  - [computer-vision, cv, image-processing]
  - [reinforcement-learning, rl]
```

### Pattern 4: Personal Knowledge Management

```yaml
synonyms:
  - [meeting, meetings, mtg]
  - [idea, ideas, brainstorm]
  - [task, tasks, todo, todos]
  - [project, projects, prj]
  - [note, notes]
  - [reference, references, ref]
```

### Pattern 5: Academic Subjects

```yaml
synonyms:
  - [mathematics, math, maths]
  - [physics, phys]
  - [chemistry, chem]
  - [biology, bio]
  - [computer-science, cs, compsci]
  - [psychology, psych, psychol]
```

## Troubleshooting

### Configuration Not Loading

**Check:**
1. File is named exactly `.tagex-synonyms.yaml` (note the leading dot)
2. File is in vault root, not a subdirectory
3. YAML syntax is valid (use a YAML validator)

**Test:**
```python
from pathlib import Path
from tagex.config.synonym_config import SynonymConfig

config = SynonymConfig(Path("/path/to/vault"))
print(f"Loaded {len(config.synonym_groups)} groups")
print(f"Config file: {config.config_file}")
print(f"Exists: {config.config_file.exists()}")
```

### YAML Syntax Errors

**Common mistakes:**

**Wrong:** (missing spaces after colons)
```yaml
prefer:
  python:[py, python3]
```

**Right:**
```yaml
prefer:
  python: [py, python3]
```

**Wrong:** (inconsistent indentation)
```yaml
synonyms:
  - [python, py]
   - [javascript, js]  # Extra space!
```

**Right:**
```yaml
synonyms:
  - [python, py]
  - [javascript, js]
```

### Conflicting Definitions

**Problem:**
```yaml
synonyms:
  - [python, py, python3]
  - [py, python-2, legacy-python]  # "py" appears in both groups!
```

**Solution:** Each tag should appear in only one group. Consolidate:
```yaml
synonyms:
  - [python, py, python3, python-2, legacy-python]
```

## Related Documentation

- [ANALYTICS.md](ANALYTICS.md) - Synonym detection algorithms
- [ALGORITHMS.md](ALGORITHMS.md) - Technical details of synonym matching

---

**Document Version:** 1.0
**Last Updated:** 2025-10-25
