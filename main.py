import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Web3 Research Co-Pilot", page_icon="🚀", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []


def main():
    # Header
    st.title("🚀 Web3 Research Co-Pilot")
    st.markdown(
        "Ask me anything about Web3 data, DeFi protocols, token metrics, and blockchain analytics!"
    )

    # Sidebar for settings and chat history
    with st.sidebar:
        st.header("⚙️ Settings")

        # API Status Check
        st.subheader("API Status")
        if os.getenv("GEMINI_API_KEY"):
            st.success("✅ Gemini API Key loaded")
        else:
            st.error("❌ Gemini API Key missing")
            st.info("Add GEMINI_API_KEY to your .env file")

        # Data Sources
        st.subheader("📊 Data Sources")
        sources = [
            ("DeFiLlama", "Free"),
            ("CoinMarketCap", "API Key needed"),
            ("Etherscan", "API Key needed"),
            ("Dune Analytics", "Coming soon"),
            ("Nansen", "Coming soon"),
            ("Artemis", "Coming soon"),
        ]

        for source, status in sources:
            if "Free" in status:
                st.info(f"🟢 {source} - {status}")
            elif "API Key" in status:
                st.warning(f"🟡 {source} - {status}")
            else:
                st.info(f"🔵 {source} - {status}")

        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    # Main chat interface
    st.subheader("💬 Chat Interface")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"🕒 {message['timestamp']}")

    # Chat input
    if prompt := st.chat_input("Ask me about Web3 data..."):
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add user message
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "timestamp": timestamp}
        )

        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"🕒 {timestamp}")

        # Generate response (placeholder for now)
        with st.chat_message("assistant"):
            with st.spinner("🔍 Researching..."):
                # Placeholder response - will be replaced with actual AI agent
                response = f"""
                📊 **Research Results for:** "{prompt}"
                
                🚧 **Status:** Development Mode
                
                **Next Steps:**
                1. Set up LangChain agent with Gemini
                2. Connect to data sources (DeFiLlama, CoinMarketCap, etc.)
                3. Implement query processing
                
                **Data Sources Being Prepared:**
                - 🟢 DeFiLlama API (Ready)
                - 🟡 CoinMarketCap API (Needs key)
                - 🟡 Etherscan API (Needs key)
                - 🔵 Dune Analytics MCP (Coming soon)
                
                *This is a placeholder response. Full functionality coming in Phase 2!*
                """

                st.write(response)

                # Add assistant message
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

    # Footer
    st.markdown("---")
    st.markdown("**Development Status:** Phase 1 - Foundation Setup Complete ✅")


if __name__ == "__main__":
    main()
