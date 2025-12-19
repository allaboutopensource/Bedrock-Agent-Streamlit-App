# Bedrock-Agent-Streamlit-App

📌 Project Summary: AI Conversational Assistant with Streamlit, Amazon Bedrock, and Jira

Overview

This project implements an IT Operations (ITOPS) conversational assistant that enables users to interact with Jira directly through a chat-based web interface. The solution uses a Streamlit application as the frontend, integrated with an Amazon Bedrock Agent that orchestrates actions through a Jira Action Group backed by an AWS Lambda function.

The system allows users to:

Query the status and details of existing Jira tickets (e.g., IIS-354)

Create new Jira tickets through natural language prompts

Interact in a ChatGPT-style conversational UI

A lightweight Streamlit-based UI for interacting with an Amazon Bedrock Agent that has an LLM model and guardrails attached. The app runs locally, uses AWS credentials/profiles, and supports multi-turn conversations via session management.

<img width="592" height="396" alt="image" src="https://github.com/user-attachments/assets/b6d185b6-7e45-43df-aaa5-524a9f43af2f" />




Technologies Used

Frontend: Streamlit (Python)

AI Orchestration: Amazon Bedrock Agents

Backend: AWS Lambda (Python)

Integration: Jira Cloud REST API

Infrastructure: AWS IAM, Bedrock Agent Runtime


<img width="990" height="474" alt="image" src="https://github.com/user-attachments/assets/75c2b97d-6243-4eb7-a217-25fd92ab74da" />


Note: Configure AWS credentials for the streamlit user, in this case the user is ubuntu 

Note: we have created agent-chat as virtual enviroment in the Python and installed boto3, streamlit, pandas numpy requests. We also created a service called "streamlit-app.service"

streamlit service config :


[Unit]
Description=Streamlit App
After=network.target


[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/streamlit-app
Environment="PATH=/home/ubuntu/streamlit-app/agent-chat/bin"
ExecStart=/home/ubuntu/streamlit-app/agent-chat/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always
RestartSec=5


[Install]
WantedBy=multi-user.target

