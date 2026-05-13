"""CLI interface for conversation bot."""

import os
import sys
from pathlib import Path
from typing import Optional

from langchain_core.messages import AIMessage,SystemMessage
from langchain_openai import ChatOpenAI

from .agent.conversation_agent import ConversationAgent
from .session_manager import SessionManager
from .short_term_memory import ShortTermMemory


class CLI:
    """Command-line interface for conversation bot."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        """Initialize CLI.

        Args:
            storage_dir: Directory for session storage.
        """
        self._storage_dir = storage_dir or Path("sessions")
        self._session_manager = SessionManager(self._storage_dir)
        self._agent: Optional[ConversationAgent] = None
        self._current_memory: Optional[ShortTermMemory] = None
        self._setup_llm()
        self._ensure_session()

    def _setup_llm(self) -> None:
        """Setup LLM service."""
        self._llm = ChatOpenAI(
            model="qwen3.5",
            base_url="http://127.0.0.1:1234/v1",
            api_key="dummy",
            temperature=0.7,
        )

    def _llm_call(self, messages: list) -> AIMessage:
        """Call LLM with messages.

        Args:
            messages: List of messages.

        Returns:
            AI response message.
        """
        response = self._llm.invoke(messages)
        return response

    def _ensure_session(self) -> None:
        """Ensure there's an active session."""
        current_id = self._session_manager.current_session_id
        if current_id is None:
            session = self._session_manager.create_session()
            current_id = session.session_id

        self._current_memory = self._session_manager.load_memory(current_id)
        if self._current_memory is None:
            self._current_memory = ShortTermMemory(session_id=current_id)

        self._agent = ConversationAgent(
            llm_callable=self._llm_call,
            short_term_memory=self._current_memory,
        )

    def run(self) -> None:
        """Run the CLI main loop."""
        self._ensure_session()
        print("Conversation Bot (type /help for commands)")
        print(f"Session: {self._session_manager.current_session_id}")

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    response = self._handle_command(user_input)
                    if response is not None:
                        print(f"Bot: {response}")
                    if response == "exit":
                        break
                else:
                    response = self._agent.process(user_input)
                    print(f"Bot: {response}")

            except KeyboardInterrupt:
                print("\nExiting...")
                self._save_current_session()
                break
            except Exception as e:
                print(f"Error: {e}")

    def _handle_command(self, command: str) -> Optional[str]:
        """Handle CLI commands.

        Args:
            command: The command string.

        Returns:
            Response string or None for session switch.
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/new":
            self._save_current_session()
            name = arg if arg else None
            if name and self._session_manager.find_session_by_name(name):
                print(f"会话名 '{name}' 已存在，请选择操作:")
                print("  1. 覆盖 (删除旧会话)")
                print("  2. 重命名")
                print("  3. 取消")
                choice = input("请输入选项 (1/2/3): ").strip()
                if choice == "1":
                    old_session_id = self._session_manager.find_session_by_name(name)
                    if old_session_id:
                        self._session_manager.delete_session(old_session_id)
                elif choice == "2":
                    name = input("请输入新名称: ").strip()
                    if not name:
                        return "已取消"
                elif choice == "3":
                    return "已取消"
                else:
                    return "无效选项，已取消"
            session = self._session_manager.create_session(name)
            self._current_memory = ShortTermMemory(session_id=session.session_id)
            self._current_memory._session_name = session.name
            self._agent = ConversationAgent(
                llm_callable=self._llm_call,
                short_term_memory=self._current_memory,
            )
            print(f"Created new session: {session.session_id}")
            return None

        elif cmd == "/switch":
            if not arg:
                return "Usage: /switch <session_id>"
            self._save_current_session()
            # Try to find session_id by name first if switch_session returns False with name
            session_id = self._session_manager.find_session_by_name(arg) or arg
            if self._session_manager.switch_session(session_id):
                self._current_memory = self._session_manager.load_memory(session_id)
                if self._current_memory is None:
                    self._current_memory = ShortTermMemory(session_id=session_id)
                self._current_memory._session_name = self._session_manager.get_session(session_id).name if self._session_manager.get_session(session_id) else arg
                self._agent = ConversationAgent(
                    llm_callable=self._llm_call,
                    short_term_memory=self._current_memory,
                )
                return None
            return f"Session not found: {arg}"

        elif cmd == "/sessions":
            sessions = self._session_manager.list_sessions()
            if not sessions:
                return "No sessions found."
            lines = ["Sessions:"]
            for s in sessions:
                current = " *" if s.session_id == self._session_manager.current_session_id else ""
                lines.append(f"  {s.session_id} - {s.name}{current}")
            return "\n".join(lines)

        elif cmd == "/delete":
            if not arg:
                return "Usage: /delete <session_id>"
            if self._session_manager.delete_session(arg):
                return f"Deleted session: {arg}"
            return f"Session not found: {arg}"

        elif cmd == "/exit":
            self._save_current_session()
            return "exit"

        elif cmd == "/rewind":
            if not arg or not arg.isdigit():
                return "Usage: /rewind <n>"
            n = int(arg)
            self._agent.rewind(n)
            return f"Rewound {n} message pair(s)"

        elif cmd == "/repeat":
            response = self._agent.repeat()
            return response if response else "Nothing to repeat"

        elif cmd == "/compact":
            if self._current_memory and len(self._current_memory.messages) > 1:
                summary = self._generate_summary()
                self._agent.compact(summary)
                return "Context compacted"
            return "Nothing to compact"

        elif cmd == "/context":
            return self._get_context_usage()

        elif cmd == "/help":
            return (
                "Commands:\n"
                "  /new <name>    - Create new session (name conflict: 覆盖/重命名/取消)\n"
                "  /switch <id>   - Switch to session\n"
                "  /sessions      - List all sessions\n"
                "  /delete <id>   - Delete session\n"
                "  /exit          - Save and exit\n"
                "  /rewind <n>    - Rewind n pairs\n"
                "  /repeat        - Repeat last response\n"
                "  /compact       - Compact context\n"
                "  /context       - Show context usage"
            )

        else:
            return f"Unknown command: {cmd}"

    def _generate_summary(self) -> str:
        """Generate summary of current conversation."""
        if self._current_memory is None:
            return ""
        messages = self._current_memory.get_messages()
        if len(messages) <= 1:
            return ""
        conversation_text = "\n".join(
            f"{type(m).__name__}: {m.content[:100]}" for m in messages[-10:]
        )
        prompt = f"简要总结以下对话的核心内容:\n{conversation_text}"
        try:
            response = self._llm.invoke([SystemMessage(content=prompt)])
            return response.content
        except Exception:
            return "Summary unavailable"

    def _get_context_usage(self) -> str:
        """Get current context usage information."""
        if self._agent is None:
            return "No active session"
        tokens = self._agent.token_count
        messages = self._agent.message_count
        return f"Tokens: ~{tokens} | Messages: {messages}"

    def _save_current_session(self) -> None:
        """Save current session memory."""
        if self._current_memory is not None and self._agent is not None:
            self._session_manager.save_memory(self._current_memory)


def main() -> None:
    """Main entry point."""
    storage_dir = Path("sessions")
    cli = CLI(storage_dir)
    cli.run()


if __name__ == "__main__":
    main()