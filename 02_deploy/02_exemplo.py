"""
Agente de PDF — Agno v2.x + AgentOS

Ingestão do relatório via `lifespan`, para funcionar tanto rodando local
(`uv run 02_exemplo.py`) quanto em produção (Render, que importa `app`
diretamente via `uvicorn 02_exemplo:app`, sem passar pelo `if __name__`).
"""

from contextlib import asynccontextmanager

from agno.agent import Agent
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.vectordb.chroma import ChromaDb
from agno.models.openrouter import OpenRouter
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.embedder.google import GeminiEmbedder
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# RAG: base vetorial do PDF
# --------------------------------------------------------------------------
vector_db = ChromaDb(
    collection="pdf_agent",
    path="tmp/chromadb",
    persistent_client=True,
    embedder=GeminiEmbedder(),
)

knowledge = Knowledge(
    vector_db=vector_db,
)

# --------------------------------------------------------------------------
# Banco de sessões / histórico
# --------------------------------------------------------------------------
db = SqliteDb(
    session_table="agent_session",
    db_file="tmp/agent.db",
)

# --------------------------------------------------------------------------
# Agente
# --------------------------------------------------------------------------
agent = Agent(
    id="agente_pdf",
    name="Agente de PDF",
    model=OpenRouter(id="openai/gpt-oss-120b"),
    db=db,
    knowledge=knowledge,
    enable_user_memories=True,
    instructions="Você deve chamar o usuário de senhor e busque as informações do PDF.",
    description="",
    add_history_to_context=True,
    search_knowledge=True,
    num_history_runs=3,
    debug_mode=True,
)


# --------------------------------------------------------------------------
# Lifespan: roda a ingestão do PDF sempre que a aplicação sobe,
# independente de ser via `python 02_exemplo.py` (local) ou
# `uvicorn 02_exemplo:app` (Render/produção) — os dois passam por aqui.
# --------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):
    await knowledge.add_content_async(
        url="https://s3.sa-east-1.amazonaws.com/static.grendene.aatb.com.br/releases/2417_2T25.pdf",
        metadata={
            "source": "Grandene",
            "type": "pdf",
            "description": "Relatório Trimestral Grandene - 2T25",
        },
        skip_if_exists=True,
        reader=PDFReader(),
    )
    yield
    # (nada a fazer no shutdown por enquanto)


# --------------------------------------------------------------------------
# AgentOS
# --------------------------------------------------------------------------
agent_os = AgentOS(
    agents=[agent],
    db=db,
    lifespan=lifespan,
)

app = agent_os.get_app()


# --------------------------------------------------------------------------
# Execução local
# --------------------------------------------------------------------------
if __name__ == "__main__":
    agent_os.serve(
        app="02_exemplo:app",
        host="0.0.0.0",
        port=7777,
        reload=True,
    )
