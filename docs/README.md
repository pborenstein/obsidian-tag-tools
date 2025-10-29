# tagex Documentation

Welcome to the tagex documentation. This guide will help you navigate the available resources based on your needs.

## Quick Navigation

- **New to tagex?** Start with the [main README](../README.md) for installation and quick start
- **Setting up your vault?** See [Setup Guide](SETUP_GUIDE.md) for installation and best practices
- **Encountering issues?** Check [Troubleshooting](TROUBLESHOOTING.md) for solutions
- **Understanding the system?** See [Architecture Overview](ARCHITECTURE.md)
- **Using analysis tools?** Check out the [Analytics Guide](ANALYTICS.md)
- **Deep technical dive?** Read [Algorithms Reference](ALGORITHMS.md)

## Suggested Reading Flow

### For New Users

1. **[Main README](../README.md)** - Installation, commands, and basic usage
2. **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet (keep this handy!)
3. **[Setup Guide](SETUP_GUIDE.md)** - Installation and vault setup
4. **[Configuration Reference](CONFIGURATION_REFERENCE.md)** - `.tagex/` directory configuration files
5. **[Analytics Guide](ANALYTICS.md)** - Complete analysis guide with decision tree
6. **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### For Contributors

1. **[Architecture Overview](ARCHITECTURE.md)** - System design and component organization
2. **[Algorithms Reference](ALGORITHMS.md)** - Algorithm implementations and complexity analysis
3. **[Archive](archive/)** - Historical decisions, completed plans, and development narratives

### For Algorithm Deep Dives

1. **[Algorithms Reference](ALGORITHMS.md)** - Complete technical reference for all algorithms
2. **[Analytics Guide](ANALYTICS.md)** - User-focused guide with practical examples

## Documentation Files

### Core Documentation

| Document | Description | Audience |
|:---------|:------------|:---------|
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | **Single-page command reference and cheat sheet** | **Users** |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Installation, vault setup, git integration, naming conventions | Users |
| [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) | `.tagex/` directory configuration files (config.yaml, synonyms.yaml, exclusions.yaml) | Users & Developers |
| [ANALYTICS.md](ANALYTICS.md) | Complete analysis guide with decision tree and workflows | Users & Developers |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions | Users & Developers |

### Technical Documentation

| Document | Description | Audience |
|:---------|:------------|:---------|
| [ALGORITHMS.md](ALGORITHMS.md) | Algorithm details: TF-IDF, Jaccard, specificity scoring, etc. | Developers |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flow, component design | Developers |

### Archive

| Document | Description | Audience |
|:---------|:------------|:---------|
| [archive/DESIGN_CONSIDERATIONS.md](archive/DESIGN_CONSIDERATIONS.md) | Future design discussions and unresolved tensions | Developers |
| [archive/SEMANTIC_ANALYSIS.md](archive/SEMANTIC_ANALYSIS.md) | Original TF-IDF documentation (superseded by ALGORITHMS.md) | Developers |
| [archive/TESTING_NARRATIVE.md](archive/TESTING_NARRATIVE.md) | Documentation-driven test development methodology | Developers |
| [archive/FRONTMATTER_PARSER_DECISION.md](archive/FRONTMATTER_PARSER_DECISION.md) | PyYAML vs python-frontmatter analysis (Sep 2024) | Developers |
| [archive/TAG_TYPE_FILTERING_PLAN.md](archive/TAG_TYPE_FILTERING_PLAN.md) | Historical implementation plan (completed) | Developers |
| [archive/TAG_QUALITY_IMPROVEMENTS.md](archive/TAG_QUALITY_IMPROVEMENTS.md) | Tag quality analysis implementation plan (completed Oct 2025) | Developers |
| [archive/EVALUATION_2025_09_30.md](archive/EVALUATION_2025_09_30.md) | Documentation quality assessment and recommendations | Developers |

## Additional Resources

- **[Test Suite Documentation](../tests/README.md)** - Test organization and usage
- **[Operation Logs](../logs/README.md)** - Log file structure and format

## Contributing to Documentation

When adding new documentation:

- Use lowercase filenames with hyphens (e.g., `new-feature.md`)
- Add entries to this README in the appropriate section
- Update cross-references in related documents
- Consider the reading flow for different audiences