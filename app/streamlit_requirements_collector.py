import os
import streamlit as st
import openai
import json
from copy import deepcopy

# ✅ New OpenAI Client API (v1.0+)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StreamlitRequirementsCollector:
    def __init__(self):
        if not client.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        self.schema_template = {
            "project_name": None,
            "project_description": None,
            "functional_requirements": [],
            "non_functional_requirements": [],
            "preferred_tech_stack": None,
            "target_platform": None,
            "constraints": [],
            "suggested_tech_stack": None,
        }

        if 'requirements' not in st.session_state:
            st.session_state.requirements = deepcopy(self.schema_template)
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = [
                {"role": "system", "content": self._system_prompt()}
            ]
        if 'final_summary' not in st.session_state:
            st.session_state.final_summary = ""

    def _system_prompt(self) -> str:
        return (
            "You are a professional software analyst helping clients define complete and clear software project requirements.\n"
            "Your job is to collect:\n"
            "- Functional requirements (what the system should do)\n"
            "- Non-functional requirements (performance, scalability, security, etc)\n"
            "- Preferred tech stack (languages, frameworks)\n"
            "- Target platform (web, mobile, desktop, etc)\n"
            "- Any constraints or preferences (budget, time, legal, etc)\n"
            "\n"
            "At the end, analyze the project and suggest a suitable tech stack based on the gathered information.\n"
            "Ask questions until you are confident that the requirements are complete. Then summarize the requirements and tech stack recommendation, and ask the client to confirm."
        )

    def _summarize_state(self) -> str:
        return "\n".join([f"{key}: {value}" for key, value in st.session_state.requirements.items()])

    def _build_user_prompt(self) -> str:
        return (
            f"Current gathered info:\n{self._summarize_state()}\n\n"
            "What should you ask next to complete the requirements collection?"
        )

    def _call_openai(self) -> str:
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=st.session_state.chat_history,
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            return "⚠️ OpenAI failed to respond."

    def interact(self):
        st.title("🧠 AI Requirements Collector with Tech Stack Suggestion")
        user_input = st.text_input("💬 Enter your reply or idea", key="user_input")

        if st.button("Send"):
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "user", "content": self._build_user_prompt()})
            reply = self._call_openai()
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.session_state.last_reply = reply

        if 'last_reply' in st.session_state:
            st.markdown("### 🤖 Agent Reply")
            st.markdown(st.session_state.last_reply)

        if st.button("✅ Confirm & Export JSON"):
            st.session_state.final_summary = st.session_state.last_reply
            export_data = {
                "requirements": st.session_state.requirements,
                "final_summary": st.session_state.final_summary
            }
            json_data = json.dumps(export_data, indent=2)
            st.download_button(
                "📁 Download Requirements JSON",
                json_data,
                file_name="requirements_summary.json",
                mime="application/json"
            )

if __name__ == "__main__":
    collector = StreamlitRequirementsCollector()
    collector.interact()
