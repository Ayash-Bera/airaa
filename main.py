import streamlit as st
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.research_agent import Web3ResearchAgent
from mcps.defillama_mcp import DeFiLlamaMCP
from mcps.coinmarketcap_mcp import CoinMarketCapMCP
from mcps.etherscan_mcp import EtherscanMCP
from mcps.artemis_mcp import ArtemisMCP
from mcps.dune_mcp import DuneAnalyticsMCP
from mcps.nansen_mcp import NansenMCP

# Load environment variables

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
            
        # Add Artemis MCP (requires API key)
        artemis = ArtemisMCP()
        for tool in artemis.get_tools():
            agent.add_tool(tool)
            
        # Add Dune Analytics MCP (requires API key)
        dune = DuneAnalyticsMCP()
        for tool in dune.get_tools():
            agent.add_tool(tool)
            
        # Add Nansen MCP (requires API key)
        nansen = NansenMCP()
        for tool in nansen.get_tools():
            agent.add_tool(tool)
        
        return agent, None
    except Exception as e:
        return None, str(e)

def check_api_status():
    """Check which APIs are properly configured"""
    status = {}
    
    # Gemini
    status['gemini'] = bool(os.getenv("GEMINI_API_KEY"))
    
    # Test each MCP by making a simple call
    try:
        etherscan = EtherscanMCP()
        # Try a simple call to test if API key works
        result = etherscan.get_gas_tracker()
        status['etherscan'] = not result.startswith("Error")
    except:
        status['etherscan'] = False
        
    try:
        cmc = CoinMarketCapMCP()
        result = cmc.get_global_metrics()
        status['coinmarketcap'] = not result.startswith("Error")
    except:
        status['coinmarketcap'] = False
    
    # Others - just check if API key exists
    status['artemis'] = bool(os.getenv("ARTEMIS_API_KEY"))
    status['dune'] = bool(os.getenv("DUNE_API_KEY"))
    status['nansen'] = bool(os.getenv("NANSEN_API_KEY"))
    status['defillama'] = True  # No API key needed
    
    return status

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

    # Get API status
    api_status = check_api_status()

    # Sidebar for settings and chat history
    with st.sidebar:
        st.header("⚙️ Settings")

        # API Status Check
        st.subheader("API Status")
        
        if api_status['gemini']:
            st.success("✅ Gemini API")
        else:
            st.error("❌ Gemini API Key missing")

        # Data Sources Status
        st.subheader("📊 Data Sources")
        
        # DeFiLlama (always active)
        st.success("🟢 Active DeFiLlama")
        st.caption("Free API")
        
        # Etherscan
        if api_status['etherscan']:
            st.success("🟢 Active Etherscan")
            st.caption("Working API key")
        else:
            st.warning("🟡 Ready Etherscan")
            st.caption("Need API key")
            
        # CoinMarketCap
        if api_status['coinmarketcap']:
            st.success("🟢 Active CoinMarketCap")
            st.caption("Working API key")
        else:
            st.warning("🟡 Ready CoinMarketCap")
            st.caption("Need API key")
            
        # Others
        sources = [
            ("Artemis", api_status['artemis']),
            ("Dune Analytics", api_status['dune']),
            ("Nansen", api_status['nansen']),
        ]
        
        for source, active in sources:
            if active:
                st.success(f"🟢 Active {source}")
                st.caption("Working API key")
            else:
                st.warning(f"🟡 Ready {source}")
                st.caption("Need API key")

        # Available Tools
        st.subheader("🔧 Available Tools")
        if st.session_state.agent:
            tools = st.session_state.agent.get_available_tools()
            st.info(f"📊 {len(tools)} tools loaded")
            with st.expander("View all tools"):
                for tool in tools:
                    st.text(f"• {tool}")
        
        st.markdown("---")
        
        # Sample queries
        st.subheader("💡 Try These Queries")
        sample_queries = [
            "What are current Ethereum gas prices?",
            "Show me top 10 DeFi protocols by TVL",
            "Analyze Uniswap protocol",
            "What are the highest yield opportunities?"
        ]
        
        for query in sample_queries:
            if st.button(f"📝", key=f"btn_{query}", help=query, use_container_width=True):
                # Add to chat
                st.session_state.messages.append({
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.rerun()
            st.caption(query)

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
                            if hasattr(step, '__len__') and len(step) > 1:
                                st.write(f"{i}. Tool: {step[0].tool}")
                                st.write(f"   Action: {step[0].tool_input}")
                                st.write(f"   Result: {step[1][:200]}..." if len(step[1]) > 200 else f"   Result: {step[1]}")
                            else:
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
                    try:
                        result = st.session_state.agent.research(prompt)
                        
                        if result["success"]:
                            st.write(result["answer"])
                            
                            # Show sources
                            if result["sources"]:
                                with st.expander("📚 Sources Used"):
                                    for source in result["sources"]:
                                        st.write(f"• {source}")
                            
                            # Show steps
                            if result["steps"]:
                                with st.expander("🔍 Research Steps"):
                                    for i, step in enumerate(result["steps"], 1):
                                        if hasattr(step, '__len__') and len(step) > 1:
                                            st.write(f"**Step {i}:** {step[0].tool}")
                                            st.code(f"Input: {step[0].tool_input}")
                                            result_text = step[1][:300] + "..." if len(step[1]) > 300 else step[1]
                                            st.text(f"Output: {result_text}")
                                        else:
                                            st.write(f"{i}. {step}")
                            
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
                            
                            # Show more details about the error
                            if 'error' in result:
                                st.error(f"Details: {result['error']}")
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_msg,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                    except Exception as e:
                        error_msg = f"❌ Unexpected error: {str(e)}"
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
        active_sources = sum([1 for status in api_status.values() if status])
        st.metric("Active APIs", f"{active_sources}/7")
    with col3:
        if st.session_state.agent:
            tool_count = len(st.session_state.agent.get_available_tools())
            st.metric("Tools Active", f"{tool_count}")

if __name__ == "__main__":
    main()