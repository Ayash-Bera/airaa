import requests
import json
from typing import Dict, List, Any, Optional
from langchain.tools import Tool


class DeFiLlamaMCP:
    """DeFiLlama API integration - No API key required"""

    def __init__(self):
        self.base_url = "https://api.llama.fi"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Web3-Research-Copilot/1.0"})

    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def get_protocols(self, limit: int = 20) -> str:
        """Get top DeFi protocols by TVL"""
        data = self._make_request("/protocols")

        if "error" in data:
            return f"Error fetching protocols: {data['error']}"

        # Sort by TVL and limit results
        protocols = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:limit]

        result = "🏆 **Top DeFi Protocols by TVL:**\n\n"
        for i, protocol in enumerate(protocols, 1):
            name = protocol.get("name", "Unknown")
            tvl = protocol.get("tvl", 0)
            change_1d = protocol.get("change_1d", 0)
            category = protocol.get("category", "Unknown")

            result += f"{i}. **{name}**\n"
            result += f"   - TVL: ${tvl:,.0f}\n"
            result += f"   - 24h Change: {change_1d:+.2f}%\n"
            result += f"   - Category: {category}\n\n"

        return result

    def get_protocol_info(self, protocol_name: str) -> str:
        """Get detailed information about a specific protocol"""
        # First get all protocols to find the slug
        data = self._make_request("/protocols")

        if "error" in data:
            return f"Error fetching protocol data: {data['error']}"

        # Find protocol by name (case insensitive)
        protocol = None
        for p in data:
            if protocol_name.lower() in p.get("name", "").lower():
                protocol = p
                break

        if not protocol:
            return (
                f"Protocol '{protocol_name}' not found. Try searching for exact name."
            )

        # Get detailed protocol data
        slug = protocol.get("slug")
        if slug:
            detailed_data = self._make_request(f"/protocol/{slug}")
            if "error" not in detailed_data:
                protocol.update(detailed_data)

        result = f"📊 **{protocol.get('name', 'Unknown')} Analysis:**\n\n"
        result += f"**Current TVL:** ${protocol.get('tvl', 0):,.0f}\n"
        result += f"**24h Change:** {protocol.get('change_1d', 0):+.2f}%\n"
        result += f"**7d Change:** {protocol.get('change_7d', 0):+.2f}%\n"
        result += f"**Category:** {protocol.get('category', 'Unknown')}\n"

        if "description" in protocol:
            result += f"**Description:** {protocol['description'][:200]}...\n"

        if "chains" in protocol:
            result += f"**Chains:** {', '.join(protocol['chains'])}\n"

        return result

    def get_chain_tvl(self, chain_name: Optional[str] = None) -> str:
        """Get TVL data for blockchains"""
        data = self._make_request("/chains")

        if "error" in data:
            return f"Error fetching chain data: {data['error']}"

        if chain_name:
            # Find specific chain
            chain = None
            for c in data:
                if chain_name.lower() in c.get("name", "").lower():
                    chain = c
                    break

            if not chain:
                return f"Chain '{chain_name}' not found."

            result = f"⛓️ **{chain.get('name', 'Unknown')} TVL Analysis:**\n\n"
            result += f"**Current TVL:** ${chain.get('tvl', 0):,.0f}\n"
            result += f"**24h Change:** {chain.get('change_1d', 0):+.2f}%\n"
            result += f"**7d Change:** {chain.get('change_7d', 0):+.2f}%\n"

        else:
            # Top chains by TVL
            chains = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:10]

            result = "⛓️ **Top Blockchains by TVL:**\n\n"
            for i, chain in enumerate(chains, 1):
                name = chain.get("name", "Unknown")
                tvl = chain.get("tvl", 0)
                change_1d = chain.get("change_1d", 0)

                result += f"{i}. **{name}**: ${tvl:,.0f} ({change_1d:+.2f}%)\n"

        return result

    def get_yields(self, min_apy: float = 5.0, limit: int = 10) -> str:
        """Get yield farming opportunities"""
        data = self._make_request("/yields")

        if "error" in data:
            return f"Error fetching yields: {data['error']}"

        # Filter and sort yields
        yields = data.get("data", [])
        filtered_yields = [
            y
            for y in yields
            if y.get("apy", 0) >= min_apy and y.get("tvlUsd", 0) > 100000
        ]

        # Sort by APY
        sorted_yields = sorted(
            filtered_yields, key=lambda x: x.get("apy", 0), reverse=True
        )[:limit]

        result = f"💰 **High Yield Opportunities (>{min_apy}% APY):**\n\n"

        for i, pool in enumerate(sorted_yields, 1):
            protocol = pool.get("project", "Unknown")
            apy = pool.get("apy", 0)
            tvl = pool.get("tvlUsd", 0)
            symbol = pool.get("symbol", "Unknown")
            chain = pool.get("chain", "Unknown")

            result += f"{i}. **{protocol}** ({chain})\n"
            result += f"   - Pool: {symbol}\n"
            result += f"   - APY: {apy:.2f}%\n"
            result += f"   - TVL: ${tvl:,.0f}\n\n"

        return result

    def get_tools(self) -> List[Tool]:
        """Return LangChain tools for this MCP"""
        return [
            Tool(
                name="get_defi_protocols",
                description="Get top DeFi protocols by Total Value Locked (TVL). Useful for protocol rankings and comparisons.",
                func=lambda query: self.get_protocols(
                    limit=int(query) if query.isdigit() else 20
                ),
            ),
            Tool(
                name="analyze_defi_protocol",
                description="Get detailed analysis of a specific DeFi protocol including TVL, changes, and description. Input should be protocol name.",
                func=self.get_protocol_info,
            ),
            Tool(
                name="get_blockchain_tvl",
                description="Get TVL data for blockchains. Leave empty for top chains, or specify chain name for specific data.",
                func=self.get_chain_tvl,
            ),
            Tool(
                name="find_yield_opportunities",
                description="Find high-yield farming opportunities in DeFi. Shows pools with good APY and reasonable TVL.",
                func=lambda query: self.get_yields(
                    min_apy=float(query) if query.replace(".", "").isdigit() else 5.0
                ),
            ),
        ]
