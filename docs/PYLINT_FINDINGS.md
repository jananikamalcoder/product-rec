# Pylint Analysis Report

## Summary

Pylint was run on the `src/` directory to identify code quality issues. This document summarizes the findings and which issues were addressed.

**Current Score: 9.98/10**

## Issues Fixed

### Critical/Errors

| Issue | Code | File | Description | Status |
|-------|------|------|-------------|--------|
| Missing method | E1101 | `agent_tools.py:925` | `PersonalizationAgent` had no `get_personalized_recommendation` member | ✅ Fixed |

### High Priority

| Issue | Code | File | Description | Status |
|-------|------|------|-------------|--------|
| Missing `from e` | W0707 | `agent_tools.py:26,657,1050` | Re-raise without exception chaining | ✅ Fixed |
| Missing `from e` | W0707 | `search_tools.py:22` | Re-raise without exception chaining | ✅ Fixed |
| Missing `from e` | W0707 | `product_search_agent.py:44` | Re-raise without exception chaining | ✅ Fixed |
| Unused import | W0611 | `load_products.py:5` | Unused `Settings` from chromadb.config | ✅ Fixed |
| Unused import | W0611 | `personalization_agent.py:14` | Unused `asyncio` | ✅ Fixed |
| Unused import | W0611 | `personalization_agent.py:30` | Unused `UserMemory` | ✅ Fixed |
| Unused import | W0611 | `search_tools.py:7` | Unused `List` from typing | ✅ Fixed |
| Unused import | W0611 | `product_search_agent.py:16` | Unused `List` from typing | ✅ Fixed |
| Unused variable | W0612 | `load_products.py:34` | Unused variable `idx` | ✅ Fixed |
| Unused variable | W0612 | `visual_formatting_tool.py:364` | Unused variable `ratings` | ✅ Fixed |
| Unused variable | W0612 | `visual_formatting_tool.py:424` | Unused variable `max_bucket` | ✅ Fixed |
| Missing encoding | W1514 | `memory.py:53,62` | `read_text()`/`write_text()` without encoding | ✅ Fixed |

### Medium Priority (Import Order)

| Issue | Code | File | Description | Status |
|-------|------|------|-------------|--------|
| Import order | C0411 | `load_products.py` | Standard imports after third-party | ✅ Fixed |

## Issues Not Addressed (Intentional/Low Priority)

### Singleton Pattern (Expected)

| Issue | Code | Files | Reason |
|-------|------|-------|--------|
| Global statement | W0603 | Multiple | Required for singleton pattern |
| Constant naming | C0103 | Multiple | `_search_engine`, `_visual_formatting_tool`, etc. are intentionally lowercase |

### Broad Exception Catching (Intentional)

| Issue | Code | Files | Reason |
|-------|------|-------|--------|
| Broad exception | W0718 | Multiple | Intentional for error handling in tool functions |

### Import Outside Toplevel (Intentional)

| Issue | Code | Files | Reason |
|-------|------|-------|--------|
| Import outside toplevel | C0415 | Multiple | Lazy imports to avoid circular dependencies and improve startup time |

### Code Complexity (Refactoring Suggestions)

| Issue | Code | Description | Recommendation |
|-------|------|-------------|----------------|
| Too many arguments | R0913/R0917 | Functions with >5 parameters | Consider using dataclasses/config objects in future |
| Too many branches | R0912 | Functions with >12 branches | Could be refactored but functional as-is |
| Too many locals | R0914 | Functions with >15 local variables | Could be refactored but functional as-is |
| Too many statements | R0915 | Functions with >50 statements | Could be split into smaller functions |
| Too many lines | C0302 | `agent_tools.py` has >1000 lines | Could be split into separate modules |

### Style Issues (Fixed)

| Issue | Code | Description | Status |
|-------|------|-------------|--------|
| Line too long | C0301 | Lines >100 characters | ✅ Fixed (27 occurrences) |
| Wrong import position | C0413 | Imports after code | ✅ Fixed |
| Disallowed name | C0104 | Variable named `bar` | ✅ Fixed |
| F-string without interpolation | W1309 | F-strings with no variables | ✅ Fixed |
| Unnecessary else after return | R1705 | `elif`/`else` after `return` | ✅ Fixed |

### Style Issues (Remaining - Intentional)

| Issue | Code | Description | Reason |
|-------|------|-------------|--------|
| Line too long | C0301 | 3 lines in LLM instruction strings | Intentional for LLM readability |

## How to Run Pylint

```bash
# Install pylint (if not already installed)
pip install -e ".[dev]"

# Run on entire src directory
pylint src/

# Run on specific file
pylint src/agents/memory.py

# Run with specific checks only
pylint src/ --disable=all --enable=E,W

# Generate report
pylint src/ --output-format=json > pylint_report.json
```

## Configuration

To customize pylint behavior, create a `.pylintrc` file or add to `pyproject.toml`:

```toml
[tool.pylint.messages_control]
disable = [
    "C0103",  # Invalid name (for singletons)
    "W0603",  # Global statement (for singletons)
    "R0913",  # Too many arguments (tool functions need many params)
]

[tool.pylint.format]
max-line-length = 120
```
