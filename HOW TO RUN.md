# How to Run

This guide explains how to set up and run the project using `uv`.

## Prerequisites

- Python 3.x
- [uv](https://github.com/astral-sh/uv) installed

## Installation and Setup

Follow these steps to configure your environment:

### 1. Create a virtual environment

```bash
uv venv
```

### 2. Activate the virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Sync dependencies

```bash
uv sync
```

### 4. Install Chromium browser for Playwright

```bash
playwright install chromium
```

## Running the Project

After completing the setup, run the project with:

```bash
uv run main.py
```

---

**Note:** Make sure all installation steps are completed before running the project.

