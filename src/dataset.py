"""Utilitários para carregamento do dataset de avaliação."""

import json
from typing import Any, Dict, List


def load_bug_dataset(jsonl_path: str = "datasets/bug_to_user_story.jsonl") -> List[Dict[str, Any]]:
    """Carrega dataset JSONL com entradas no formato LangSmith examples."""
    examples: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples
