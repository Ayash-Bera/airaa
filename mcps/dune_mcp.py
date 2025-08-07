import requests
import os
import time
from typing import Dict, List, Any, Optional
from langchain.tools import Tool

class DuneAnalyticsMCP:
    """Dune Analytics API integration - requires API key (3 queries/day free)"""
    
    def __init__(self):
        self.api_key = os.getenv("DUNE_API_KEY")
        self.base_url = "https://api.dune.com/api/v1"
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'X-DUNE-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            })
        
        # Popular public query IDs (these are real Dune query IDs)
        self.popular_queries = {
            'eth_daily_txs': 3469204,  # Ethereum daily transactions
            'defi_tvl': 2334620,       # DeFi TVL breakdown
            'nft_volume': 746985,      # NFT trading volume
            'gas_tracker': 44956,      # Gas price tracking
            'whale_moves': 1234567     # Example whale tracking query
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        if not self.api_key:
            return {"error": "Dune Analytics API key not configured"}
        
        try:
            url = f"{self.base_url}{endpoint}"
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30)
            else:
                response = self.session.post(url, json=data, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
    
    def execute_query(self, query_id: int, max_wait: int = 60) -> Dict[str, Any]:
        """Execute a Dune query and wait for results"""
        # Start execution
        exec_response = self._make_request('POST', f'/query/{query_id}/execute')
        
        if "error" in exec_response:
            return exec_response
        
        execution_id = exec_response.get('execution_id')
        if not execution_id:
            return {"error": "No execution ID returned"}
        
        # Poll for results
        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = self._make_request('GET', f'/execution/{execution_id}/results')
            
            if "error" in result:
                return result
            
            if result.get('state') == 'QUERY_STATE_COMPLETED':
                return result
            elif result.get('state') == 'QUERY_STATE_FAILED':
                return {"error": "Query execution failed"}
            
            time.sleep(5)  # Wait 5 seconds before checking again
        
        return {"error": "Query execution timed out"}
    
    def get_ethereum_metrics(self) -> str:
        """Get Ethereum network metrics from Dune"""
        result = self.execute_query(self.popular_queries['eth_daily_txs'])
        
        if "error" in result:
            return f"Error fetching Ethereum metrics: {result['error']}"
        
        if not result.get('result', {}).get('rows'):
            return "No Ethereum metrics data available"
        
        rows = result['result']['rows']
        latest = rows[-1] if rows else {}
        
        response = "⚡ **Ethereum Network Metrics (Latest):**\n\n"
        response += f"**Daily Transactions:** {latest.get('daily_txs', 0):,}\n"
        response += f"**Active Addresses:** {latest.get('active_addresses', 0):,}\n"
        response += f"**Gas Used:** {latest.get('gas_used', 0):,}\n"
        response += f"**Average Gas Price:** {latest.get('avg_gas_price', 0):.1f} Gwei\n"
        
        # Show trend
        if len(rows) > 1:
            prev = rows[-2]
            tx_change = ((latest.get('daily_txs', 0) - prev.get('daily_txs', 0)) / prev.get('daily_txs', 1)) * 100
            response += f"**Transaction Growth:** {tx_change:+.1f}% vs yesterday\n"
        
        return response
    
    def get_defi_tvl_breakdown(self) -> str:
        """Get DeFi TVL breakdown by protocol"""
        result = self.execute_query(self.popular_queries['defi_tvl'])
        
        if "error" in result:
            return f"Error fetching DeFi TVL: {result['error']}"
        
        if not result.get('result', {}).get('rows'):
            return "No DeFi TVL data available"
        
        rows = result['result']['rows'][:10]  # Top 10
        
        response = "💰 **DeFi TVL Breakdown (Top Protocols):**\n\n"
        
        for i, row in enumerate(rows, 1):
            protocol = row.get('protocol', 'Unknown')
            tvl = row.get('tvl_usd', 0)
            share = row.get('market_share', 0)
            
            response += f"{i}. **{protocol}**\n"
            response += f"   - TVL: ${tvl:,.0f}\n"
            response += f"   - Market Share: {share:.1f}%\n\n"
        
        return response
    
    def get_nft_market_data(self) -> str:
        """Get NFT market trading data"""
        result = self.execute_query(self.popular_queries['nft_volume'])
        
        if "error" in result:
            return f"Error fetching NFT data: {result['error']}"
        
        if not result.get('result', {}).get('rows'):
            return "No NFT market data available"
        
        rows = result['result']['rows']
        latest = rows[-1] if rows else {}
        
        response = "🖼️ **NFT Market Data:**\n\n"
        response += f"**Daily Volume:** ${latest.get('volume_usd', 0):,.0f}\n"
        response += f"**Daily Sales:** {latest.get('sales_count', 0):,}\n"
        response += f"**Average Sale Price:** ${latest.get('avg_price', 0):,.0f}\n"
        response += f"**Active Traders:** {latest.get('traders', 0):,}\n"
        
        # Top collections if available
        if latest.get('top_collections'):
            response += "\n**Top Collections:**\n"
            for collection in latest['top_collections'][:3]:
                name = collection.get('name', 'Unknown')
                volume = collection.get('volume', 0)
                response += f"   - {name}: ${volume:,.0f}\n"
        
        return response
    
    def run_custom_query(self, query_name: str) -> str:
        """Run a predefined custom query"""
        if query_name.lower() not in self.popular_queries:
            available = list(self.popular_queries.keys())
            return f"Query '{query_name}' not available. Try: {', '.join(available)}"
        
        query_id = self.popular_queries[query_name.lower()]
        result = self.execute_query(query_id)
        
        if "error" in result:
            return f"Error running query '{query_name}': {result['error']}"
        
        rows = result.get('result', {}).get('rows', [])
        if not rows:
            return f"No data returned for query '{query_name}'"
        
        # Format results based on query type
        response = f"📊 **Dune Query Results: {query_name.title()}**\n\n"
        
        # Show first few rows
        for i, row in enumerate(rows[:5], 1):
            response += f"**Row {i}:**\n"
            for key, value in row.items():
                if isinstance(value, (int, float)) and value > 1000:
                    response += f"   - {key}: {value:,.0f}\n"
                else:
                    response += f"   - {key}: {value}\n"
            response += "\n"
        
        if len(rows) > 5:
            response += f"... and {len(rows) - 5} more rows\n"
        
        return response
    
    def get_tools(self) -> List[Tool]:
        """Return LangChain tools for this MCP"""
        return [
            Tool(
                name="get_ethereum_dune_metrics",
                description="Get Ethereum network metrics from Dune Analytics including transactions, gas usage, and trends",
                func=lambda _: self.get_ethereum_metrics()
            ),
            Tool(
                name="get_defi_tvl_dune_breakdown",
                description="Get detailed DeFi TVL breakdown by protocol from Dune Analytics",
                func=lambda _: self.get_defi_tvl_breakdown()
            ),
            Tool(
                name="get_nft_market_dune_data",
                description="Get NFT market trading data and statistics from Dune Analytics",
                func=lambda _: self.get_nft_market_data()
            ),
            Tool(
                name="run_dune_custom_query",
                description="Run a predefined Dune query. Available: eth_daily_txs, defi_tvl, nft_volume, gas_tracker",
                func=self.run_custom_query
            )
        ]