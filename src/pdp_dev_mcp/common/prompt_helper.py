from pathlib import Path


def load_prompt_content(prompt_path: Path | str) -> str:
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Could not find prompt file at {prompt_path}"
    except Exception as e:
        return f"Error loading prompt: {str(e)}"
