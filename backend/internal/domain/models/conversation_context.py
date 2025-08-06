from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ConversationContext:
    """Domain model representing the context of a conversation."""
    user_query: str
    relevant_documents: List[str]
    conversation_history: Optional[List[str]] = None

    def has_relevant_context(self) -> bool:
        """Check if there are relevant documents to provide context."""
        return bool(self.relevant_documents)

    def get_context_summary(self) -> str:
        """Get a summary of the relevant context for the conversation."""
        if not self.has_relevant_context():
            return ""

        summary = ""
        for document in self.relevant_documents:
            document = document.replace("\n", " ")
            summary += f"\n - '{document}'"

        return summary

    def get_conversation_history(self) -> Tuple[str, int]:
        """Get the conversation history."""
        if self.conversation_history is None:
            return "", 0
        return "- " + "\n - ".join(self.conversation_history), len(self.conversation_history)
