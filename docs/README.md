# tagex Documentation

Welcome to the tagex documentation. This guide will help you navigate the available resources based on your needs.

## Quick Navigation

- **New to tagex?** Start with the [main README](../README.md) for installation and quick start
- **Setting up your vault?** See [Configuration Guide](CONFIGURATION.md) for best practices
- **Encountering issues?** Check [Troubleshooting](TROUBLESHOOTING.md) for solutions
- **Understanding the system?** See [Architecture Overview](ARCHITECTURE.md)
- **Using analysis tools?** Check out the [Analytics Guide](ANALYTICS.md)
- **Deep technical dive?** Read [Semantic Analysis](SEMANTIC_ANALYSIS.md)

## Suggested Reading Flow

### For New Users

1. **[Main README](../README.md)** - Installation, commands, and basic usage
2. **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet (keep this handy!)
3. **[Analytics Guide](ANALYTICS.md)** - Complete analysis guide with decision tree
4. **[Configuration Guide](CONFIGURATION.md)** - Vault setup and best practices
5. **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### For Contributors

1. **[Architecture Overview](ARCHITECTURE.md)** - System design and component organization
2. **[Algorithms Reference](ALGORITHMS.md)** - Algorithm implementations and complexity analysis
3. **[Testing Narrative](TESTING_NARRATIVE.md)** - Development approach and testing philosophy
4. **[Archive](archive/)** - Historical decisions and completed plans

### For Algorithm Deep Dives

1. **[Algorithms Reference](ALGORITHMS.md)** - Complete technical reference for all algorithms
2. **[Analytics Guide](ANALYTICS.md)** - User-focused guide with practical examples
3. **[Semantic Analysis](SEMANTIC_ANALYSIS.md)** - Original TF-IDF documentation (now superseded by ALGORITHMS.md)

## Documentation Files

### Core Documentation

| Document | Description | Audience |
|:---------|:------------|:---------|
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | **Single-page command reference and cheat sheet** | **Users** |
| [ANALYTICS.md](ANALYTICS.md) | Complete analysis guide with decision tree and workflows | Users & Developers |
| [SYNONYM_CONFIGURATION.md](SYNONYM_CONFIGURATION.md) | .tagex-synonyms.yaml format, examples, and best practices | Users & Developers |
| [CONFIGURATION.md](CONFIGURATION.md) | Vault setup, git integration, naming conventions | Users & Developers |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions | Users & Developers |

### Technical Documentation

| Document | Description | Audience |
|:---------|:------------|:---------|
| [ALGORITHMS.md](ALGORITHMS.md) | Algorithm details: TF-IDF, Jaccard, specificity scoring, etc. | Developers |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flow, component design | Developers |
| [SEMANTIC_ANALYSIS.md](SEMANTIC_ANALYSIS.md) | Semantic similarity algorithms (deprecated - see ALGORITHMS.md) | Developers |
| [TESTING_NARRATIVE.md](TESTING_NARRATIVE.md) | Test development story and approach | Developers |

### Archive

| Document | Description | Audience |
|:---------|:------------|:---------|
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