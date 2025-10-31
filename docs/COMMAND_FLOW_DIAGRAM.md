# Tagex Command Flow & Interaction Diagram

## Current Command Hierarchy (Visual)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           TAGEX CLI                                 │
└─────────────────────────────────────────────────────────────────────┘
           │
           ├── TOP LEVEL (Inconsistent)
           │   ├── init [vault]            ← Configuration
           │   ├── validate [vault]        ← Configuration
           │   ├── stats [vault]           ← Information
           │   └── health [vault]          ← Information
           │
           ├── tags/ (Write Operations)
           │   ├── extract [vault]         ← READ ONLY (shouldn't be here!)
           │   ├── rename <v> <old> <new>  ← WRITE
           │   ├── merge <v> ... --into    ← WRITE
           │   ├── delete <v> <tags>       ← WRITE
           │   ├── fix-duplicates [v]      ← WRITE
           │   └── apply <ops.yaml>        ← WRITE (executes multiple ops)
           │
           ├── analyze/ (Read-Only Analysis)
           │   ├── pairs [input]           ← JSON or Vault
           │   ├── quality [input]         ← JSON or Vault
           │   ├── synonyms [input]        ← JSON or Vault (can export YAML)
           │   ├── plurals [input]         ← JSON or Vault (can export YAML)
           │   ├── merge [input]           ← JSON or Vault (can export YAML)
           │   ├── suggest [paths] --vault ← Weird argument order!
           │   └── recommendations [input] ← Generates ops.yaml
           │
           └── vault/ (Filesystem Operations)
               └── cleanup-backups <vault> ← WRITE (deletes .bak files)
```

## Data Flow: Current Workflow

```
┌─────────────┐
│  User wants │
│  to clean   │
│  up tags    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ tagex init      │  ← Create .tagex/ config
│ /vault          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ tagex validate  │  ← Check config validity
│ /vault          │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ tagex stats /vault                       │  ← Understand current state
│                                          │
│  Output: 500 tags, 100 singletons (20%)│
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ tagex health /vault                      │  ← Get recommendations
│                                          │
│  Output: Health Score 60/100            │
│  - High singleton ratio                 │
│  - 50 plural variants                   │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ tagex analyze recommendations /vault    │  ← Generate operations
│         --export operations.yaml        │
│                                          │
│  Creates: operations.yaml               │
│  - 50 merge operations                  │
│  - 20 rename operations                 │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ $EDITOR operations.yaml                  │  ← Review & edit
│                                          │
│  User reviews, enables/disables ops     │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ tagex tags apply operations.yaml        │  ← Preview (dry-run)
│         --vault-path /vault             │
│                                          │
│  Shows what WOULD change                │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ tagex tags apply operations.yaml        │  ← Execute changes
│         --vault-path /vault --execute   │
│                                          │
│  Modifies vault files                   │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ tagex stats /vault                       │  ← Verify results
│                                          │
│  Output: 380 tags (-120), 40 singletons│
└──────────────────────────────────────────┘
```

## Problems Visualized

```
PROBLEM 1: Inconsistent Grouping
┌─────────────┐  ┌─────────────┐
│   init      │  │  validate   │  ← Should be in config/ group
└─────────────┘  └─────────────┘
       TOP LEVEL (exposed)

┌─────────────┐  ┌─────────────┐
│   stats     │  │   health    │  ← Should be in info/ group
└─────────────┘  └─────────────┘
       TOP LEVEL (exposed)

vs.

┌─────────────────────────────────┐
│        tags/ (grouped)          │
│  extract, rename, merge, etc.   │
└─────────────────────────────────┘


PROBLEM 2: Extract in Wrong Group
┌─────────────────────────────────┐
│          tags/                  │
├─────────────────────────────────┤
│ extract   ← READ-ONLY           │  Should be in info/
│ rename    ← WRITE               │
│ merge     ← WRITE               │
│ delete    ← WRITE               │
└─────────────────────────────────┘
     Mixed read/write in same group!


PROBLEM 3: Argument Inconsistencies
┌──────────────────────────────────────┐
│ tagex tags rename /vault old new     │  vault is positional
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ tagex tags apply ops.yaml            │  vault is --option
│       --vault-path /vault            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ tagex analyze suggest paths...       │  vault is --option
│       --vault-path /vault            │  but paths are positional??
└──────────────────────────────────────┘
```

## Proposed Solution: Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TAGEX CLI (v2.0)                             │
└─────────────────────────────────────────────────────────────────────┘
           │
           ├── QUICK ACCESS (Porcelain - Most Used)
           │   ├── init [vault]            ← Quick setup
           │   ├── stats [vault]           ← Quick info
           │   └── health [vault]          ← Quick health check
           │
           ├── config/ (Configuration)
           │   ├── validate [vault]        ← Check config
           │   ├── show [vault]            ← Display config
           │   └── edit [vault]            ← Open in $EDITOR
           │
           ├── analyze/ (Read-Only Analysis)
           │   ├── pairs [vault]           ← All accept vault OR json
           │   ├── quality [vault]
           │   ├── synonyms [vault] [--export ops.yaml]
           │   ├── plurals [vault] [--export ops.yaml]
           │   ├── merges [vault] [--export ops.yaml]
           │   ├── suggest [vault] [paths...] [--export ops.yaml]
           │   └── recommendations [vault] [--export ops.yaml]
           │
           ├── tag/ (Tag Write Operations)
           │   ├── export [vault]          ← Renamed from extract
           │   ├── rename <vault> <old> <new>
           │   ├── merge <vault> <src...> --into <target>
           │   ├── delete <vault> <tags...>
           │   ├── add <vault> <file> <tags...>  ← NEW
           │   ├── fix [vault]             ← Renamed from fix-duplicates
           │   └── apply [vault] <ops.yaml>
           │
           └── vault/ (Filesystem Operations)
               ├── cleanup [vault]         ← Renamed from cleanup-backups
               ├── backup [vault]          ← NEW
               └── verify [vault]          ← NEW
```

## New Data Flow: Improved Workflow

```
QUICK START (Common Path)
─────────────────────────

┌─────────────┐
│ tagex init  │  ← One command, fast setup
└──────┬──────┘
       │
       ▼
┌─────────────┐
│tagex health │  ← One command, see everything
└──────┬──────┘
       │
       ▼
┌────────────────────────────┐
│tagex analyze recommendations│  ← Generate ops file
│      --export ops.yaml      │
└──────┬─────────────────────┘
       │
       ▼
┌────────────────┐
│ edit ops.yaml  │  ← Review
└──────┬─────────┘
       │
       ▼
┌──────────────────────┐
│tagex tag apply ops.yaml│  ← Preview
└──────┬───────────────┘
       │
       ▼
┌───────────────────────────────┐
│tagex tag apply ops.yaml --execute│  ← Execute
└───────────────────────────────┘


ADVANCED (Specific Analysis)
────────────────────────────

┌─────────────────────────┐
│ tagex analyze synonyms  │
│       --export syn.yaml │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ tagex analyze plurals   │
│       --export plu.yaml │
└──────┬──────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Merge YAML files         │  ← User combines
│ cat syn.yaml plu.yaml    │
│   > combined.yaml        │
└──────┬───────────────────┘
       │
       ▼
┌─────────────────────────┐
│tagex tag apply combined.yaml│
│      --execute          │
└─────────────────────────┘


ONE-OFF OPERATIONS
──────────────────

┌──────────────────────────────┐
│ tagex tag rename tech technology│  ← Direct execution
└──────────────────────────────┘

┌──────────────────────────────┐
│ tagex tag merge ml ai        │
│       --into machine-learning│
└──────────────────────────────┘

┌──────────────────────────────┐
│ tagex tag delete spam junk   │
└──────────────────────────────┘
```

## Command Relationships (Semantic Map)

```
                    ┌────────────────┐
                    │  Obsidian      │
                    │  Vault         │
                    └───────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼───────┐
    │  .tagex/     │ │  .md files│ │  .bak files  │
    │  config/     │ │  with tags│ │  (backups)   │
    └───────┬──────┘ └─────┬─────┘ └──────┬───────┘
            │               │               │
            │               │               │
    ┌───────▼──────────────▼───────────────▼───────┐
    │            TAGEX COMMANDS                    │
    └──────────────────┬───────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐  ┌────▼────┐  ┌─────▼─────┐
    │ READ    │  │ ANALYZE │  │  WRITE    │
    │         │  │         │  │           │
    │ stats   │  │ synonyms│  │ rename    │
    │ health  │  │ plurals │  │ merge     │
    │ export  │  │ merges  │  │ delete    │
    │         │  │ suggest │  │ add       │
    │         │  │ recomm. │  │ fix       │
    │         │  │         │  │ apply     │
    └─────────┘  └────┬────┘  └─────▲─────┘
                      │              │
                      │   ┌──────────┤
                      └───▼──────┐   │
                          │ops.yaml│ │
                          │(YAML)  │ │
                          └────────┴─┘
                    User reviews & edits
```

## Command Capabilities Matrix

```
┌────────────────┬──────┬───────┬────────┬────────┬──────────┐
│ Command        │ Read │ Write │ Export │ Vault  │ JSON/In  │
│                │ Only │ Files │ YAML   │ Req'd  │ Accepts  │
├────────────────┼──────┼───────┼────────┼────────┼──────────┤
│ init           │      │  ✓    │        │  opt   │          │
│ stats          │  ✓   │       │  ✓     │  opt   │  ✓       │
│ health         │  ✓   │       │        │  opt   │  ✓       │
├────────────────┼──────┼───────┼────────┼────────┼──────────┤
│ config validate│  ✓   │       │        │  opt   │          │
│ config show    │  ✓   │       │        │  opt   │          │
│ config edit    │      │  ✓    │        │  opt   │          │
├────────────────┼──────┼───────┼────────┼────────┼──────────┤
│ tag export     │  ✓   │       │  ✓     │  opt   │          │
│ tag rename     │      │  ✓    │        │  req   │          │
│ tag merge      │      │  ✓    │        │  req   │          │
│ tag delete     │      │  ✓    │        │  req   │          │
│ tag add        │      │  ✓    │        │  req   │          │
│ tag fix        │      │  ✓    │        │  opt   │          │
│ tag apply      │      │  ✓    │        │  opt   │  YAML    │
├────────────────┼──────┼───────┼────────┼────────┼──────────┤
│ analyze pairs  │  ✓   │       │        │  opt   │  ✓       │
│ analyze quality│  ✓   │       │  ✓     │  opt   │  ✓       │
│ analyze syn..  │  ✓   │       │  ✓     │  opt   │  ✓       │
│ analyze plur.. │  ✓   │       │  ✓     │  opt   │  ✓       │
│ analyze merge  │  ✓   │       │  ✓     │  opt   │  ✓       │
│ analyze sugg.. │  ✓   │       │  ✓     │  req   │          │
│ analyze recomm │  ✓   │       │  ✓     │  opt   │  ✓       │
├────────────────┼──────┼───────┼────────┼────────┼──────────┤
│ vault cleanup  │      │  ✓    │        │  req   │          │
│ vault backup   │  ✓   │  ✓    │        │  req   │          │
│ vault verify   │  ✓   │       │        │  req   │          │
└────────────────┴──────┴───────┴────────┴────────┴──────────┘

Legend:
  Read Only  = Only reads files, safe to run anytime
  Write Files = Modifies markdown files or creates backups
  Export YAML = Can generate operations.yaml file
  Vault Req'd = Whether vault path is required vs. optional
  JSON/In Accepts = Can accept JSON input instead of vault
```

## Safety Levels

```
LEVEL 1: ALWAYS SAFE (Read-Only)
┌────────────────────────────────┐
│ • stats                        │
│ • health                       │
│ • config validate, show        │
│ • tag export                   │
│ • ALL analyze commands         │
└────────────────────────────────┘
   No risk, run anytime


LEVEL 2: SAFE WITH PREVIEW (Dry-Run Default)
┌────────────────────────────────┐
│ • tag rename (without --execute)│
│ • tag merge (without --execute)│
│ • tag delete (without --execute)│
│ • tag fix (without --execute)  │
│ • tag apply (without --execute)│
│ • vault cleanup (without --execute)│
└────────────────────────────────┘
   Shows changes but doesn't apply


LEVEL 3: WRITES FILES (Needs --execute)
┌────────────────────────────────┐
│ • tag rename --execute         │
│ • tag merge --execute          │
│ • tag delete --execute         │
│ • tag add --execute            │
│ • tag fix --execute            │
│ • tag apply --execute          │
│ • vault cleanup --execute      │
└────────────────────────────────┘
   Creates .bak backups before changes


LEVEL 4: CONFIGURATION (Low Risk)
┌────────────────────────────────┐
│ • init                         │
│ • config edit                  │
│ • vault backup                 │
└────────────────────────────────┘
   Only modifies .tagex/ or creates backups
```

## Tab Completion Tree

```
tagex <TAB>
├── init
├── stats
├── health
├── config <TAB>
│   ├── validate
│   ├── show
│   └── edit
├── tag <TAB>
│   ├── export
│   ├── rename
│   ├── merge
│   ├── delete
│   ├── add
│   ├── fix
│   └── apply
├── analyze <TAB>
│   ├── pairs
│   ├── quality
│   ├── synonyms
│   ├── plurals
│   ├── merges
│   ├── suggest
│   └── recommendations
└── vault <TAB>
    ├── cleanup
    ├── backup
    └── verify
```

## Summary

The proposed structure:

1. **Keeps common commands short**: `init`, `stats`, `health`
2. **Groups related operations**: `config/`, `tag/`, `analyze/`, `vault/`
3. **Clear read/write separation**: analyze/* is read-only, tag/* writes
4. **Consistent arguments**: all default to cwd, predictable order
5. **Safety by default**: writes require `--execute` flag
6. **Better discovery**: logical grouping + tab completion
