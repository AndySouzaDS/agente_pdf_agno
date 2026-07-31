from agno.agent import Agent
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.models.openrouter import OpenRouter
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb
from fastapi import FastAPI
import uvicorn
import asyncio
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
    name="Agente de PDF",
    model=OpenRouter(id="openai/gpt-oss-120b"),
    db=db,
    knowledge=knowledge,
    instructions="Você deve chamar o usuário de senhor",
    description="",
    add_history_to_context=True,
    search_knowledge=True,
    num_history_runs=3,
    debug_mode=True
)

# API
app = FastAPI(title="Agente de PDF", description="API do agente de PDF")

@app.post("/agente_pdf")
async def agente_pdf(pergunta: str):
    response = await agent.arun(pergunta)
    return {"message": response.content}

# Run
if __name__ == "__main__":
    asyncio.run(knowledge.add_content_async(
            url="https://s3.sa-east-1.amazonaws.com/static.grendene.aatb.com.br/releases/2417_2T25.pdf",
            metadata={
                "source": "Grandene",
                "type": "pdf",
                "description": "Relatório Trimestral Grandene - 2T25"  
            },
            skip_if_exists=True,
            reader=PDFReader()
        )   
    )     
    uvicorn.run("01_exemplo:app", host="0.0.0.0", port=8000, reload=True)
