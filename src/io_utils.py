# -*- coding: utf-8 -*-
"""
I/O utilities for LinkedIn ESG Sentiment Analysis pipeline.
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import Any


def save_json(data: Any, path: str | Path, **kwargs) -> Path:
    """Save data as JSON file. Returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, **kwargs)
    return path


def load_json(path: str | Path) -> Any:
    """Load data from JSON file."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv(df: pd.DataFrame, path: str | Path, **kwargs) -> Path:
    """Save DataFrame as CSV. Returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", **kwargs)
    return path


def load_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load CSV into DataFrame."""
    path = Path(path)
    return pd.read_csv(path, encoding="utf-8", **kwargs)


def list_html_files(folder: str | Path) -> list[Path]:
    """List all .html and .htm files in a directory (sorted)."""
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.suffix.lower() in {".html", ".htm"}])


def list_html_files_recursive(folder: str | Path) -> list[Path]:
    """List all .html and .htm files recursively."""
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(folder.rglob("*.[hH][tT][mM][lL]")) + sorted(folder.rglob("*.[hH][tT][mM]"))
