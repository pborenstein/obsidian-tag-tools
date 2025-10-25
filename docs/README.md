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
2. **[Configuration Guide](CONFIGURATION.md)** - Vault setup and best practices
3. **[Architecture Overview](ARCHITECTURE.md)** - Understanding how tagex works
4. **[Analytics Guide](ANALYTICS.md)** - Tag analysis, statistics, and relationship detection
5. **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### For Contributors

1. **[Architecture Overview](ARCHITECTURE.md)** - System design and component organization
2. **[Testing Narrative](TESTING_NARRATIVE.md)** - Development approach and testing philosophy
3. **[Archive](archive/)** - Historical decisions and completed plans

### For Algorithm Deep Dives

1. **[Semantic Analysis](SEMANTIC_ANALYSIS.md)** - TF-IDF, cosine similarity, and morphological fallback
2. **[Analytics Guide](ANALYTICS.md)** - Pair analysis, hub detection, and merge recommendations

## Documentation Files

### Core Documentation

| Document | Description | Audience |
|:---------|:------------|:---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flow, component design | Developers |
| [ANALYTICS.md](ANALYTICS.md) | Tag analysis tools, statistics, relationship detection | Users & Developers |
| [SEMANTIC_ANALYSIS.md](SEMANTIC_ANALYSIS.md) | Semantic similarity algorithms and implementation | Developers |
| [TESTING_NARRATIVE.md](TESTING_NARRATIVE.md) | Test development story and approach | Developers |
| [CONFIGURATION.md](CONFIGURATION.md) | Vault setup, git integration, naming conventions, best practices | Users & Developers |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions | Users & Developers |

### Archive

| Document | Description | Audience |
|:---------|:------------|:---------|
| [archive/FRONTMATTER_PARSER_DECISION.md](archive/FRONTMATTER_PARSER_DECISION.md) | PyYAML vs python-frontmatter analysis (Sep 2024) | Developers |
| [archive/TAG_TYPE_FILTERING_PLAN.md](archive/TAG_TYPE_FILTERING_PLAN.md) | Historical implementation plan (completed) | Developers |
| [archive/EVALUATION_2025_09_30.md](archive/EVALUATION_2025_09_30.md) | Documentation quality assessment and recommendations | Developers |

## Additional Resources

- **[Test Suite Documentation](../tests/README.md)** - Test organization and usage
- **[Operation Logs](../log/README.md)** - Log file structure and format

## Contributing to Documentation

When adding new documentation:

- Use lowercase filenames with hyphens (e.g., `new-feature.md`)
- Add entries to this README in the appropriate section
- Update cross-references in related documents
- Consider the reading flow for different audiences