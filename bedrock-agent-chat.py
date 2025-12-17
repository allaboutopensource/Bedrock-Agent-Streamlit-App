#!/usr/bin/env python3
import argparse
import boto3
import uuid
from botocore.exceptions import ClientError
"""
Prompt (your code) → invoke_agent API → Agent (LLM + guardrails + tools/KB) → streamed chunks → concatenate → print final reply
 Invoke an Amazon Bedrock Agent and print the response
"""
agent_id = "<enter your bedtock agent ID>"
agent_alias_id = "<enter your bedtock agent alias ID"
region = "us-east-1"
prompt = input("Enter your prompt for the agent: ")

session = boto3.Session(profile_name="default", region_name=region)
client = session.client("bedrock-agent-runtime")

def invoke_agent(agent_id: str, agent_alias_id: str, prompt: str, region: str, session_id: str | None = None):
    if session_id is None:
        session_id = str(uuid.uuid4())                          # Generate a new session ID if not provided and uuid.uuid4() will create a random unique identifier

    try:
        response = client.invoke_agent(agentId=agent_id,agentAliasId=agent_alias_id,sessionId=session_id,inputText=prompt)
        completion_text = ""
        for event in response.get("completion", []):
            if "chunk" in event and "bytes" in event["chunk"]:
                completion_text += event["chunk"]["bytes"].decode("utf-8")  # :contentReference[oaicite:4]{index=4}

        return completion_text, session_id

    except ClientError as e:
        raise RuntimeError(f"InvokeAgent failed: {e}") from e 

def main():
    reply = invoke_agent(agent_id=agent_id,agent_alias_id=agent_alias_id,region=region,prompt=prompt)
    print("Agent reply:")
    print(reply)

if __name__ == "__main__":
    main()
