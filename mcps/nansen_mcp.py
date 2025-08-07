import requests
import os
from typing import Dict, List, Any, Optional
from langchain.tools import Tool

class NansenMCP:
    """Nansen API integration - requires API key (7-day trial available)"""
    
    def __init__(self):
        self.api_key = os.getenv("NANSEN_API_KEY")
        self.base_url = "https://api.nansen.ai/v1"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        if not self.api_key:
            return {"error": "Nansen API key not configured"}
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
    
    def analyze_wallet_intelligence(self, address: str) -> str:
        """Get wallet intelligence and labeling data"""
        data = self._make_request(f"/wallets/{address}/intelligence")
        
        if "error" in data:
            return f"Error analyzing wallet: {data['error']}"
        
        if not data:
            return f"No intelligence data found for {address[:10]}...{address[-8:]}"
        
        result = f"🧠 **Wallet Intelligence: {address[:10]}...{address[-8:]}**\n\n"
        
        # Wallet labels
        if data.get('labels'):
            result += "**Labels:**\n"
            for label in data['labels']:
                confidence = label.get('confidence', 0)
                result += f"   - {label.get('name', 'Unknown')}: {confidence:.1%} confidence\n"
            result += "\n"
        
        # Wallet scoring
        if data.get('smart_money_score'):
            score = data['smart_money_score']
            result += f"**Smart Money Score:** {score:.1f}/100\n"
            
            if score > 80:
                result += "   - 🔥 Elite trader/investor\n"
            elif score > 60:
                result += "   - 🟢 Above average performance\n"
            elif score > 40:
                result += "   - 🟡 Average performance\n"
            else:
                result += "   - 🔴 Below average performance\n"
            result += "\n"
        
        # Portfolio value
        if data.get('portfolio_value'):
            result += f"**Portfolio Value:** ${data['portfolio_value']:,.0f}\n"
        
        # Activity metrics
        if data.get('activity'):
            activity = data['activity']
            result += f"**Activity (30d):**\n"
            result += f"   - Transactions: {activity.get('transactions', 0):,}\n"
            result += f"   - Volume: ${activity.get('volume_usd', 0):,.0f}\n"
            result += f"   - Profit/Loss: ${activity.get('pnl_usd', 0):+,.0f}\n"
        
        return result
    
    def get_smart_money_flows(self, token_address: str = None) -> str:
        """Get smart money flows for tokens"""
        endpoint = "/smart-money/flows"
        params = {"token": token_address} if token_address else {"limit": 10}
        
        data = self._make_request(endpoint, params)
        
        if "error" in data:
            return f"Error fetching smart money flows: {data['error']}"
        
        flows = data.get('flows', [])
        if not flows:
            return "No smart money flows data available"
        
        result = "💰 **Smart Money Flows:**\n\n"
        
        for flow in flows[:10]:
            token = flow.get('token', {})
            direction = flow.get('direction', 'unknown')
            amount = flow.get('amount_usd', 0)
            wallet_count = flow.get('wallet_count', 0)
            
            emoji = "📈" if direction == "in" else "📉"
            result += f"{emoji} **{token.get('symbol', 'Unknown')}**\n"
            result += f"   - Flow: ${amount:,.0f} ({direction}bound)\n"
            result += f"   - Smart wallets: {wallet_count}\n"
            result += f"   - Token: {token.get('name', 'Unknown')}\n\n"
        
        return result
    
    def get_whale_tracking(self, min_value: int = 1000000) -> str:
        """Track whale movements and large transactions"""
        data = self._make_request("/whales/movements", {"min_value_usd": min_value})
        
        if "error" in data:
            return f"Error tracking whales: {data['error']}"
        
        movements = data.get('movements', [])
        if not movements:
            return f"No whale movements above ${min_value:,} found"
        
        result = f"🐋 **Whale Movements (>${min_value:,}):**\n\n"
        
        for movement in movements[:8]:
            token = movement.get('token', {})
            from_addr = movement.get('from_address', '')
            to_addr = movement.get('to_address', '')
            value = movement.get('value_usd', 0)
            tx_type = movement.get('type', 'transfer')
            
            result += f"**${value:,.0f} {token.get('symbol', 'Unknown')} Move**\n"
            result += f"   - From: {from_addr[:10]}...{from_addr[-6:] if from_addr else ''}\n"
            result += f"   - To: {to_addr[:10]}...{to_addr[-6:] if to_addr else ''}\n"
            result += f"   - Type: {tx_type.title()}\n"
            result += f"   - Time: {movement.get('timestamp', 'Unknown')}\n\n"
        
        return result
    
    def get_token_holders_analysis(self, token_address: str) -> str:
        """Analyze token holder distribution and smart money involvement"""
        data = self._make_request(f"/tokens/{token_address}/holders")
        
        if "error" in data:
            return f"Error analyzing token holders: {data['error']}"
        
        if not data:
            return f"No holder data found for token {token_address[:10]}..."
        
        result = f"👥 **Token Holder Analysis: {token_address[:10]}...**\n\n"
        
        # Smart money stats
        if data.get('smart_money_stats'):
            stats = data['smart_money_stats']
            result += "**Smart Money Involvement:**\n"
            result += f"   - Smart wallets holding: {stats.get('smart_holders_count', 0)}\n"
            result += f"   - Smart money %: {stats.get('smart_money_percentage', 0):.1%}\n"
            result += f"   - Avg holding size: ${stats.get('avg_holding_usd', 0):,.0f}\n\n"
        
        # Top holders
        if data.get('top_holders'):
            result += "**Top Holders:**\n"
            for i, holder in enumerate(data['top_holders'][:5], 1):
                addr = holder.get('address', '')
                balance = holder.get('balance_usd', 0)
                percentage = holder.get('percentage', 0)
                label = holder.get('label', 'Unknown')
                
                result += f"{i}. {addr[:10]}...{addr[-6:]} ({label})\n"
                result += f"   - Value: ${balance:,.0f} ({percentage:.1%})\n"
        
        # Distribution metrics
        if data.get('distribution'):
            dist = data['distribution']
            result += f"\n**Distribution Metrics:**\n"
            result += f"   - Total holders: {dist.get('total_holders', 0):,}\n"
            result += f"   - Top 10 hold: {dist.get('top_10_percentage', 0):.1%}\n"
            result += f"   - Gini coefficient: {dist.get('gini', 0):.2f}\n"
        
        return result
    
    def get_trending_tokens(self) -> str:
        """Get trending tokens based on smart money activity"""
        data = self._make_request("/trending/tokens")
        
        if "error" in data:
            return f"Error fetching trending tokens: {data['error']}"
        
        tokens = data.get('tokens', [])
        if not tokens:
            return "No trending tokens data available"
        
        result = "🔥 **Trending Tokens (Smart Money Activity):**\n\n"
        
        for token in tokens[:8]:
            name = token.get('name', 'Unknown')
            symbol = token.get('symbol', 'Unknown')
            smart_money_flow = token.get('smart_money_flow_24h', 0)
            price_change = token.get('price_change_24h', 0)
            smart_wallets = token.get('smart_wallets_count', 0)
            
            result += f"**{name} ({symbol})**\n"
            result += f"   - Smart money flow: ${smart_money_flow:+,.0f}\n"
            result += f"   - Price change: {price_change:+.1f}%\n"
            result += f"   - Smart wallets involved: {smart_wallets}\n\n"
        
        return result
    
    def get_tools(self) -> List[Tool]:
        """Return LangChain tools for this MCP"""
        return [
            Tool(
                name="analyze_wallet_nansen",
                description="Get detailed wallet intelligence including labels, smart money score, and activity. Input: wallet address",
                func=self.analyze_wallet_intelligence
            ),
            Tool(
                name="get_smart_money_flows_nansen",
                description="Get smart money flows for tokens. Input: token address (optional)",
                func=lambda token: self.get_smart_money_flows(token if token and len(token) > 10 else None)
            ),
            Tool(
                name="track_whale_movements",
                description="Track large whale movements and transactions. Input: minimum USD value (default 1000000)",
                func=lambda min_val: self.get_whale_tracking(int(min_val) if min_val.isdigit() else 1000000)
            ),
            Tool(
                name="analyze_token_holders_nansen",
                description="Analyze token holder distribution and smart money involvement. Input: token contract address",
                func=self.get_token_holders_analysis
            ),
            Tool(
                name="get_trending_tokens_nansen",
                description="Get trending tokens based on smart money activity and flows",
                func=lambda _: self.get_trending_tokens()
            )
        ]