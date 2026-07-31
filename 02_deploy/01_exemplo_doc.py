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

# -------------------------------- RAG -------------------------------- 
# O ChromaDb é um banco de dados vetorial que armazena os embeddings dos documentos
# O embedder é responsável por converter os documentos em embeddings
# O persistent_client=True faz com que o banco de dados seja persistente
# embedder=GeminiEmbedder() - o instrutor não usou, pois esta utilizando um modelo da OpenAI 
# que já vem com embedder
vector_db = ChromaDb(
    collection="pdf_agent", 
    path="tmp/chromadb", 
    persistent_client=True,
    embedder=GeminiEmbedder()
)

knowledge = Knowledge(
    vector_db=vector_db,
)

db = SqliteDb(
    session_table="agent_session", 
    db_file="tmp/agent.db"
)

# Visualizar a classe Agent, clicando no ctrl + click em Agent, e será aberto 
# o arquivo agent.py, para verificar os parâmetros que podem ser passados para 
# o Agent
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

# agent_os = AgentOS(agents=[agent])
# app = agent_os.get_app()

# agent.print_response(
#     "Qual foi a receita líquida da Grandene no 2T25?"
# )

# -------------------------------- API -------------------------------- 
app = FastAPI(title="Agente de PDF", description="API do agente de PDF")

# # resposta completa
# @app.post("/agente_pdf")
# def agente_pdf(pergunta: str):
#     return {"message": agent.run(pergunta)}

# # resposta direta - ERRO INSTRUTOR
# @app.post("/agente_pdf")
# def agente_pdf(pergunta: str):
#     response = asyncio.run(agent.run(pergunta))
#     message = response.messages[-1]
#     return {"message": message.content}

@app.post("/agente_pdf")
async def agente_pdf(pergunta: str):
    response = await agent.arun(pergunta)
    return {"message": response.content}

# -------------------------------- RUN -------------------------------- 
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
