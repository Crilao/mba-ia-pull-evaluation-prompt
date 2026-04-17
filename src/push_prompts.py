"""
Script to push optimized prompts to the LangSmith Prompt Hub.

This script:
1. Reads the optimized prompt from prompts/bug_to_user_story_v2.yml
2. Validates the prompt structure
3. Pushes it as a public prompt to LangSmith
4. Adds metadata through tags, description, and README content
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate

from utils import check_env_vars, load_yaml, print_section_header

load_dotenv()


PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"


def _get_prompt_entry(prompt_file_data: dict) -> tuple[str, dict]:
    """
    Extract the prompt name and payload from the YAML structure.

    The file can contain either:
    - a single top-level key: bug_to_user_story_v2: {...}
    - or a direct payload with system_prompt/user_prompt fields
    """
    if not isinstance(prompt_file_data, dict) or not prompt_file_data:
        raise ValueError("Invalid YAML structure: expected a non-empty dictionary.")

    if len(prompt_file_data) == 1:
        prompt_name, prompt_content = next(iter(prompt_file_data.items()))
        if isinstance(prompt_content, dict):
            return prompt_name, prompt_content

    if "system_prompt" in prompt_file_data or "user_prompt" in prompt_file_data:
        prompt_name = prompt_file_data.get("name") or "bug_to_user_story_v2"
        return prompt_name, prompt_file_data

    raise ValueError(
        "Could not identify the prompt payload in the YAML. "
        "Expected a single top-level key or a direct prompt dictionary."
    )


def _build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Build a serializable ChatPromptTemplate from the YAML content."""
    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt = prompt_data.get("user_prompt", "").strip()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

    # Helpful for tracing and future prompt management.
    prompt.metadata = {
        "version": prompt_data.get("version", "v2"),
        "created_at": prompt_data.get("created_at", ""),
        "tags": prompt_data.get("tags", []),
        "techniques_applied": prompt_data.get("techniques_applied", []),
    }

    return prompt


def validate_prompt(prompt_data: dict) -> tuple[bool, list[str]]:
    """Validate the basic prompt structure before publishing."""
    errors: list[str] = []

    required_fields = ["description", "system_prompt", "user_prompt", "version"]
    for field in required_fields:
        value = prompt_data.get(field, "")
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Missing or empty required field: {field}")

    system_prompt = prompt_data.get("system_prompt", "")
    user_prompt = prompt_data.get("user_prompt", "")

    tags = prompt_data.get("tags", [])
    if not isinstance(tags, list) or not tags:
        errors.append("tags must be a non-empty list")

    return len(errors) == 0, errors


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Push the optimized prompt to the LangSmith Hub as a public prompt.
    """
    try:
        prompt = _build_chat_prompt(prompt_data)

        description = prompt_data.get("description", "").strip()
        tags = list(prompt_data.get("tags", []))

        api_key = os.getenv("LANGSMITH_API_KEY")
        api_url = os.getenv("LANGSMITH_ENDPOINT")

        print(f"   Publishing prompt '{prompt_name}' to LangSmith Hub...")

        url = hub.push(
            prompt_name,
            prompt,
            api_url=api_url,
            api_key=api_key,
            new_repo_is_public=True,
            new_repo_description=description or None,
            tags=tags,
        )

        print(f"   ✓ Published successfully: {url}")
        return True

    except Exception as e:
        print(f"   ❌ Failed to publish prompt '{prompt_name}': {e}")
        return False


def main() -> int:
    """Main entry point."""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    prompt_path = Path(PROMPT_FILE)
    if not prompt_path.exists():
        print(f"❌ File not found: {prompt_path}")
        return 1

    prompt_file_data = load_yaml(str(prompt_path))
    if not prompt_file_data:
        print("❌ Could not load the YAML prompt file")
        return 1

    try:
        prompt_name, prompt_data = _get_prompt_entry(prompt_file_data)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt validation failed:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB is not configured in .env")
        return 1

    prompt_identifier = f"{username}/{prompt_name}"
    version = prompt_data.get("version", "v2")

    print(f"Local prompt: {prompt_path}")
    print(f"Hub prompt: {prompt_identifier}")
    print(f"Version: {version}")
    print("Visibility: public\n")

    success = push_prompt_to_langsmith(prompt_identifier, prompt_data)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
