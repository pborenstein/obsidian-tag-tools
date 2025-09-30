# tagex Documentation

Welcome to the tagex documentation. This guide will help you navigate the available resources based on your needs.

## Quick Navigation

- **New to tagex?** Start with the [main README](../README.md) for installation and quick start
- **Understanding the system?** See [Architecture Overview](architecture.md)
- **Using analysis tools?** Check out the [Analytics Guide](analytics.md)
- **Deep technical dive?** Read [Semantic Analysis](semantic-analysis.md)

## Suggested Reading Flow

### For New Users

1. **[Main README](../README.md)** - Installation, commands, and basic usage
2. **[Architecture Overview](architecture.md)** - Understanding how tagex works
3. **[Analytics Guide](analytics.md)** - Tag analysis, statistics, and relationship detection

### For Contributors

1. **[Architecture Overview](architecture.md)** - System design and component organization
2. **[Testing Narrative](testing-narrative.md)** - Development approach and testing philosophy
3. **[Decision Records](decisions/)** - Architectural decisions and rationale

### For Algorithm Deep Dives

1. **[Semantic Analysis](semantic-analysis.md)** - TF-IDF, cosine similarity, and morphological fallback
2. **[Analytics Guide](analytics.md)** - Pair analysis, hub detection, and merge recommendations

## Documentation Files

### Core Documentation

| Document | Description |
|:---------|:------------|
| [architecture.md](architecture.md) | System architecture, data flow, component design |
| [analytics.md](analytics.md) | Tag analysis tools, statistics, relationship detection |
| [semantic-analysis.md](semantic-analysis.md) | Semantic similarity algorithms and implementation |
| [testing-narrative.md](testing-narrative.md) | Test development story and approach |

### Decision Records

| Document | Description |
|:---------|:------------|
| [decisions/frontmatter-parser.md](decisions/frontmatter-parser.md) | PyYAML vs python-frontmatter analysis |

### Archive

| Document | Description |
|:---------|:------------|
| [archive/tag-type-filtering-plan.md](archive/tag-type-filtering-plan.md) | Historical implementation plan (completed) |

## Additional Resources

- **[Test Suite Documentation](../tests/README.md)** - Test organization and usage
- **[Operation Logs](../log/README.md)** - Log file structure and format

## Contributing to Documentation

When adding new documentation:

- Use lowercase filenames with hyphens (e.g., `new-feature.md`)
- Add entries to this README in the appropriate section
- Update cross-references in related documents
- Consider the reading flow for different audiences