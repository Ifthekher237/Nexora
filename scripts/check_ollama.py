"""Check whether the local Ollama server is reachable."""

from __future__ import annotations

import os
import sys

import requests


OLLAMA_URL = os.getenv("NEXORA_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def main() -> int:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Ollama is not reachable at {OLLAMA_URL}.")
        print("Start Ollama with `ollama serve` or open the Ollama desktop app.")
        print(f"Details: {exc}")
        return 1

    data = response.json()
    models = [model.get("name") for model in data.get("models", []) if model.get("name")]

    print(f"Ollama is reachable at {OLLAMA_URL}.")
    if models:
        print("Installed local models:")
        for model in models:
            print(f"- {model}")
    else:
        print("No local Ollama models were reported.")
        print("Install a configured model, for example: `ollama pull llama3.1:8b`")

    return 0


if __name__ == "__main__":
    sys.exit(main())
