import requests
import os
from typing import Dict, List, Any, Optional
from langchain.tools import Tool

class ArtemisMCP:
    """Artemis API integration - requires API key (free tier available)"""
    
    def __init__(self):
        self.api_key = os.getenv("ARTEMIS_API_KEY")
        self.base_url = "https://api.artemis.xyz"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        if not self.api_key:
            return {"error": "Artemis API key not configured"}
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
    
    def get_protocol_metrics(self, protocol: str = None, limit: int = 20) -> str:
        """Get protocol metrics and analytics"""
        endpoint = "/protocols" if not protocol else f"/protocols/{protocol.lower()}"
        data = self._make_request(endpoint)
        
        if "error" in data:
            return f"Error fetching protocol metrics: {data['error']}"
        
        if protocol:
            # Single protocol details
            if not data:
                return f"Protocol '{protocol}' not found"
            
            result = f"📊 **{protocol.title()} Protocol Metrics:**\n\n"
            result += f"**TVL:** ${data.get('tvl', 0):,.0f}\n"
            result += f"**Daily Volume:** ${data.get('volume_24h', 0):,.0f}\n"
            result += f"**Active Users (7d):** {data.get('users_7d', 0):,}\n"
            result += f"**Revenue (30d):** ${data.get('revenue_30d', 0):,.0f}\n"
            result += f"**Fees (24h):** ${data.get('fees_24h', 0):,.0f}\n"
            
            if data.get('chains'):
                result += f"**Supported Chains:** {', '.join(data['chains'])}\n"
        
        else:
            # Top protocols
            protocols = sorted(data[:limit], key=lambda x: x.get('tvl', 0), reverse=True)
            result = "🏆 **Top Protocols by Metrics:**\n\n"
            
            for i, proto in enumerate(protocols, 1):
                name = proto.get('name', 'Unknown')
                tvl = proto.get('tvl', 0)
                volume = proto.get('volume_24h', 0)
                users = proto.get('users_7d', 0)
                
                result += f"{i}. **{name}**\n"
                result += f"   - TVL: ${tvl:,.0f}\n"
                result += f"   - Volume: ${volume:,.0f}\n"
                result += f"   - Users: {users:,}\n\n"
        
        return result
    
    def get_chain_activity(self, chain: str = None) -> str:
        """Get blockchain activity metrics"""
        endpoint = "/chains" if not chain else f"/chains/{chain.lower()}"
        data = self._make_request(endpoint)
        
        if "error" in data:
            return f"Error fetching chain data: {data['error']}"
        
        if chain:
            result = f"⛓️ **{chain.title()} Activity:**\n\n"
            result += f"**Daily Transactions:** {data.get('transactions_24h', 0):,}\n"
            result += f"**Active Addresses:** {data.get('active_addresses_24h', 0):,}\n"
            result += f"**Gas Used:** {data.get('gas_used_24h', 0):,}\n"
            result += f"**Average Gas Price:** {data.get('avg_gas_price', 0):.1f} Gwei\n"
            result += f"**Network Fees:** ${data.get('fees_24h', 0):,.0f}\n"
        else:
            chains = data[:10]
            result = "⛓️ **Chain Activity Rankings:**\n\n"
            
            for i, chain_data in enumerate(chains, 1):
                name = chain_data.get('name', 'Unknown')
                txs = chain_data.get('transactions_24h', 0)
                users = chain_data.get('active_addresses_24h', 0)
                
                result += f"{i}. **{name}**: {txs:,} txs, {users:,} users\n"
        
        return result
    
    def get_defi_trends(self) -> str:
        """Get DeFi market trends and insights"""
        data = self._make_request("/trends/defi")
        
        if "error" in data:
            return f"Error fetching DeFi trends: {data['error']}"
        
        result = "📈 **DeFi Market Trends:**\n\n"
        
        if data.get('total_tvl'):
            result += f"**Total DeFi TVL:** ${data['total_tvl']:,.0f}\n"
            result += f"**24h Change:** {data.get('tvl_change_24h', 0):+.2f}%\n\n"
        
        if data.get('trending_protocols'):
            result += "**Trending Protocols:**\n"
            for proto in data['trending_protocols'][:5]:
                name = proto.get('name', 'Unknown')
                change = proto.get('growth_7d', 0)
                result += f"   - {name}: {change:+.1f}% growth\n"
            result += "\n"
        
        if data.get('top_gainers'):
            result += "**Top Gainers (24h):**\n"
            for gainer in data['top_gainers'][:3]:
                name = gainer.get('name', 'Unknown')
                change = gainer.get('change_24h', 0)
                result += f"   - {name}: {change:+.1f}%\n"
        
        return result
    
    def get_protocol_revenue(self, days: int = 30) -> str:
        """Get protocol revenue rankings"""
        data = self._make_request("/analytics/revenue", {"days": days})
        
        if "error" in data:
            return f"Error fetching revenue data: {data['error']}"
        
        result = f"💰 **Protocol Revenue ({days}d):**\n\n"
        
        for i, proto in enumerate(data[:10], 1):
            name = proto.get('name', 'Unknown')
            revenue = proto.get('revenue', 0)
            fees = proto.get('fees', 0)
            
            result += f"{i}. **{name}**\n"
            result += f"   - Revenue: ${revenue:,.0f}\n"
            result += f"   - Fees: ${fees:,.0f}\n"
            result += f"   - Revenue/TVL: {proto.get('revenue_tvl_ratio', 0):.2%}\n\n"
        
        return result
    
    def get_tools(self) -> List[Tool]:
        """Return LangChain tools for this MCP"""
        return [
            Tool(
                name="get_artemis_protocol_metrics",
                description="Get protocol metrics and analytics from Artemis. Input: protocol name (optional) or 'all' for rankings",
                func=lambda query: self.get_protocol_metrics(query if query and query != 'all' else None)
            ),
            Tool(
                name="get_chain_activity_artemis",
                description="Get blockchain activity metrics including transactions, users, and fees. Input: chain name or 'all'",
                func=lambda query: self.get_chain_activity(query if query and query != 'all' else None)
            ),
            Tool(
                name="get_defi_market_trends",
                description="Get current DeFi market trends, trending protocols, and top gainers",
                func=lambda _: self.get_defi_trends()
            ),
            Tool(
                name="get_protocol_revenue_rankings",
                description="Get protocol revenue rankings. Input: number of days (default 30)",
                func=lambda days: self.get_protocol_revenue(int(days) if days.isdigit() else 30)
            )
        ]