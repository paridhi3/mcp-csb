# mcp_client_agent.py
from mcp_agents.client import MCPClient  # Other package: see https://github.com/lastmile-ai/mcp-agent
from langchain.llms import OpenAI

mcp = MCPClient(servers=[
    {"type": "stdio", "command": ["python", "mcp_server_tools.py"]},
    {"type": "stdio", "command": ["python", "mcp_server_summarizer.py"]},
    {"type": "stdio", "command": ["python", "mcp_server_validator.py"]},
])

def ingest_all_files():
    files = mcp.call("list_files", {"source": "local"})
    for f in files:
        ext = f.split(".")[-1]
        if ext == "pdf":
            text = mcp.call("extract_pdf", {"filename": f})
        else:
            text = mcp.call("extract_ppt", {"filename": f})
        summary = mcp.call("summarize", {"text": text})
        tags = mcp.call("categorize", {"text": text})
        result = {"file": f, "summary": summary, "category_domain_tech": tags, "full_text": text}
        valid = mcp.call("validate", {"item": result})
        print(result, valid)

def ask_multi_file(query):
    # Implement custom Retriever+RAG using stored summaries, or call a compatible search tool via MCP
    pass  # User may add code with llama-index or similar

if __name__ == "__main__":
    ingest_all_files()
    # ask_multi_file("List all case studies in finance domain")
