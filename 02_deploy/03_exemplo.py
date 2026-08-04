# 1. Importações
import requests
import json
from pprint import pprint


# PROTOCOL_HTTP = "http://"
# HOST = "localhost"
# PORT = "7777"
# ENDPOINT = "/agents/{AGENT_ID}/runs"
AGENT_ID = "agente_pdf"
ENDPOINT = f"http://localhost:7777/agents/{AGENT_ID}/runs"

# 2. Conexão com o Agno
def get_response_stream(message: str):
    response = requests.post(
        url=ENDPOINT,
        data={
            "message": message,
            "stream": True
        },
        stream=True
    )

    return response


# 3. Streaming (processamento)

# 4. Printar a resposta

# 5. RUN (loop)
# 5.1. Acessando o AgentUI:
# Rodamos o comando: cd agent-ui && npm run dev
# Depois entramos em:
# Local: http://localhost:3000
# Network: http://192.168.0.140:3000
if __name__ == "__main__":
    message = input("Digite sua mensagem: ")
    response = get_response_stream(message)
    print(response.text)
