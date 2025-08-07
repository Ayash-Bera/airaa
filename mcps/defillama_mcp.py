import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from langchain.tools import Tool


class DeFiLlamaMCP:
    """Enhanced DeFiLlama API integration with advanced analytics features"""

    def __init__(self):
        self.base_url = "https://api.llama.fi"
        self.coins_url = "https://coins.llama.fi"
        self.yields_url = "https://yields.llama.fi"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Web3-Research-Copilot/2.0"})

    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def get_protocols_enhanced(self, limit: int = 20) -> str:
        """Enhanced protocol analysis with trends and metrics"""
        data = self._make_request(f"{self.base_url}/protocols")
        
        if "error" in data:
            return f"Error fetching protocols: {data['error']}"

        # Filter out protocols with None/invalid TVL and sort
        valid_protocols = [p for p in data if isinstance(p.get("tvl"), (int, float)) and p.get("tvl", 0) > 0]
        protocols = sorted(valid_protocols, key=lambda x: x.get("tvl", 0), reverse=True)[:limit]

        result = "🏆 **Enhanced Protocol Rankings:**\n\n"
        
        for i, protocol in enumerate(protocols, 1):
            name = protocol.get("name", "Unknown")
            tvl = protocol.get("tvl", 0)
            change_1d = protocol.get("change_1d", 0)
            change_7d = protocol.get("change_7d", 0)
            change_1m = protocol.get("change_1m", 0)
            category = protocol.get("category", "Unknown")
            chains = protocol.get("chains", [])
            
            # Calculate momentum score
            momentum = (change_1d * 0.5) + (change_7d * 0.3) + (change_1m * 0.2)
            momentum_emoji = "🚀" if momentum > 5 else "📈" if momentum > 0 else "📉" if momentum > -5 else "💥"
            
            result += f"{i}. **{name}** {momentum_emoji}\n"
            result += f"   - TVL: ${tvl:,.0f}\n"
            result += f"   - Changes: 1d: {change_1d:+.1f}% | 7d: {change_7d:+.1f}% | 1m: {change_1m:+.1f}%\n"
            result += f"   - Category: {category} | Chains: {len(chains)}\n"
            if len(chains) <= 3:
                result += f"   - Networks: {', '.join(chains[:3])}\n"
            result += "\n"

        return result

    def get_protocol_deep_dive(self, protocol_name: str) -> str:
        """Deep protocol analysis with historical data and metrics"""
        # Get protocol list
        protocols_data = self._make_request(f"{self.base_url}/protocols")
        if "error" in protocols_data:
            return f"Error: {protocols_data['error']}"

        # Find protocol
        protocol = None
        for p in protocols_data:
            if protocol_name.lower() in p.get("name", "").lower():
                protocol = p
                break

        if not protocol:
            return f"Protocol '{protocol_name}' not found"

        slug = protocol.get("slug")
        
        # Get detailed protocol data
        protocol_detail = self._make_request(f"{self.base_url}/protocol/{slug}")
        
        if "error" in protocol_detail:
            protocol_detail = protocol

        result = f"🔍 **{protocol.get('name')} Deep Analysis:**\n\n"
        
        # Basic metrics
        result += "**📊 Current Metrics:**\n"
        result += f"   - TVL: ${protocol.get('tvl', 0):,.0f}\n"
        result += f"   - Rank: #{protocols_data.index(protocol) + 1}\n"
        result += f"   - Category: {protocol.get('category', 'Unknown')}\n"
        
        # Performance metrics
        result += "\n**📈 Performance:**\n"
        changes = {
            "1 Day": protocol.get('change_1d', 0),
            "7 Days": protocol.get('change_7d', 0),
            "1 Month": protocol.get('change_1m', 0)
        }
        
        for period, change in changes.items():
            emoji = "🟢" if change > 0 else "🔴" if change < -2 else "🟡"
            result += f"   - {period}: {change:+.1f}% {emoji}\n"
        
        # Multi-chain analysis
        chains = protocol.get("chains", [])
        if chains:
            result += f"\n**⛓️ Multi-Chain Presence ({len(chains)} chains):**\n"
            for chain in chains[:5]:
                result += f"   - {chain}\n"
            if len(chains) > 5:
                result += f"   - ... and {len(chains) - 5} more\n"
        
        # Get chain-specific TVL if available
        if 'chainTvls' in protocol_detail:
            result += "\n**🔗 Chain Distribution:**\n"
            chain_tvls = protocol_detail['chainTvls']
            total_tvl = sum(chain_tvls.values())
            for chain, tvl in sorted(chain_tvls.items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (tvl / total_tvl * 100) if total_tvl > 0 else 0
                result += f"   - {chain}: ${tvl:,.0f} ({percentage:.1f}%)\n"

        # Additional info
        if protocol.get("description"):
            result += f"\n**📝 Description:**\n{protocol['description'][:200]}...\n"
            
        if protocol.get("url"):
            result += f"\n**🌐 Website:** {protocol['url']}\n"

        return result

    def get_chain_ecosystem_analysis(self, chain_name: str = None) -> str:
        """Enhanced chain analysis with ecosystem metrics"""
        chains_data = self._make_request(f"{self.base_url}/chains")
        
        if "error" in chains_data:
            return f"Error: {chains_data['error']}"

        if chain_name:
            # Single chain deep dive
            chain = None
            for c in chains_data:
                if chain_name.lower() in c.get("name", "").lower():
                    chain = c
                    break
            
            if not chain:
                return f"Chain '{chain_name}' not found"
                
            result = f"⛓️ **{chain.get('name')} Ecosystem Analysis:**\n\n"
            
            # Core metrics
            result += "**💰 Financial Metrics:**\n"
            result += f"   - Total TVL: ${chain.get('tvl', 0):,.0f}\n"
            result += f"   - 24h Change: {chain.get('change_1d', 0):+.1f}%\n"
            result += f"   - 7d Change: {chain.get('change_7d', 0):+.1f}%\n"
            result += f"   - 1m Change: {chain.get('change_1m', 0):+.1f}%\n"
            
            # Get protocols on this chain
            protocols_data = self._make_request(f"{self.base_url}/protocols")
            if "error" not in protocols_data:
                chain_protocols = [p for p in protocols_data if chain_name.lower() in [c.lower() for c in p.get("chains", [])]]
                
                result += f"\n**🏗️ Ecosystem Health:**\n"
                result += f"   - Active Protocols: {len(chain_protocols)}\n"
                
                if chain_protocols:
                    top_protocol = max(chain_protocols, key=lambda x: x.get("tvl", 0))
                    result += f"   - Largest Protocol: {top_protocol.get('name')} (${top_protocol.get('tvl', 0):,.0f})\n"
                    
                    categories = {}
                    for p in chain_protocols:
                        cat = p.get('category', 'Unknown')
                        categories[cat] = categories.get(cat, 0) + 1
                    
                    result += "   - Top Categories:\n"
                    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]:
                        result += f"     • {cat}: {count} protocols\n"
        else:
            # Multi-chain comparison
            chains = sorted(chains_data, key=lambda x: x.get("tvl", 0), reverse=True)[:15]
            
            result = "⛓️ **Multi-Chain Ecosystem Rankings:**\n\n"
            
            for i, chain in enumerate(chains, 1):
                name = chain.get("name", "Unknown")
                tvl = chain.get("tvl", 0)
                change_1d = chain.get("change_1d", 0)
                change_7d = chain.get("change_7d", 0)
                
                # Calculate ecosystem strength
                strength = "🔥" if tvl > 10000000000 else "💪" if tvl > 1000000000 else "🌱" if tvl > 100000000 else "📈"
                trend = "📈" if change_7d > 5 else "📊" if change_7d > -5 else "📉"
                
                result += f"{i}. **{name}** {strength} {trend}\n"
                result += f"   - TVL: ${tvl:,.0f}\n"
                result += f"   - Momentum: 1d: {change_1d:+.1f}% | 7d: {change_7d:+.1f}%\n\n"

        return result

    def get_yield_opportunities_enhanced(self, min_apy: float = 5.0, limit: int = 15) -> str:
        """Enhanced yield analysis with risk metrics and trends"""
        data = self._make_request(f"{self.yields_url}/pools")
        
        if "error" in data:
            return f"Error: {data['error']}"

        pools = data.get("data", [])
        
        # Filter and enhance with risk scoring
        filtered_pools = []
        for pool in pools:
            apy = pool.get("apy") or 0
            tvl = pool.get("tvlUsd") or 0
            
            # Skip pools with None/invalid values
            if not isinstance(apy, (int, float)) or not isinstance(tvl, (int, float)):
                continue
                
            if apy >= min_apy and tvl > 100000:  # Minimum TVL for liquidity
                # Calculate risk score
                risk_score = 0
                
                # TVL-based risk (higher TVL = lower risk)
                if tvl > 10000000: risk_score += 1
                elif tvl > 1000000: risk_score += 0.5
                
                # APY-based risk (extremely high APY = higher risk)
                if apy < 20: risk_score += 1
                elif apy < 50: risk_score += 0.5
                
                # Stablecoin bonus (lower risk)
                symbol = pool.get("symbol", "").upper()
                if any(stable in symbol for stable in ["USDC", "USDT", "DAI", "FRAX"]):
                    risk_score += 1
                
                pool["risk_score"] = risk_score
                filtered_pools.append(pool)

        # Sort by risk-adjusted return (APY * risk_score)
        sorted_pools = sorted(filtered_pools, key=lambda x: (x.get("apy") or 0) * max(x.get("risk_score", 0.1), 0.1), reverse=True)[:limit]

        result = f"💰 **Enhanced Yield Opportunities (>{min_apy}% APY):**\n\n"

        for i, pool in enumerate(sorted_pools, 1):
            protocol = pool.get("project", "Unknown")
            apy = pool.get("apy", 0)
            tvl = pool.get("tvlUsd", 0)
            symbol = pool.get("symbol", "Unknown")
            chain = pool.get("chain", "Unknown")
            risk_score = pool.get("risk_score", 0)
            
            # Risk assessment
            if risk_score >= 2:
                risk_emoji = "🟢"
                risk_text = "Low Risk"
            elif risk_score >= 1:
                risk_emoji = "🟡"
                risk_text = "Med Risk"
            else:
                risk_emoji = "🔴"
                risk_text = "High Risk"

            result += f"{i}. **{protocol}** ({chain}) {risk_emoji}\n"
            result += f"   - Pool: {symbol}\n"
            result += f"   - APY: {apy:.1f}% | TVL: ${tvl:,.0f}\n"
            result += f"   - Risk Level: {risk_text}\n"
            
            # Add yield composition if available
            if pool.get("apyBase") and pool.get("apyReward"):
                base_apy = pool.get("apyBase", 0)
                reward_apy = pool.get("apyReward", 0)
                result += f"   - Base APY: {base_apy:.1f}% | Reward APY: {reward_apy:.1f}%\n"
            
            result += "\n"

        return result

    def get_stablecoin_analytics(self) -> str:
        """Comprehensive stablecoin market analysis"""
        # Get stablecoin data
        stablecoin_data = self._make_request(f"{self.base_url}/stablecoins")
        
        if "error" in stablecoin_data:
            return f"Error: {stablecoin_data['error']}"

        stablecoins = stablecoin_data.get("peggedAssets", [])[:10]
        
        result = "💵 **Stablecoin Market Analysis:**\n\n"
        
        # Market overview
        total_mcap = sum(s.get("circulating", {}).get("peggedUSD", 0) for s in stablecoins)
        result += f"**📊 Market Overview:**\n"
        result += f"   - Total Market Cap: ${total_mcap:,.0f}\n"
        result += f"   - Active Stablecoins: {len(stablecoins)}\n\n"
        
        result += "**🏆 Top Stablecoins:**\n"
        
        for i, stable in enumerate(stablecoins, 1):
            name = stable.get("name", "Unknown")
            symbol = stable.get("symbol", "Unknown")
            mcap = stable.get("circulating", {}).get("peggedUSD", 0)
            change_1d = stable.get("change_1d", 0)
            chains = stable.get("chainCirculating", {})
            
            market_share = (mcap / total_mcap * 100) if total_mcap > 0 else 0
            
            result += f"{i}. **{name} ({symbol})**\n"
            result += f"   - Market Cap: ${mcap:,.0f} ({market_share:.1f}%)\n"
            result += f"   - 24h Change: {change_1d:+.2f}%\n"
            result += f"   - Chains: {len(chains)}\n"
            
            # Top chains for this stablecoin
            if chains:
                top_chains = sorted(chains.items(), key=lambda x: x[1], reverse=True)[:3]
                result += "   - Top Chains: "
                result += ", ".join([f"{chain}: ${amount:,.0f}" for chain, amount in top_chains])
                result += "\n"
            
            result += "\n"

        return result

    def get_cross_chain_bridge_analysis(self) -> str:
        """Cross-chain bridge volume and activity analysis"""
        bridge_data = self._make_request(f"{self.base_url}/bridges")
        
        if "error" in bridge_data:
            return f"Error: {bridge_data['error']}"

        bridges = sorted(bridge_data.get("bridges", []), key=lambda x: x.get("volumePrevDay", 0), reverse=True)[:10]
        
        result = "🌉 **Cross-Chain Bridge Analysis:**\n\n"
        
        total_volume = sum(b.get("volumePrevDay", 0) for b in bridges)
        result += f"**📊 Market Overview:**\n"
        result += f"   - Total 24h Volume: ${total_volume:,.0f}\n"
        result += f"   - Active Bridges: {len(bridges)}\n\n"
        
        result += "**🏆 Top Bridges by Volume:**\n"
        
        for i, bridge in enumerate(bridges, 1):
            name = bridge.get("displayName", "Unknown")
            volume_24h = bridge.get("volumePrevDay", 0)
            volume_7d = bridge.get("volumePrev7Days", 0)
            chains = bridge.get("chains", [])
            
            market_share = (volume_24h / total_volume * 100) if total_volume > 0 else 0
            avg_daily_7d = volume_7d / 7 if volume_7d > 0 else 0
            
            trend = "📈" if volume_24h > avg_daily_7d else "📉" if volume_24h < avg_daily_7d * 0.8 else "📊"
            
            result += f"{i}. **{name}** {trend}\n"
            result += f"   - 24h Volume: ${volume_24h:,.0f} ({market_share:.1f}%)\n"
            result += f"   - 7d Average: ${avg_daily_7d:,.0f}\n"
            result += f"   - Supported Chains: {len(chains)}\n"
            
            if len(chains) <= 4:
                result += f"   - Networks: {', '.join(chains)}\n"
            
            result += "\n"

        return result

    def get_trending_protocols(self) -> str:
        """Identify trending protocols based on growth metrics"""
        data = self._make_request(f"{self.base_url}/protocols")
        
        if "error" in data:
            return f"Error: {data['error']}"

        # Filter for protocols with significant growth
        trending = []
        for protocol in data:
            change_7d = protocol.get("change_7d", 0)
            tvl = protocol.get("tvl", 0)
            
            # Criteria: >10% growth in 7d and >$1M TVL
            if change_7d > 10 and tvl > 1000000:
                momentum_score = change_7d * (tvl / 1000000) ** 0.5  # TVL-weighted momentum
                protocol["momentum_score"] = momentum_score
                trending.append(protocol)
        
        trending = sorted(trending, key=lambda x: x.get("momentum_score", 0), reverse=True)[:10]
        
        result = "🔥 **Trending Protocols (High Growth):**\n\n"
        
        if not trending:
            result += "No significant trending protocols found in current market conditions.\n"
            return result
        
        for i, protocol in enumerate(trending, 1):
            name = protocol.get("name", "Unknown")
            tvl = protocol.get("tvl", 0)
            change_1d = protocol.get("change_1d", 0)
            change_7d = protocol.get("change_7d", 0)
            category = protocol.get("category", "Unknown")
            momentum = protocol.get("momentum_score", 0)
            
            result += f"{i}. **{name}** 🚀\n"
            result += f"   - TVL: ${tvl:,.0f}\n"
            result += f"   - Growth: 1d: {change_1d:+.1f}% | 7d: {change_7d:+.1f}%\n"
            result += f"   - Category: {category}\n"
            result += f"   - Momentum Score: {momentum:.1f}\n\n"

        return result

    def get_tools(self) -> List[Tool]:
        """Return enhanced LangChain tools"""
        return [
            Tool(
                name="get_defi_protocols",
                description="Get enhanced protocol rankings with trends, momentum scores, and multi-chain analysis",
                func=lambda query: self.get_protocols_enhanced(
                    limit=int(query) if query.isdigit() else 20
                ),
            ),
            Tool(
                name="analyze_defi_protocol",
                description="Comprehensive protocol analysis with historical data, chain distribution, and ecosystem metrics. Input: protocol name",
                func=self.get_protocol_deep_dive,
            ),
            Tool(
                name="get_blockchain_tvl",
                description="Enhanced blockchain ecosystem analysis with protocol distribution and health metrics. Input: chain name or 'all' for comparison",
                func=lambda query: self.get_chain_ecosystem_analysis(query if query and query != 'all' else None),
            ),
            Tool(
                name="find_yield_opportunities",
                description="Advanced yield farming analysis with risk scoring and composition breakdown. Input: minimum APY (default 5.0)",
                func=lambda query: self.get_yield_opportunities_enhanced(
                    min_apy=float(query) if query.replace(".", "").isdigit() else 5.0
                ),
            ),
            Tool(
                name="stablecoin_market_analysis",
                description="Comprehensive stablecoin market analysis with cross-chain distribution and market share data",
                func=lambda _: self.get_stablecoin_analytics(),
            ),
            Tool(
                name="cross_chain_bridge_analytics",
                description="Cross-chain bridge volume analysis and activity trends across different networks",
                func=lambda _: self.get_cross_chain_bridge_analysis(),
            ),
            Tool(
                name="trending_protocols_detector",
                description="Identify trending protocols with high growth momentum and significant TVL changes",
                func=lambda _: self.get_trending_protocols(),
            ),
        ]