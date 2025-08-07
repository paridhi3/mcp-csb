# mcp_client_agent.py
import asyncio
from mcp_agents.client import MCPClient  # MCP agent Python client library
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores import FAISS
import os

class MCPAgentClient:
    def __init__(self):
        # Define MCP servers to connect to, running extraction, summarizer, validator tools
        self.mcp = MCPClient(servers=[
            {"type": "stdio", "command": ["python", "mcp_server_tools.py"]},
            {"type": "stdio", "command": ["python", "mcp_server_summarizer.py"]},
            {"type": "stdio", "command": ["python", "mcp_server_validator.py"]},
        ])
        self.index = None
        self.documents = []

    async def start(self):
        # Start the MCP client and connect to all servers
        await self.mcp.start()

    async def ingest_all_files(self):
        # List all files from local MCP filesystem server
        files = await self.mcp.call_tool("list_files", {"source": "local"})
        results = []

        # Process each file: extract text, summarize, categorize, validate
        for f in files:
            ext = f.split(".")[-1].lower()
            if ext == "pdf":
                text = await self.mcp.call_tool("extract_pdf", {"filename": f})
            else:
                text = await self.mcp.call_tool("extract_ppt", {"filename": f})

            summary = await self.mcp.call_tool("summarize", {"text": text})
            tags = await self.mcp.call_tool("categorize", {"text": text})

            result = {
                "file": f,
                "summary": summary,
                "category_domain_tech": tags,
                "full_text": text,
            }
            valid = await self.mcp.call_tool("validate", {"item": result})

            if valid.get("valid", False):
                results.append(result)
            else:
                print(f"Validation failed for {f}: {valid.get('errors')}")

        self.documents = results
        await self.build_index()

    async def build_index(self):
        # Use AzureOpenAIEmbeddings with text-embedding-ada-002 model
        embedding_model = AzureOpenAIEmbeddings(deployment_name="text-embedding-ada-002")
        texts = [doc["summary"] for doc in self.documents]
        # Create FAISS vector index for semantic search
        self.index = FAISS.from_texts(texts, embedding_model)

    async def ask_multi_file(self, query):
        # Perform semantic search on indexed summaries
        if self.index is None:
            print("Index not built yet. Please ingest files first.")
            return None
        docs = self.index.similarity_search(query)
        # Return concatenated matching summaries as answer
        answers = "\n\n".join([doc.page_content for doc in docs])
        return answers


async def main():
    agent = MCPAgentClient()
    await agent.start()
    await agent.ingest_all_files()
    # Example query to test multi-file search
    response = await agent.ask_multi_file("List all case studies in finance domain")
    print("Answer:\n", response)


if __name__ == "__main__":
    asyncio.run(main())
