import streamlit as st
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.research_agent import Web3ResearchAgent
from mcps.defillama_mcp import DeFiLlamaMCP
from mcps.coinmarketcap_mcp import CoinMarketCapMCP
from mcps.etherscan_mcp import EtherscanMCP

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Web3 Research Co-Pilot", page_icon="🚀", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

@st.cache_resource
def initialize_agent():
    """Initialize the research agent with data sources"""
    try:
        agent = Web3ResearchAgent()
        
        # Add DeFiLlama MCP (free, no API key needed)
        defillama = DeFiLlamaMCP()
        for tool in defillama.get_tools():
            agent.add_tool(tool)
        
        # Add CoinMarketCap MCP (requires API key)
        coinmarketcap = CoinMarketCapMCP()
        for tool in coinmarketcap.get_tools():
            agent.add_tool(tool)
        
        # Add Etherscan MCP (requires API key)
        etherscan = EtherscanMCP()
        for tool in etherscan.get_tools():
            agent.add_tool(tool)
        
        return agent, None
    except Exception as e:
        return None, str(e)

def main():
    # Header
    st.title("🚀 Web3 Research Co-Pilot")
    st.markdown(
        "Ask me anything about Web3 data, DeFi protocols, token metrics, and blockchain analytics!"
    )

    # Initialize agent
    if st.session_state.agent is None:
        with st.spinner("🔧 Initializing AI agent..."):
            agent, error = initialize_agent()
            if agent:
                st.session_state.agent = agent
                st.success("✅ Agent initialized successfully!")
            else:
                st.error(f"❌ Failed to initialize agent: {error}")
                st.stop()

    # Sidebar for settings and chat history
    with st.sidebar:
        st.header("⚙️ Settings")

        # API Status Check
        st.subheader("API Status")
        if os.getenv("GEMINI_API_KEY"):
            st.success("✅ Gemini API")
        else:
            st.error("❌ Gemini API Key missing")
            st.info("Add GEMINI_API_KEY to your .env file")

        # Available Tools
        st.subheader("🔧 Available Tools")
        if st.session_state.agent:
            tools = st.session_state.agent.get_available_tools()
            for tool in tools:
                st.info(f"🟢 {tool}")
        
        # Data Sources Status
        st.subheader("📊 Data Sources")
        sources_status = [
            ("DeFiLlama", "🟢 Active", "Free API"),
            ("CoinMarketCap", "🟡 Pending", "Need API key"),
            ("Etherscan", "🟡 Pending", "Need API key"),
            ("Dune Analytics", "🔵 Coming soon", "Phase 2"),
            ("Nansen", "🔵 Coming soon", "Phase 2"),
            ("Artemis", "🔵 Coming soon", "Phase 2"),
        ]

        for source, status, note in sources_status:
            st.text(f"{status} {source}")
            st.caption(note)

        st.markdown("---")
        
        # Sample queries
        st.subheader("💡 Try These Queries")
        sample_queries = [
            "Show me top 10 DeFi protocols by TVL",
            "Analyze Uniswap protocol",
            "What are the highest yield opportunities?",
            "Compare TVL across different blockchains"
        ]
        
        for query in sample_queries:
            if st.button(f"📝 {query}", key=query, use_container_width=True):
                # Add to chat
                st.session_state.messages.append({
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.rerun()

        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Main chat interface
    st.subheader("💬 Chat Interface")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "data" in message:
                # Display structured response
                st.write(message["content"])
                
                # Show sources if available
                if message["data"].get("sources"):
                    with st.expander("📚 Sources Used"):
                        for source in message["data"]["sources"]:
                            st.write(f"• {source}")
                
                # Show research steps if available
                if message["data"].get("steps"):
                    with st.expander("🔍 Research Steps"):
                        for i, step in enumerate(message["data"]["steps"], 1):
                            st.write(f"{i}. {step}")
                            
            else:
                st.write(message["content"])
            
            if "timestamp" in message:
                st.caption(f"🕒 {message['timestamp']}")

    # Chat input
    if prompt := st.chat_input("Ask me about Web3 data..."):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        })

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"🕒 {timestamp}")

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Researching..."):
                # Use the real agent
                if st.session_state.agent:
                    result = st.session_state.agent.research(prompt)
                    
                    if result["success"]:
                        st.write(result["answer"])
                        
                        # Show sources
                        if result["sources"]:
                            with st.expander("📚 Sources Used"):
                                for source in result["sources"]:
                                    st.write(f"• {source}")
                        
                        # Add assistant message with structured data
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["answer"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "data": result
                        })
                    else:
                        error_msg = f"❌ Research failed: {result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                else:
                    st.error("❌ Agent not initialized")

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "🟢 Online")
    with col2:
        st.metric("Phase", "1 Complete")
    with col3:
        if st.session_state.agent:
            tool_count = len(st.session_state.agent.get_available_tools())
            st.metric("Tools Active", f"{tool_count}")

if __name__ == "__main__":
    main()