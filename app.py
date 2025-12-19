import streamlit as st
import boto3
import uuid
from botocore.exceptions import ClientError

# -------------------------
# CONFIG
# -------------------------
AGENT_ID = "<your bedrock agent id>"
AGENT_ALIAS_ID = "<your bedrock agent alias ID>"
region = "us-east-1"

if not AGENT_ID or not AGENT_ALIAS_ID:
    raise RuntimeError("Set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID in your environment.")

def get_client():
    # Uses your local AWS profile / credentials
    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
    return client


def invoke_agent(prompt: str, session_id: str | None = None):
    if session_id is None:
        session_id = str(uuid.uuid4())

    client = get_client()

    try:
        response = client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=prompt,
            enableTrace=True
        )

        final_text = ""
        for event in response.get("completion", []):
            if "chunk" in event:
                final_text += event["chunk"]["bytes"].decode("utf-8")

        return final_text, session_id

    except ClientError as e:
        st.error(f"AWS error: {e}")
        return None, session_id


# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="ITOPS Agent Chat", layout="centered")
st.title("🤖 ITOPS Agent Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])  # markdown = ChatGPT look

prompt = st.chat_input("Message ITOPS Agent...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        try:
            result = invoke_agent(prompt, st.session_state.session_id)
            reply = result[0] if isinstance(result, tuple) else result
        except Exception as e:
            reply = f"❌ Error: {e}"
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
