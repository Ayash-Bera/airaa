import requests
import os
from typing import Dict, List, Any, Optional
from langchain.tools import Tool


class EtherscanMCP:
    """Etherscan API integration - requires API key (100K calls/day free)"""

    def __init__(self):
        self.api_key = os.getenv("ETHERSCAN_API_KEY")
        self.base_url = "https://api.etherscan.io/api"
        self.session = requests.Session()

    def _make_request(self, params: Dict) -> Dict[str, Any]:
        """Make API request with error handling"""
        if not self.api_key:
            return {"error": "Etherscan API key not configured"}

        params["apikey"] = self.api_key

        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "0":
                return {"error": data.get("message", "Unknown error")}

            return data
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def get_ethereum_stats(self) -> str:
        """Get Ethereum network statistics"""
        # Get ETH price
        price_data = self._make_request({"module": "stats", "action": "ethprice"})

        # Get ETH supply
        supply_data = self._make_request({"module": "stats", "action": "ethsupply"})

        if "error" in price_data or "error" in supply_data:
            return "Error fetching Ethereum stats"

        eth_price = float(price_data.get("result", {}).get("ethusd", 0))
        eth_supply = int(supply_data.get("result", 0)) / 10**18  # Convert from wei

        result = "⚡ **Ethereum Network Statistics:**\n\n"
        result += f"**ETH Price:** ${eth_price:.2f}\n"
        result += f"**Total Supply:** {eth_supply:,.0f} ETH\n"
        result += f"**Market Cap:** ${eth_price * eth_supply:,.0f}\n"

        return result

    def analyze_wallet(self, address: str) -> str:
        """Analyze an Ethereum wallet address"""
        # Get ETH balance
        balance_data = self._make_request(
            {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
            }
        )

        # Get transaction count
        tx_count_data = self._make_request(
            {
                "module": "proxy",
                "action": "eth_getTransactionCount",
                "address": address,
                "tag": "latest",
            }
        )

        if "error" in balance_data:
            return f"Error analyzing wallet: {balance_data['error']}"

        balance_wei = int(balance_data.get("result", 0))
        balance_eth = balance_wei / 10**18
        tx_count = int(tx_count_data.get("result", "0x0"), 16)

        result = f"👛 **Wallet Analysis: {address[:10]}...{address[-8:]}**\n\n"
        result += f"**ETH Balance:** {balance_eth:.4f} ETH\n"
        result += f"**Transaction Count:** {tx_count:,}\n"

        # Categorize wallet activity
        if tx_count > 10000:
            activity = "🔥 Very Active"
        elif tx_count > 1000:
            activity = "🟢 Active"
        elif tx_count > 100:
            activity = "🟡 Moderate"
        elif tx_count > 10:
            activity = "🔵 Light"
        else:
            activity = "⚪ New/Inactive"

        result += f"**Activity Level:** {activity}\n"

        return result

    def get_recent_transactions(self, address: str, limit: int = 10) -> str:
        """Get recent transactions for an address"""
        data = self._make_request(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )

        if "error" in data:
            return f"Error fetching transactions: {data['error']}"

        transactions = data.get("result", [])

        if not transactions:
            return f"No transactions found for {address[:10]}...{address[-8:]}"

        result = f"📋 **Recent Transactions for {address[:10]}...{address[-8:]}:**\n\n"

        for tx in transactions:
            value_eth = int(tx.get("value", 0)) / 10**18
            gas_used = int(tx.get("gasUsed", 0))
            gas_price = int(tx.get("gasPrice", 0)) / 10**9  # Gwei

            result += f"**Hash:** {tx.get('hash', '')[:16]}...\n"
            result += (
                f"**From:** {tx.get('from', '')[:10]}...{tx.get('from', '')[-8:]}\n"
            )
            result += f"**To:** {tx.get('to', '')[:10]}...{tx.get('to', '')[-8:]}\n"
            result += f"**Value:** {value_eth:.4f} ETH\n"
            result += f"**Gas:** {gas_used:,} @ {gas_price:.1f} Gwei\n\n"

        return result

    def get_gas_tracker(self) -> str:
        """Get current gas prices"""
        data = self._make_request({"module": "gastracker", "action": "gasoracle"})

        if "error" in data:
            return f"Error fetching gas data: {data['error']}"

        gas_data = data.get("result", {})

        result = "⛽ **Ethereum Gas Tracker:**\n\n"
        result += f"**Safe Gas Price:** {gas_data.get('SafeGasPrice', 0)} Gwei\n"
        result += (
            f"**Standard Gas Price:** {gas_data.get('StandardGasPrice', 0)} Gwei\n"
        )
        result += f"**Fast Gas Price:** {gas_data.get('FastGasPrice', 0)} Gwei\n"

        # Estimate transaction costs
        safe_cost = (
            float(gas_data.get("SafeGasPrice", 0)) * 21000 / 10**9
        )  # ETH for simple transfer
        fast_cost = float(gas_data.get("FastGasPrice", 0)) * 21000 / 10**9

        result += f"\n**Estimated TX Costs (simple transfer):**\n"
        result += f"   - Safe: ~{safe_cost:.6f} ETH\n"
        result += f"   - Fast: ~{fast_cost:.6f} ETH\n"

        return result

    def get_top_accounts(self) -> str:
        """Get top Ethereum accounts by balance"""
        data = self._make_request(
            {
                "module": "account",
                "action": "balancemulti",
                "address": ",".join(
                    [
                        "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",  # Binance
                        "0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a",  # Bitfinex
                        "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance 2
                        "0x21a31ee1afc51d94c2efccaa2092ad1028285549",  # Binance 3
                        "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",  # Kraken
                    ]
                ),
                "tag": "latest",
            }
        )

        if "error" in data:
            return f"Error fetching top accounts: {data['error']}"

        accounts = data.get("result", [])

        result = "🏆 **Top Ethereum Accounts (Exchanges):**\n\n"

        exchange_names = ["Binance", "Bitfinex", "Binance 2", "Binance 3", "Kraken"]

        for i, account in enumerate(accounts):
            balance_wei = int(account.get("balance", 0))
            balance_eth = balance_wei / 10**18
            address = account.get("account", "")

            result += f"**{exchange_names[i]}**\n"
            result += f"   - Address: {address[:10]}...{address[-8:]}\n"
            result += f"   - Balance: {balance_eth:,.0f} ETH\n\n"

        return result

    def get_tools(self) -> List[Tool]:
        """Return LangChain tools for this MCP"""
        return [
            Tool(
                name="get_ethereum_stats",
                description="Get Ethereum network statistics including price, supply, and market cap",
                func=lambda _: self.get_ethereum_stats(),
            ),
            Tool(
                name="analyze_ethereum_wallet",
                description="Analyze an Ethereum wallet address for balance, transaction count, and activity. Input: wallet address",
                func=self.analyze_wallet,
            ),
            Tool(
                name="get_wallet_transactions",
                description="Get recent transactions for an Ethereum address. Input: wallet address",
                func=lambda address: self.get_recent_transactions(address),
            ),
            Tool(
                name="get_gas_prices",
                description="Get current Ethereum gas prices and estimated transaction costs",
                func=lambda _: self.get_gas_tracker(),
            ),
            Tool(
                name="get_top_ethereum_accounts",
                description="Get top Ethereum accounts by balance (major exchanges)",
                func=lambda _: self.get_top_accounts(),
            ),
        ]
