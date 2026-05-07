---
name: feedback_testing
description: Key testing feedback and patterns for this project
type: feedback
---

Unit tests MUST mock ChatLlamaCpp (llm_service.py) entirely since calling Ollama API is not allowed in unit tests. Mock LLMService.generate() and LLMService.generate_with_context() methods.

**Why:** External API calls to Ollama are slow, non-deterministic, and require network. CI cannot depend on external services.

**How to apply:** In test_chain.py, always mock LLMService class. In test_memory_manager.py, mock ChatMessageHistory. Use unittest.mock.patch decorators.
