from typing import List


class PromptBuilder:
    def __init__(self, task_description: str):
        self.task_description = task_description

    def build_with_context(self, context: List[str], question: str) -> str:
        """Builds a prompt with context."""
        
        context = "\n".join(context)

        return (f"{self.task_description}"
                f""
                f"Kontext: {context}"
                f""
                f"Frage: {question}")
