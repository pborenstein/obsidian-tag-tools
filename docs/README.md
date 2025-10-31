# tagex Documentation

Welcome to the tagex documentation. This guide will help you navigate the available resources based on your needs.

## Start Here

**👉 New to tagex? Read [GETTING_STARTED.md](GETTING_STARTED.md) for a step-by-step walkthrough of the most common workflow.**

This 10-step guide will take you from installation to a cleaned-up vault in about 15 minutes.

**⚡ In a hurry? See [HAPPY_PATH.md](HAPPY_PATH.md) for just the commands (no explanations).**

## Quick Navigation

- **First time here?** → [Getting Started Guide](GETTING_STARTED.md) - Complete walkthrough
- **Just the commands?** → [Happy Path Cheat Sheet](HAPPY_PATH.md) - Ultra-minimal command list
- **Need a quick reference?** → [Quick Reference](QUICK_REFERENCE.md) - Complete command cheat sheet
- **Setting up your vault?** → [Setup Guide](SETUP_GUIDE.md) - Installation and best practices
- **Something broken?** → [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- **Want to understand how it works?** → [Architecture Overview](ARCHITECTURE.md) - System design
- **Using analysis tools?** → [Analytics Guide](ANALYTICS.md) - Complete analysis workflows
- **Deep dive?** → [Algorithms Reference](ALGORITHMS.md) - Technical details

## Suggested Reading Flow

### For New Users

1. **[Getting Started Guide](GETTING_STARTED.md)** - **START HERE** - Step-by-step walkthrough of the most common workflow
2. **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet (keep this handy!)
3. **[Setup Guide](SETUP_GUIDE.md)** - Installation details and vault setup
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
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | **Step-by-step walkthrough of the complete workflow** | **New Users** |
| **[HAPPY_PATH.md](HAPPY_PATH.md)** | **Ultra-minimal cheat sheet - just the commands** | **All Users** |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | **Single-page command reference and cheat sheet** | **All Users** |
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
| [archive/COMMAND_STRUCTURE_ANALYSIS.md](archive/COMMAND_STRUCTURE_ANALYSIS.md) | CLI restructure analysis and design options (Oct 2025) | Developers |
| [archive/COMMAND_FLOW_DIAGRAM.md](archive/COMMAND_FLOW_DIAGRAM.md) | Visual command hierarchy and workflow diagrams (Oct 2025) | Developers |
| [archive/RESTRUCTURE_ROADMAP.md](archive/RESTRUCTURE_ROADMAP.md) | Implementation plan for CLI restructure (Oct 2025) | Developers |
| [archive/RESTRUCTURE_COMPLETE.md](archive/RESTRUCTURE_COMPLETE.md) | Completion report and migration guide (Oct 2025) | Developers |
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