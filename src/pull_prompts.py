"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def _get_langsmith_config() -> dict:
    """Monta parâmetros opcionais de conexão com o LangSmith."""
    config = {
        "api_url": os.getenv("LANGSMITH_ENDPOINT"),
        "api_key": os.getenv("LANGSMITH_API_KEY"),
    }
    return {key: value for key, value in config.items() if value}


def _extract_message_template(message: object) -> Optional[Tuple[str, str]]:
    """Extrai (role, template) de uma mensagem do prompt quando possível."""
    role = getattr(message, "role", None) or getattr(message, "type", None)
    prompt = getattr(message, "prompt", None)
    template = getattr(prompt, "template", None) if prompt is not None else None

    if role and template:
        return str(role), str(template)

    template = getattr(message, "template", None)
    if role and template:
        return str(role), str(template)

    return None


def _serialize_prompt(prompt: object, source_name: str) -> dict:
    """Serializa o prompt puxado do Hub para um YAML local simples."""
    system_prompt = ""
    user_prompt = ""
    messages = []

    for message in getattr(prompt, "messages", []) or []:
        extracted = _extract_message_template(message)
        if not extracted:
            continue

        role, template = extracted
        messages.append({"role": role, "template": template})
        normalized_role = role.lower()

        if normalized_role in {"system", "systemmessageprompttemplate"} and not system_prompt:
            system_prompt = template
        elif normalized_role in {"human", "user", "humanmessageprompttemplate"} and not user_prompt:
            user_prompt = template

    return {
        source_name: {
            "description": f"Prompt puxado de {source_name} no LangSmith Hub",
            "version": "v1",
            "source": source_name,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "messages": messages,
            "raw": prompt.to_json() if hasattr(prompt, "to_json") else str(prompt),
        }
    }


def pull_prompts_from_langsmith():
    """Faz pull do prompt inicial e salva em prompts/bug_to_user_story_v1.yml."""
    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"

    print_section_header("PULL DE PROMPTS")
    print(f"Buscando prompt: {prompt_name}")

    config = _get_langsmith_config()
    prompt = hub.pull(prompt_name, **config)
    prompt_data = _serialize_prompt(prompt, "bug_to_user_story_v1")

    if not save_yaml(prompt_data, str(output_path)):
        raise RuntimeError(f"Falha ao salvar prompt em {output_path}")

    print(f"✓ Prompt salvo em: {output_path}")
    return output_path


def main():
    """Função principal"""
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        pull_prompts_from_langsmith()
        return 0
    except Exception as exc:
        print(f"❌ Erro ao fazer pull do prompt: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
