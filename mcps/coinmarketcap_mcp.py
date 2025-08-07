import requests
import os
from typing import Dict, List, Any, Optional
from langchain.tools import Tool


class CoinMarketCapMCP:
    """CoinMarketCap API integration - requires API key (10K calls/month free)"""

    def __init__(self):
        self.api_key = os.getenv("COINMARKETCAP_API_KEY")
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-CMC_PRO_API_KEY": self.api_key,
                "Accept": "application/json",
            }
        )

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        if not self.api_key:
            return {"error": "CoinMarketCap API key not configured"}

        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}", params=params, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def get_top_cryptocurrencies(self, limit: int = 20) -> str:
        """Get top cryptocurrencies by market cap"""
        data = self._make_request(
            "/cryptocurrency/listings/latest", {"limit": limit, "convert": "USD"}
        )

        if "error" in data:
            return f"Error fetching crypto data: {data['error']}"

        if "data" not in data:
            return "No cryptocurrency data available"

        result = "💰 **Top Cryptocurrencies by Market Cap:**\n\n"

        for crypto in data["data"]:
            name = crypto.get("name", "Unknown")
            symbol = crypto.get("symbol", "")
            price = crypto["quote"]["USD"].get("price", 0)
            market_cap = crypto["quote"]["USD"].get("market_cap", 0)
            change_24h = crypto["quote"]["USD"].get("percent_change_24h", 0)
            volume_24h = crypto["quote"]["USD"].get("volume_24h", 0)

            result += f"**{name} ({symbol})**\n"
            result += f"   - Price: ${price:.4f}\n"
            result += f"   - Market Cap: ${market_cap:,.0f}\n"
            result += f"   - 24h Change: {change_24h:+.2f}%\n"
            result += f"   - 24h Volume: ${volume_24h:,.0f}\n\n"

        return result

    def get_cryptocurrency_info(self, symbol: str) -> str:
        """Get detailed info about a specific cryptocurrency"""
        # First get the ID from symbol
        data = self._make_request("/cryptocurrency/map", {"symbol": symbol.upper()})

        if "error" in data:
            return f"Error fetching crypto info: {data['error']}"

        if not data.get("data"):
            return f"Cryptocurrency '{symbol}' not found"

        crypto_id = data["data"][0]["id"]

        # Get quotes
        quote_data = self._make_request(
            "/cryptocurrency/quotes/latest", {"id": crypto_id, "convert": "USD"}
        )

        # Get metadata
        info_data = self._make_request("/cryptocurrency/info", {"id": crypto_id})

        if "error" in quote_data or "error" in info_data:
            return f"Error fetching detailed data for {symbol}"

        crypto = quote_data["data"][str(crypto_id)]
        info = info_data["data"][str(crypto_id)]

        result = f"📊 **{crypto['name']} ({crypto['symbol']}) Analysis:**\n\n"

        quote = crypto["quote"]["USD"]
        result += f"**Price:** ${quote.get('price', 0):.6f}\n"
        result += f"**Market Cap:** ${quote.get('market_cap', 0):,.0f}\n"
        result += f"**Volume (24h):** ${quote.get('volume_24h', 0):,.0f}\n"
        result += f"**Circulating Supply:** {crypto.get('circulating_supply', 0):,.0f} {crypto['symbol']}\n"
        result += f"**Max Supply:** {crypto.get('max_supply') or 'Unlimited'}\n\n"

        result += "**Price Changes:**\n"
        result += f"   - 1h: {quote.get('percent_change_1h', 0):+.2f}%\n"
        result += f"   - 24h: {quote.get('percent_change_24h', 0):+.2f}%\n"
        result += f"   - 7d: {quote.get('percent_change_7d', 0):+.2f}%\n"
        result += f"   - 30d: {quote.get('percent_change_30d', 0):+.2f}%\n\n"

        if info.get("description"):
            result += f"**Description:** {info['description'][:300]}...\n\n"

        if info.get("urls", {}).get("website"):
            result += f"**Website:** {info['urls']['website'][0]}\n"

        return result

    def get_trending_cryptocurrencies(self) -> str:
        """Get trending cryptocurrencies by volume and price changes"""
        data = self._make_request(
            "/cryptocurrency/listings/latest",
            {"limit": 100, "sort": "percent_change_24h", "convert": "USD"},
        )

        if "error" in data:
            return f"Error fetching trending data: {data['error']}"

        # Filter for significant gainers with decent volume
        gainers = [
            crypto
            for crypto in data.get("data", [])
            if crypto["quote"]["USD"].get("percent_change_24h", 0) > 5
            and crypto["quote"]["USD"].get("volume_24h", 0) > 1000000
        ][:10]

        result = "📈 **Trending Cryptocurrencies (24h Gainers):**\n\n"

        for crypto in gainers:
            name = crypto.get("name", "Unknown")
            symbol = crypto.get("symbol", "")
            price = crypto["quote"]["USD"].get("price", 0)
            change_24h = crypto["quote"]["USD"].get("percent_change_24h", 0)
            volume_24h = crypto["quote"]["USD"].get("volume_24h", 0)

            result += f"**{name} ({symbol})**\n"
            result += f"   - Price: ${price:.6f}\n"
            result += f"   - 24h Change: {change_24h:+.2f}%\n"
            result += f"   - 24h Volume: ${volume_24h:,.0f}\n\n"

        return result

    def get_global_metrics(self) -> str:
        """Get global cryptocurrency market metrics"""
        data = self._make_request("/global-metrics/quotes/latest", {"convert": "USD"})

        if "error" in data:
            return f"Error fetching global metrics: {data['error']}"

        metrics = data.get("data", {})
        quote = metrics.get("quote", {}).get("USD", {})

        result = "🌍 **Global Crypto Market Metrics:**\n\n"
        result += f"**Total Market Cap:** ${quote.get('total_market_cap', 0):,.0f}\n"
        result += f"**24h Volume:** ${quote.get('total_volume_24h', 0):,.0f}\n"
        result += f"**Bitcoin Dominance:** {metrics.get('btc_dominance', 0):.1f}%\n"
        result += f"**Ethereum Dominance:** {metrics.get('eth_dominance', 0):.1f}%\n"
        result += f"**Active Cryptocurrencies:** {metrics.get('active_cryptocurrencies', 0):,}\n"
        result += f"**Active Exchanges:** {metrics.get('active_exchanges', 0):,}\n\n"

        result += "**Market Changes:**\n"
        result += f"   - 24h Change: {quote.get('total_market_cap_yesterday_percentage_change', 0):+.2f}%\n"

        return result

    def get_tools(self) -> List[Tool]:
        """Return LangChain tools for this MCP"""
        return [
            Tool(
                name="get_top_cryptocurrencies",
                description="Get top cryptocurrencies by market cap with prices, changes, and volumes. Input: number limit (default 20)",
                func=lambda query: self.get_top_cryptocurrencies(
                    limit=int(query) if query.isdigit() else 20
                ),
            ),
            Tool(
                name="analyze_cryptocurrency",
                description="Get detailed analysis of a specific cryptocurrency including price, market cap, supply, and description. Input: crypto symbol (e.g., BTC, ETH)",
                func=self.get_cryptocurrency_info,
            ),
            Tool(
                name="get_trending_crypto",
                description="Get trending cryptocurrencies with significant 24h gains and good volume",
                func=lambda _: self.get_trending_cryptocurrencies(),
            ),
            Tool(
                name="get_global_crypto_metrics",
                description="Get global cryptocurrency market metrics including total market cap, volume, and dominance",
                func=lambda _: self.get_global_metrics(),
            ),
        ]
