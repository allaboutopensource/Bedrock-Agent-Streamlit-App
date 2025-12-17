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


@st.cache_resource
def get_client():
    # Uses your local AWS profile / credentials
    client = boto3.client("bedrock-agent-runtime", region_name=region)
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

# Keep session id across Streamlit reruns
if "session_id" not in st.session_state:
    st.session_state.session_id = None

prompt = st.text_area("Enter your prompt:")

if st.button("Send"):
    if prompt.strip():
        with st.spinner("Agent is thinking..."):
            reply, sid = invoke_agent(prompt, st.session_state.session_id)
            st.session_state.session_id = sid

        if reply:
            st.markdown("### Agent reply")
            st.write(reply)
    else:
        st.warning("Please enter a prompt.")
