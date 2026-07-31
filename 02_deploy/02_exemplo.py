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

# RAG
vector_db = ChromaDb(
    collection="pdf_agent", 
    path="tmp/chromadb", 
    persistent_client=True,
    embedder=GeminiEmbedder()
)

# Banco de dados do conhecimento
knowledge = Knowledge(
    vector_db=vector_db,
)

# Banco de dados das sessões
db = SqliteDb(
    session_table="agent_session", 
    db_file="tmp/agent.db"
)

# Criação do agente
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
    debug_mode=True
)

# AgentOS (não precisa nem do name e nem do id do agente)
agent_os = AgentOS(
    agents=[agent],
    db=db
    )

app = agent_os.get_app()

# Run
if __name__ == "__main__":
    knowledge.add_content(
            url="https://s3.sa-east-1.amazonaws.com/static.grendene.aatb.com.br/releases/2417_2T25.pdf",
            metadata={
                "source": "Grandene",
                "type": "pdf",
                "description": "Relatório Trimestral Grandene - 2T25"  
            },
            skip_if_exists=True,
            reader=PDFReader()
        )

    agent_os.serve(
        app="02_exemplo:app",
        host="0.0.0.0",
        port=10000,
        reload=True
    )
