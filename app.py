"""
Streamlit app with 3 tabs:
1. Files Metadata Table (File, Category, Domain, Technologies)
2. Chatbot interface for queries
3. Summaries display (optional)
"""

import os
import streamlit as st
from dotenv import load_dotenv
from mcp_agents.client import MCPClient
import asyncio

load_dotenv()

# MCP tool servers assumed running locally or via subprocess
# Adjust commands or connection params as per your deployment

# Initialize MCP client with stdio servers or remote URLs as per your setup
# For demonstration, we will spawn subprocess MCP servers inline (simplified).
# In production, run these servers separately for stability!

# Note: In a real app, async-await usage is necessary to interact with MCP client; here simplified with asyncio.run

async def start_mcp_client():
    # Start MCP client connecting to tool servers

    # For demo, using stdio server launching Python scripts.
    # In production you'd launch MCP servers separately and connect to URLs or IPC.

    client = MCPClient(servers=[
        # File ops server
        {"type": "stdio", "command": ["python", "mcp_server_files.py"]},
        # Summarizer server
        {"type": "stdio", "command": ["python", "mcp_server_summarizer.py"]},
        # Validator server
        {"type": "stdio", "command": ["python", "mcp_server_validator.py"]},
    ])
    await client.start()
    return client

@st.cache_resource
def get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

loop = get_event_loop()
mcp_client = loop.run_until_complete(start_mcp_client())

# Utility async runner wrapper for Streamlit sync calls
def run_async(coro):
    return loop.run_until_complete(coro)


@st.cache_data(show_spinner=False)
def ingest_files():
    """
    Ingest all files, extract text, summarize, categorize, validate.
    Returns list of metadata dicts with keys: file, summary, category_domain_tech, full_text
    """
    files = run_async(mcp_client.call_tool("list_files", {"source": "local"}))
    results = []

    for f in files:
        ext = f.lower().split(".")[-1]
        if ext == "pdf":
            text = run_async(mcp_client.call_tool("extract_pdf", {"filename": f}))
        elif ext in ("ppt", "pptx"):
            text = run_async(mcp_client.call_tool("extract_ppt", {"filename": f}))
        else:
            continue

        summary = run_async(mcp_client.call_tool("summarize", {"text": text}))
        category_domain_tech = run_async(mcp_client.call_tool("categorize", {"text": text}))

        item = {
            "file": f,
            "summary": summary,
            "category_domain_tech": category_domain_tech,
            "full_text": text
        }
        validation = run_async(mcp_client.call_tool("validate", {"item": item}))

        if validation.get("valid", False):
            results.append(item)
        else:
            st.warning(f"Validation failed for file {f}: {validation.get('errors')}")

    return results


def parse_category_domain_tech(text: str):
    """
    Parses LLM categorize output formatted as:
    1. Category: ...
    2. Domain: ...
    3. Technologies: tech1, tech2,...
    Returns a tuple of strings (category, domain, technologies)
    """
    cat, dom, tech = "", "", ""
    lines = text.splitlines()
    for line in lines:
        if line.lower().startswith("1. category"):
            cat = line.split(":", 1)[1].strip()
        elif line.lower().startswith("2. domain"):
            dom = line.split(":", 1)[1].strip()
        elif line.lower().startswith("3. technologies"):
            tech = line.split(":", 1)[1].strip()
    return cat or "Unknown", dom or "Unknown", tech or "Unknown"


def main():
    st.title("Case Study MCP Agent System")

    tab1, tab2, tab3 = st.tabs(["Files Metadata", "Chatbot", "Summaries"])

    with tab1:
        st.header("File Metadata")

        data = ingest_files()

        if data:
            # Prepare table data
            rows = []
            for item in data:
                category, domain, technologies = parse_category_domain_tech(item['category_domain_tech'])
                rows.append({
                    "File Name": item['file'],
                    "Category": category,
                    "Domain": domain,
                    "Technologies": technologies,
                })
            st.table(rows)
        else:
            st.info("No files processed yet or no valid files found.")

    with tab2:
        st.header("Chatbot")

        query = st.text_input("Ask a question about the case studies:")
        if st.button("Ask"):
            if not query.strip():
                st.warning("Please enter a question.")
            else:
                # For now, implement a simple retrieval from summaries matching keywords (simplified)
                # TODO: Replace this with real MCP Search/Index server call for proper RAG query

                # Simple keyword search fallback:
                data = ingest_files()
                combined_text = "\n\n".join(item['summary'] for item in data)

                # Use OpenAI to answer query using combined summaries:
                import openai
                openai.api_key = os.getenv("OPENAI_API_KEY")

                system_prompt = "You are a chatbot providing answers based on case study summaries.\n\n"
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Case studies summaries:\n{combined_text[:3000]}"},
                    {"role": "user", "content": f"Question: {query}"}
                ]
                with st.spinner("Getting answer..."):
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-4.1",
                            messages=messages,
                            max_tokens=300,
                            temperature=0,
                        )
                        answer = response.choices[0].message.content
                        st.markdown(f"**Answer:** {answer}")
                    except Exception as e:
                        st.error(f"Error during chat: {e}")

    with tab3:
        st.header("Summaries")

        data = ingest_files()
        if data:
            for item in data:
                st.subheader(item['file'])
                st.write(item['summary'])
        else:
            st.info("No summaries available yet.")


if __name__ == "__main__":
    main()
