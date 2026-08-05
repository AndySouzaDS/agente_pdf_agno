"""
Agent Chat PDF — frontend Streamlit para um agente Agno 2.0 rodando via AgentOS.
"""
# 1. Imports
import json
import os
import requests
import streamlit as st

# 2. Conexão com o Agno (SERVER)

# 2.1. Configuração de ENDPOINT
# Por padrão aponta pra produção (Render) — igual já estava commitado.
# Pra rodar contra o Agno local, roda: AGNO_ENV=local streamlit run 04_exemplo.py
AGENT_ID = "agente_pdf"
URLS = {
    "local": "http://localhost:7777",
    "production": "https://modulo-3-api-wxvi.onrender.com",
}
AGNO_ENV = os.environ.get("AGNO_ENV", "production")
BASE_URL = URLS.get(AGNO_ENV, URLS["production"])
ENDPOINT = f"{BASE_URL}/agents/{AGENT_ID}/runs"

# 2.2. Função de Resposta com Streaming
def get_response_stream(message: str):
    response = requests.post(
        url=ENDPOINT,
        data={
            "message": message,
            "stream": "true"
        },
        stream=True
    )

    # Streaming (processamento)
    for line in response.iter_lines():
        if line:
            # Parse Server-Sent Events
            if line.startswith(b'data: '):
                data = line[6:] # Remove 'data: ' prefix
                try:
                    event = json.loads(data)
                    yield event
                except json.JSONDecodeError:
                    continue

# 3. Streamlit
# 3.1. Configuração do Header
st.set_page_config(page_title="Agente Chat PDF")
st.title("Agente Chat PDF")

# 3.2. Histórico
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3.3. Mostrar histórico   
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("process"):
            with st.expander(label="Process", expanded=False):
                st.json(msg["process"])
        st.markdown(msg["content"])

# 3.4. Input do usuário
if prompt := st.chat_input("Digite sua mensagem/pergunta..."):
    # Adicionar mensagem do usuário (memoria do streamlit)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
    
    # processamento streaming
    for event in get_response_stream(prompt):
        event_type = event.get("event", "")
        
        # Tool call iniciado
        if event_type == "ToolCallStarted":
            tool_name = event.get("tool", {}).get("tool_name")
            with st.status(f"Executando {tool_name}...", expanded=True):
                st.json(event.get("tool", {}).get("tool_args", {}))

        # Conteúdo da resposta
        elif event_type == "RunContent":
            content = event.get("content", "")
            if content:
                full_response += content
                response_placeholder.markdown(full_response + "▌")
    
    response_placeholder.markdown(full_response)

    # salvar a resposta e histórico na session state
    st.session_state.messages.append({
            "role": "assistant",
            "content": full_response

        })
