# mcp_server_summarizer.py
from agents.mcp import MCPToolServer, tool
from openai import OpenAI

class SummarizerMCPServer(MCPToolServer):
    @tool
    def summarize(self, text: str):
        # Replace with your favorite LLM call
        return OpenAI().complete(prompt=f"Summarize:\n\n{text[:3500]}")

    @tool
    def categorize(self, text: str):
        return OpenAI().complete(prompt=f"List:\n1. Category\n2. Domain\n3. Technologies:\n\n{text[:3000]}")

if __name__ == "__main__":
    SummarizerMCPServer().serve()
