"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompts = load_prompts(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
        prompt = prompts["bug_to_user_story_v2"]
        assert "system_prompt" in prompt
        assert isinstance(prompt["system_prompt"], str)
        assert prompt["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompts = load_prompts(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
        system_prompt = prompts["bug_to_user_story_v2"]["system_prompt"]
        assert re.search(r"você é|voce é|you are", system_prompt, re.IGNORECASE)
        assert re.search(r"product manager|pm sênior|product manager sênior", system_prompt, re.IGNORECASE)

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompts = load_prompts(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
        system_prompt = prompts["bug_to_user_story_v2"]["system_prompt"]
        assert re.search(r"markdown|user story", system_prompt, re.IGNORECASE)

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompts = load_prompts(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
        system_prompt = prompts["bug_to_user_story_v2"]["system_prompt"]
        assert "Exemplo 1" in system_prompt
        assert "Exemplo 2" in system_prompt
        assert "Entrada (bug report)" in system_prompt
        assert "Saída esperada" in system_prompt

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "[TODO]" not in content
        assert "TODO" not in content

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompts = load_prompts(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
        techniques = prompts["bug_to_user_story_v2"].get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
