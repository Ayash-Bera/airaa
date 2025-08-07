import os
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from typing import List, Dict, Any
import json


class Web3ResearchAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = []
        self.agent = None
        self.agent_executor = None

    def _initialize_llm(self):
        """Initialize Gemini LLM"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3,
            convert_system_message_to_human=True,
        )

    def add_tool(self, tool: Tool):
        """Add a tool to the agent"""
        self.tools.append(tool)
        self._rebuild_agent()

    def _rebuild_agent(self):
        """Rebuild agent with current tools"""
        if not self.tools:
            return

        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a Web3 Research Co-Pilot. Your role is to help users research cryptocurrency, DeFi protocols, blockchain data, and Web3 analytics.

You have access to various data sources and should:
1. Understand the user's research question
2. Break down complex queries into steps
3. Use appropriate tools to fetch data
4. Synthesize information from multiple sources
5. Provide clear, actionable insights with source citations

Available tools: {tool_names}

Always cite your data sources and be transparent about limitations of free tier APIs.

Current tools available: {tool_names}
""",
                ),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            return_intermediate_steps=True,
        )

    def research(self, query: str) -> Dict[str, Any]:
        """Process a research query and return structured results"""
        if not self.agent_executor:
            return {
                "answer": "No data sources connected. Please add API tools first.",
                "sources": [],
                "steps": [],
            }

        try:
            # Execute the query
            result = self.agent_executor.invoke(
                {"input": query, "tool_names": [tool.name for tool in self.tools]}
            )

            return {
                "answer": result["output"],
                "sources": self._extract_sources(result),
                "steps": result.get("intermediate_steps", []),
                "success": True,
            }

        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "steps": [],
                "success": False,
                "error": str(e),
            }

    def _extract_sources(self, result: Dict[str, Any]) -> List[str]:
        """Extract data sources used in the research"""
        sources = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if len(step) > 0 and hasattr(step[0], "tool"):
                    sources.append(step[0].tool)
        return list(set(sources))  # Remove duplicates

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
