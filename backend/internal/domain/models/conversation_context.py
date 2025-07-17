from dataclasses import dataclass
from typing import List, Optional


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
        
        return "\n".join(self.relevant_documents)
    
    def add_to_history(self, message: str) -> None:
        """Add a message to the conversation history."""
        if self.conversation_history is None:
            self.conversation_history = []
        self.conversation_history.append(message)