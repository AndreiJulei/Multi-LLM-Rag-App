"""
Counsel of AI — Streamlit Frontend.
Fully dynamic: models come from the backend; nothing is hardcoded.
"""

import streamlit as st
from typing import List, Dict, Optional
from api_client import APIClient


class CounselOfAIApp:
    def __init__(self, api_client: APIClient):
        self.api = api_client
        self._init_state()

    # Session
    @staticmethod
    def _init_state():
        defaults = {
            "authenticated": False,
            "token": None,
            "is_admin": False,
            "messages": [],
            "active_collection_id": None,
            "selected_mode": "debate",
            "view": "chat",
            
            # vote tracking
            "last_debate_chat_id": None,   # chat_id of most recent debate
            "pending_vote": False,          # True = last debate awaits a verdict
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    # Sidebar
    def render_sidebar(self):
        with st.sidebar:
            st.title("The Counsel Hall")
            if not st.session_state["authenticated"]:
                tab_login, tab_register = st.tabs(["Login", "Register"])
                with tab_login:
                    self._render_login_form()
                with tab_register:
                    self._render_register_form()
            else:
                self._render_authenticated_sidebar()

    def _render_login_form(self):
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted and email and password:
            res = self.api.login(email, password)
            if res.status_code == 200:
                token = res.json()["access_token"]
                st.session_state["token"] = token
                st.session_state["authenticated"] = True

                # Fetch is_admin immediately so the Admin Settings button appears
                me_res = self.api.get_me(token)
                if me_res.status_code == 200:
                    st.session_state["is_admin"] = me_res.json().get("is_admin", False)
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    def _render_register_form(self):
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Register")
        if submitted and email and password:
            res = self.api.register(email, password)
            if res.status_code == 200:
                st.success("Registered! Please log in.")
            else:
                detail = res.json().get("detail", "Registration failed")
                st.error(detail)

    def _render_authenticated_sidebar(self):
        st.success("Connected to the Counsel")
        token = st.session_state["token"]

        # navigation
        if st.button("Chat", use_container_width=True):
            st.session_state["view"] = "chat"
            st.rerun()

        if st.session_state.get("is_admin"):
            if st.button("⚙️ Admin Settings", use_container_width=True):
                st.session_state["view"] = "admin"
                st.rerun()

        st.divider()

        # collection
        st.subheader("Your Libraries")
        res = self.api.get_collections(token)
        if res.status_code == 200:
            collections = res.json()
            if collections:
                col_map = {c["name"]: c["id"] for c in collections}
                selected = st.selectbox("Select a Collection", list(col_map.keys()))
                if selected:
                    st.session_state["active_collection_id"] = col_map[selected]
            else:
                st.info("No collections yet — create one below.")

        with st.expander("New Collection"):
            new_name = st.text_input("Name", key="new_col_name")
            if st.button("Create") and new_name:
                self.api.create_collection(new_name, token)
                st.toast(f"Collection '{new_name}' created!")
                st.rerun()

        with st.expander("Upload Document"):
            uploaded_file = st.file_uploader(
                "Upload PDF / TXT / CSV / XML", type=["pdf", "txt", "csv", "xml"]
            )

            if st.button("Index Document") and uploaded_file:
                col_id = st.session_state.get("active_collection_id")
                if not col_id:
                    st.warning("Select a collection first!")
                else:
                    self.api.upload_document(
                        uploaded_file.name, uploaded_file.getvalue(), col_id, token
                    )
                    st.toast("Document indexed!")

        st.divider()

        # model selector
        st.subheader("Who Should Answer?")
        models_res = self.api.get_active_models(token)
        active_models: List[str] = []
        if models_res.status_code == 200:
            active_models = models_res.json().get("active_models", [])

        options = ["debate"] + active_models
        labels: Dict[str, str] = {
            "debate": "Full Counsel (all active models)",
            **{m: f"{m}" for m in active_models},
        }
        choice = st.radio(
            "mode", options=options,
            format_func=lambda x: labels.get(x, x),
            label_visibility="collapsed",
        )
        st.session_state["selected_mode"] = choice

        # blind vote button
        if st.session_state.get("pending_vote") and st.session_state.get("last_debate_chat_id"):
            st.divider()
            st.caption("The Counsel has spoken — let them judge the best answer!")
            if st.button("Let the Counsel Vote", type="primary", use_container_width=True):
                with st.spinner("The Counsel is deliberating on the verdict…"):
                    vote_res = self.api.blind_vote(st.session_state["last_debate_chat_id"], token)
                if vote_res.status_code == 200:
                    vdata = vote_res.json()
                    winning_model = vdata.get("winning_model", "Unknown")
                    winner_answer = vdata.get("winner_answer", "")
                    votes = vdata.get("votes", {})
                    vote_summary = ", ".join(
                        f"{m}: {v} vote{'s' if v != 1 else ''}"
                        for m, v in sorted(votes.items(), key=lambda x: -x[1])
                    )
                    st.session_state["messages"].append({
                        "role": "verdict",
                        "winning_model": winning_model,
                        "winner_answer": winner_answer,
                        "vote_summary": vote_summary,
                    })
                    st.session_state["pending_vote"] = False
                    st.rerun()
                else:
                    err = vote_res.json().get("detail", "Vote failed")
                    st.error(f"Vote error: {err}")

        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Chat
    def render_chat_interface(self):
        st.header("The Debate Arena")

        for msg in st.session_state["messages"]:
            role = msg["role"]
            if role == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            elif role == "assistant":
                with st.chat_message("assistant"):
                    responses: dict = msg.get("responses", {})
                    if len(responses) > 1:
                        # Multi-model debate — no user vote buttons
                        cols = st.columns(len(responses))
                        for i, (model_name, answer) in enumerate(responses.items()):
                            with cols[i]:
                                st.caption(f"🏛️ **{model_name}**")
                                st.info(answer)
                    elif responses:
                        model_name = list(responses.keys())[0]
                        st.caption(f"🤖 **{model_name}**")
                        st.write(responses[model_name])
            elif role == "verdict":
                with st.chat_message("assistant", avatar="⚖️"):
                    st.success("**The Counsel's Verdict**")
                    st.write(f"**Winner:** `{msg['winning_model']}`")
                    st.write(f"**Vote tally:** {msg['vote_summary']}")
                    st.markdown("---")
                    st.write(msg["winner_answer"])

        if prompt := st.chat_input("Summon the Counsel…"):
            col_id = st.session_state.get("active_collection_id")
            if not col_id:
                st.warning("Please select a Library (Collection) from the sidebar first!")
                return

            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            mode = st.session_state.get("selected_mode", "debate")

            with st.spinner("The Counsel is deliberating…"):
                response = self.api.query_counsel(
                    col_id, prompt, mode, st.session_state["token"]
                )

            if response.status_code == 200:
                data = response.json()
                responses = data.get("responses", {})
                chat_id = data.get("chat_id")

                with st.chat_message("assistant"):
                    if len(responses) > 1:
                        cols = st.columns(len(responses))
                        for i, (model_name, answer) in enumerate(responses.items()):
                            with cols[i]:
                                st.caption(f"**{model_name}**")
                                st.info(answer)
                        # activate sidebar button
                        st.session_state["last_debate_chat_id"] = chat_id
                        st.session_state["pending_vote"] = True
                        st.caption("👈 Use **⚖️ Let the Counsel Vote** in the sidebar to get the verdict.")
                    else:
                        model_name = list(responses.keys())[0]
                        st.caption(f"**{model_name}**")
                        st.write(responses[model_name])
                        st.session_state["pending_vote"] = False

                st.session_state["messages"].append(
                    {"role": "assistant", "responses": responses, "chat_id": chat_id}
                )
            else:
                try:
                    err = response.json().get("detail", "")
                except Exception:
                    err = response.text
                st.error(f"The Counsel failed to respond: {err}")

    # Admin settings
    def render_admin_panel(self):
        st.header("Admin Settings")

        token = st.session_state["token"]
        res = self.api.get_admin_settings(token)

        if res.status_code == 403:
            st.error("Admin access required.")
            return
        if res.status_code != 200:
            st.error(f"Failed to load settings ({res.status_code}): {res.text}")
            return

        settings = res.json()
        available_models: dict = settings.get("available_models", {})
        providers: list = settings.get("providers", [])
        current_active: list = settings.get("active_models", [])
        current_keys: dict = settings.get("api_keys", {})

        with st.form("admin_settings_form"):
            st.subheader("API Keys")
            st.caption(
                "Keys stored here override .env. Leave blank to keep the existing key. "
                "Displayed values are masked."
            )
            key_inputs: Dict[str, str] = {}
            for prov in providers:
                existing_masked = current_keys.get(prov, "")
                key_inputs[prov] = st.text_input(
                    f"{prov.title()} API Key",
                    value=existing_masked,
                    type="password",
                    key=f"key_{prov}",
                    placeholder=f"Enter {prov.title()} key (blank = keep current)",
                )

            st.divider()
            st.subheader("Active Models")
            st.caption("Select which models are available to all users.")
            active_selection = st.multiselect(
                "Enabled models:",
                options=list(available_models.keys()),
                default=[m for m in current_active if m in available_models],
            )

            submitted = st.form_submit_button("Save Settings", type="primary")
            if submitted:
                new_keys = {
                    p: v for p, v in key_inputs.items()
                    if v and "***" not in v and v != current_keys.get(p, "")
                }
                update_res = self.api.update_admin_settings(
                    token,
                    api_keys=new_keys if new_keys else None,
                    active_models=active_selection,
                )
                if update_res.status_code == 200:
                    st.success("Settings saved!")
                    st.rerun()
                else:
                    detail = update_res.json().get("detail", "Update failed")
                    st.error(detail)

    # Entry point 
    def run(self):
        st.set_page_config(page_title="Counsel of AI", page_icon="🏛️", layout="wide")
        self.render_sidebar()
        if st.session_state["authenticated"]:
            view = st.session_state.get("view", "chat")
            if view == "admin":
                self.render_admin_panel()
            else:
                self.render_chat_interface()
        else:
            st.info("Please log in via the sidebar to access the Counsel.")


if __name__ == "__main__":
    client = APIClient()
    app = CounselOfAIApp(client)
    app.run()
else:
    client = APIClient()
    app = CounselOfAIApp(client)
    app.run()