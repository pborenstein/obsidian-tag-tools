# Tagex Command Hierarchy

Current command structure for tagex CLI.

## Command Tree

```
tagex
├── init [vault_path]                    # Quick access - Initialize vault configuration
├── stats [vault_path]                   # Quick access - Display tag statistics
├── health [vault_path]                  # Quick access - Generate health report
│
├── config/                              # Configuration management
│   ├── validate [vault_path]            # Validate configuration
│   ├── show [vault_path]                # Display current configuration
│   └── edit [vault_path] [config]       # Edit configuration in $EDITOR
│
├── tag/                                 # Tag operations (write operations)
│   ├── export [vault_path]              # Export tags to JSON/CSV/text
│   ├── rename <vault> <old> <new>       # Rename a tag
│   ├── merge <vault> <tags...> --into   # Merge tags into one
│   ├── delete <vault> <tags...>         # Delete tags
│   ├── add <vault> <file> <tags...>     # Add tags to a file
│   ├── fix [vault_path]                 # Fix duplicate tags: fields
│   └── apply [vault_path] <ops.yaml>    # Apply operations from YAML
│
├── analyze/                             # Analysis operations (read-only)
│   ├── pairs [input_path]               # Analyze tag co-occurrence
│   ├── quality [input_path]             # Analyze tag quality metrics
│   ├── synonyms [input_path]            # Detect synonym tags
│   ├── plurals [input_path]             # Detect singular/plural variants
│   ├── merges [input_path]              # Suggest merge opportunities
│   ├── suggest [vault_path] [paths...]  # Suggest tags for notes
│   └── recommendations [vault_path]     # Generate consolidated recommendations
│
└── vault/                               # Vault maintenance operations
    ├── cleanup [vault_path]             # Remove .bak backup files
    ├── backup [vault_path]              # Create vault backup
    └── verify [vault_path]              # Verify vault integrity
```

## Design Principles

### 1. Hybrid Structure
- **Quick access commands** at top level for common operations (`init`, `stats`, `health`)
- **Grouped commands** for specific domains (`config/`, `tag/`, `analyze/`, `vault/`)

### 2. Read vs. Write Separation
- **Read-only**: `config/`, `analyze/`, `tag export`
- **Write operations**: `tag/` (except export), `vault/`
- All write operations require `--execute` flag (safe by default)

### 3. Consistent Arguments
- `[vault_path]` is optional, defaults to current directory
- Required arguments use `<angle_brackets>`
- Data arguments come after vault path
- All analyze commands accept either vault path OR JSON file

### 4. Safety Levels

**Level 1: Always Safe (Read-Only)**

```
• stats
• health
• config validate, show
• tag export
• ALL analyze commands
```

**Level 2: Preview Mode (Default)**

```
• tag rename (without --execute)
• tag merge (without --execute)
• tag delete (without --execute)
• tag add (without --execute)
• tag fix (without --execute)
• tag apply (without --execute)
• vault cleanup (without --execute)
```

**Level 3: Writes Files (Requires --execute)**

```
• tag rename --execute
• tag merge --execute
• tag delete --execute
• tag add --execute
• tag fix --execute
• tag apply --execute
• vault cleanup --execute
```

**Level 4: Configuration (Low Risk)**

```
• init
• config edit
• vault backup
```

## Common Workflows

### Quick Start

```bash
tagex init              # Initialize configuration
tagex health            # Check vault health
tagex analyze recommendations --export ops.yaml
tagex tag apply ops.yaml --execute
```

### Detailed Analysis

```bash
tagex stats                              # View current state
tagex analyze synonyms --export syn.yaml
tagex analyze plurals --export plu.yaml
tagex tag apply syn.yaml                 # Preview
tagex tag apply syn.yaml --execute       # Execute
```

### One-Off Operations

```bash
tagex tag rename old-tag new-tag --execute
tagex tag merge tag1 tag2 --into merged --execute
tagex tag delete unwanted-tag --execute
```

### Content-Based Tag Suggestions

```bash
tagex analyze suggest --min-tags 2 --export suggestions.yaml
tagex tag apply suggestions.yaml --execute
```

## Command Capabilities Matrix

| Command | Read Only | Writes Files | Export YAML | Vault Optional | Accepts JSON |
|---------|-----------|--------------|-------------|----------------|--------------|
| **Top Level** |
| init | | ✓ | | ✓ | |
| stats | ✓ | | ✓ | ✓ | ✓ |
| health | ✓ | | | ✓ | ✓ |
| **config/** |
| validate | ✓ | | | ✓ | |
| show | ✓ | | | ✓ | |
| edit | | ✓ | | ✓ | |
| **tag/** |
| export | ✓ | | ✓ | ✓ | |
| rename | | ✓ | | | |
| merge | | ✓ | | | |
| delete | | ✓ | | | |
| add | | ✓ | | | |
| fix | | ✓ | | ✓ | |
| apply | | ✓ | | ✓ | YAML |
| **analyze/** |
| pairs | ✓ | | | ✓ | ✓ |
| quality | ✓ | | ✓ | ✓ | ✓ |
| synonyms | ✓ | | ✓ | ✓ | ✓ |
| plurals | ✓ | | ✓ | ✓ | ✓ |
| merges | ✓ | | ✓ | ✓ | ✓ |
| suggest | ✓ | | ✓ | | |
| recommendations | ✓ | | ✓ | ✓ | ✓ |
| **vault/** |
| cleanup | | ✓ | | | |
| backup | ✓ | ✓ | | | |
| verify | ✓ | | | | |

## See Also

- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick command reference
- [ANALYTICS.md](ANALYTICS.md) - Detailed analysis command documentation
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration system details
- [archive/COMMAND_STRUCTURE_ANALYSIS.md](archive/COMMAND_STRUCTURE_ANALYSIS.md) - Original design analysis
- [archive/COMMAND_FLOW_DIAGRAM.md](archive/COMMAND_FLOW_DIAGRAM.md) - Planning diagrams
