import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
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
        """Initialize Gemini LLM with longer timeout"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.2,
            timeout=120,  # Increased timeout
            max_retries=3,
        )

    def add_tool(self, tool: Tool):
        """Add a tool to the agent"""
        self.tools.append(tool)
        self._rebuild_agent()

    def _rebuild_agent(self):
        """Rebuild agent with current tools"""
        if not self.tools:
            return

        # Get available tool names for validation
        available_tools = [tool.name for tool in self.tools]
        tool_list = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])

        prompt = PromptTemplate.from_template("""You are a Web3 Research Co-Pilot. Answer questions using available tools efficiently.

AVAILABLE TOOLS:
{tools}

TOOL NAMES: {tool_names}

RULES:
1. Choose the RIGHT tool for each specific task
2. For gas prices specifically, use "get_gas_prices" 
3. For Ethereum stats/price, use "get_ethereum_stats"
4. Don't repeat the same tool call - use different tools or give final answer
5. If you have enough information, provide the Final Answer immediately

Format:
Question: the input question  
Thought: what specific information do I need and which tool to use
Action: [exact tool name from list]
Action Input: [specific input needed]
Observation: [result]
Thought: do I have enough information now? 
Final Answer: [complete answer with all requested data]

Question: {input}
{agent_scratchpad}""")

        self.agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=4,  # Reduced to prevent loops
            max_execution_time=60,
            return_intermediate_steps=True,
            early_stopping_method="force"  # Forces stop after max iterations
        )

    def research(self, query: str) -> Dict[str, Any]:
        """Process research query with better error handling"""
        if not self.agent_executor:
            return {
                "answer": "No data sources connected. Please add API tools first.",
                "sources": [],
                "steps": [],
                "success": False
            }

        try:
            # Prepare input with available tools
            available_tools = [tool.name for tool in self.tools]
            tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            
            result = self.agent_executor.invoke({
                "input": query
            })

            # Extract answer
            answer = result.get("output", "No response generated")
            
            # Clean up answer if it contains reasoning
            if "Final Answer:" in answer:
                answer = answer.split("Final Answer:")[-1].strip()

            return {
                "answer": answer,
                "sources": self._extract_sources(result),
                "steps": result.get("intermediate_steps", []),
                "success": True,
                "available_tools": available_tools
            }

        except Exception as e:
            error_msg = str(e)
            
            # Handle specific errors
            if "not found" in error_msg.lower():
                return {
                    "answer": f"Tool execution failed. Available tools: {', '.join([t.name for t in self.tools])}",
                    "sources": [],
                    "steps": [],
                    "success": False,
                    "error": error_msg
                }
            
            return {
                "answer": f"Research failed: {error_msg}",
                "sources": [],
                "steps": [],
                "success": False,
                "error": error_msg
            }

    def _extract_sources(self, result: Dict[str, Any]) -> List[str]:
        """Extract data sources from intermediate steps"""
        sources = set()
        
        for step in result.get("intermediate_steps", []):
            if len(step) >= 2:
                action = step[0]
                if hasattr(action, 'tool'):
                    # Map tool names to source names
                    tool_name = action.tool
                    if 'defillama' in tool_name.lower():
                        sources.add("DeFiLlama")
                    elif 'etherscan' in tool_name.lower():
                        sources.add("Etherscan")
                    elif 'coinmarketcap' in tool_name.lower():
                        sources.add("CoinMarketCap")
                    elif 'artemis' in tool_name.lower():
                        sources.add("Artemis")
                    elif 'dune' in tool_name.lower():
                        sources.add("Dune Analytics")
                    elif 'nansen' in tool_name.lower():
                        sources.add("Nansen")
                    else:
                        sources.add(tool_name)
        
        return list(sources)

    def get_available_tools(self) -> List[str]:
        """Get available tool names"""
        return [tool.name for tool in self.tools]

    def get_tool_info(self) -> Dict[str, str]:
        """Get tool names and descriptions"""
        return {tool.name: tool.description for tool in self.tools}