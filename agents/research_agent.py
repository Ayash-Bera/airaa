import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain import hub
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
        )

    def add_tool(self, tool: Tool):
        """Add a tool to the agent"""
        self.tools.append(tool)
        self._rebuild_agent()

    def _rebuild_agent(self):
        """Rebuild agent with current tools"""
        if not self.tools:
            return

        # Get tool names and descriptions
        tool_names = [tool.name for tool in self.tools]
        tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

        # Use ReAct agent with correct prompt variables
        prompt = PromptTemplate.from_template("""
You are a Web3 Research Co-Pilot. Answer questions about cryptocurrency, DeFi, and blockchain data using the available tools.

TOOLS:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
""")

        # Create ReAct agent
        self.agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
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
            result = self.agent_executor.invoke({
                "input": query,
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            })

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