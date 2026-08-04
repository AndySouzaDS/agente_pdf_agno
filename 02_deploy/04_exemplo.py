"""
Agent Chat PDF — frontend Streamlit para um agente Agno 2.0 rodando via AgentOS.

Por que essa arquitetura:
- O agente roda separado (AgentOS, exposto via HTTP), esse script é só o CLIENTE.
- Isso é o que te permite trocar o endpoint depois do deploy sem tocar no código:
  a URL do backend vem de variável de ambiente (AGNO_API_URL), não fica hardcoded.
- O parsing do stream segue o formato oficial do AgentOS (SSE), documentado em
  https://docs.agno.com — cada evento vem como uma linha "data: {json}".
"""

import json
import os

import requests
import streamlit as st

# ── 1. Configuração via variáveis de ambiente ────────────────────────────
# Isso é o pulo do gato pro seu fluxo: local, aponta pro localhost:7777.
# No Render, você só seta AGNO_API_URL nas env vars do serviço, sem mexer no código.
# AGNO_API_URL = os.environ.get("AGNO_API_URL", "http://localhost:7777")
AGENT_ID = "agente_pdf"
ENDPOINT = f"https://modulo-3-api-wxvi.onrender.com:10000/agents/{AGENT_ID}/runs"

# ── 2. Config da página ───────────────────────────────────────────────────
st.set_page_config(page_title="Agent Chat PDF", page_icon="🤖", layout="centered")
st.title("Agent Chat PDF")

# ── 3. Histórico de mensagens no estado da sessão ────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── 4. Chamada streaming ao AgentOS ──────────────────────────────────────
def stream_agent_response(user_input: str, content_placeholder, tool_container):
    """
    Faz o POST no endpoint /runs com stream=true e vai processando os eventos
    SSE conforme chegam. Retorna o texto final acumulado.

    Formato de cada evento (linha "data: {...}"):
        {"event": "RunContent", "content": "pedaço de texto"}
        {"event": "ToolCallStarted", "tool": {"tool_name": "...", "tool_args": {...}}}
        {"event": "RunCompleted", "content": "texto final completo"}
    Eventos desconhecidos são ignorados — isso evita que o app quebre se o
    Agno adicionar um novo tipo de evento numa atualização de versão.
    """
    accumulated_text = ""

    try:
        response = requests.post(
            RUN_ENDPOINT,
            json={"input": user_input, "stream": True},
            params={"stream": "true", "stream_events": "true"},
            stream=True,
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        error_msg = f"Não consegui falar com o agente em `{RUN_ENDPOINT}`: {exc}"
        content_placeholder.error(error_msg)
        return error_msg

    for raw_line in response.iter_lines(decode_unicode=True):
        # Linhas em branco separam eventos SSE — e a linha "event: X" a gente
        # ignora, só nos importa a linha "data: {...}" que tem o payload.
        if not raw_line or not raw_line.startswith("data:"):
            continue

        payload_str = raw_line[len("data:"):].strip()
        try:
            event = json.loads(payload_str)
        except json.JSONDecodeError:
            continue

        event_type = event.get("event", "")

        if event_type == "RunContent":
            chunk = event.get("content") or ""
            accumulated_text += chunk
            content_placeholder.markdown(accumulated_text + "▌")

        elif event_type in ("ToolCallStarted", "ToolCallCompleted"):
            # O Agno manda o nome/args da tool em "tool" (dict) ou, em versões
            # antigas, direto em "tool_name"/"tool_args" — cobrimos os dois.
            tool_info = event.get("tool") or {}
            tool_name = tool_info.get("tool_name") or event.get("tool_name") or "tool"
            tool_args = tool_info.get("tool_args") or event.get("tool_args") or {}

            label = (
                f"🔧 Executando {tool_name}..."
                if event_type == "ToolCallStarted"
                else f"✅ {tool_name} concluído"
            )
            with tool_container.expander(label, expanded=False):
                st.json(tool_args)

        elif event_type == "RunCompleted":
            # RunCompleted normalmente já traz o texto final consolidado —
            # usamos ele como fonte da verdade em vez do que foi acumulado
            # chunk a chunk, pra evitar texto duplicado ou cortado.
            final_content = event.get("content")
            if final_content:
                accumulated_text = final_content
            content_placeholder.markdown(accumulated_text)

        elif event_type == "RunError":
            err = event.get("content") or "Erro desconhecido no agente."
            content_placeholder.error(err)
            return err

    # Garante que o cursor "▌" some mesmo se não veio RunCompleted explícito
    content_placeholder.markdown(accumulated_text)
    return accumulated_text


# ── 5. Input do usuário e loop principal ─────────────────────────────────
if prompt := st.chat_input("Digite sua mensagem..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        tool_container = st.container()
        content_placeholder = st.empty()
        full_response = stream_agent_response(prompt, content_placeholder, tool_container)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
