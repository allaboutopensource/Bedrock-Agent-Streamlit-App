# Bedrock-Agent-Streamlit-App
A lightweight Streamlit-based UI for interacting with an Amazon Bedrock Agent that has an LLM model and guardrails attached. The app runs locally, uses AWS credentials/profiles, and supports multi-turn conversations via session management.


<img width="592" height="396" alt="image" src="https://github.com/user-attachments/assets/b6d185b6-7e45-43df-aaa5-524a9f43af2f" />



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

