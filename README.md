# Tag Extractor

Extract and analyze tags from Obsidian vault markdown files.

## Usage

After [ installation](#installation ), run the command:
```bash
tagex <vault_path> [options]
```

Or during development:
```bash
uv run tagex <vault_path> [options]
```

### Options

- `--output`, `-o`: Output file path (default: stdout)
- `--format`, `-f`: Output format (`json`, `csv`, `txt`) (default: json)
- `--exclude`: Patterns to exclude (can be used multiple times)
- `--verbose`, `-v`: Enable verbose logging
- `--quiet`, `-q`: Suppress summary output
- `--no-filter`: Disable tag filtering (include all raw tags)

### Examples

Extract tags from vault and output as JSON:
```bash
tagex /path/to/vault
```

Save tags to CSV file:
```bash
tagex /path/to/vault -f csv -o tags.csv
```

Extract with exclusions:
```bash
tagex /path/to/vault --exclude "*.template.md" --exclude "drafts/*"
```

Extract all raw tags without filtering:
```bash
tagex /path/to/vault --no-filter
```

Get a list of tags sorted by frequency:
```bash
tagex /path/to/vault -f json | jq -r '.[] | "\(.tag) \(.tagCount)"'
```

## Features

- Extracts tags from frontmatter YAML
- Extracts inline hashtags from content
- Automatic tag validation - filters out noise (numbers, HTML entities, technical patterns) by default
- Multiple output formats (JSON, CSV, text)
- File pattern exclusions
- Statistics and summaries
- Advanced tag relationship analysis (co-occurrence, clustering)
- Migration impact assessment tools

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

Install as a global command:
```bash
uv tool install --editable .
```

Or install dependencies for development:
```bash
uv sync
```


## Documentation

| Document | Description |
| :----------|:-------------|
| [ARCHITECTURE.md](doc/ARCHITECTURE.md) | System architecture and component design |
| [ANALYTICS.md](doc/ANALYTICS.md) | Tag analysis tools and usage guide |
| [ROADMAP.md](doc/ROADMAP.md) | Planned features and improvements |

