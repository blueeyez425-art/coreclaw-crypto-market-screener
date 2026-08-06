#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoreClaw Worker: Crypto Market Screener
Fetches live crypto market data from CoinGecko public API.
No API key required. Rate limit: ~30 calls/min on free tier.
"""
import json
import urllib.request
import urllib.error
import time
from sdk import CoreSDK


COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_LIST_URL = f"{COINGECKO_BASE}/coins/list"
COINGECKO_MARKETS_URL = f"{COINGECKO_BASE}/coins/markets"

# Known top coins by market cap (fallback if CoinGecko list fails)
TOP_COINS = [
    "bitcoin", "ethereum", "tether", "binancecoin", "solana",
    "ripple", "usd-coin", "staked-ether", "dogecoin", "cardano",
    "tron", "chainlink", "avalanche-2", "sui", "stellar",
    "litecoin", "polkadot", "uniswap", "near", "pepe",
    "shiba-inu", "crypto-com-chain", "monero", "aptos", "arbitrum",
    "ethereum-classic", "optimism", "render-token", "bittensor", "vechain",
]

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "CoreClaw-Crypto-Market-Data/1.0"
}


def _fetch_json(url: str, timeout: int = 30) -> dict | list:
    """Fetch a JSON endpoint with retries."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            CoreSDK.Log.warn(f"HTTP {e.code} on attempt {attempt+1}: {url}")
            if e.code == 429:
                time.sleep(60)
            elif e.code >= 500:
                time.sleep(10)
            else:
                raise
        except Exception as e:
            CoreSDK.Log.warn(f"Network error on attempt {attempt+1}: {e}")
            time.sleep(5)
    raise RuntimeError(f"Failed to fetch after 3 retries: {url}")


def _resolve_coin_ids(coin_inputs: list, include_top: int) -> list:
    """
    Resolve user-provided coin names/symbols to CoinGecko IDs.
    Accepts: full IDs ("bitcoin"), symbols ("btc"), or names ("Bitcoin").
    """
    if not coin_inputs and include_top <= 0:
        raise ValueError("Must provide coin names or set include_top > 0")

    # Fetch the full coin list
    CoreSDK.Log.info("Fetching CoinGecko coin list...")
    coin_list = _fetch_json(COINGECKO_LIST_URL)

    # Build lookup: id -> coin, symbol_lower -> coin, name_lower -> coin
    id_map = {}
    symbol_map = {}
    name_map = {}
    for coin in coin_list:
        cid = coin["id"]
        symbol = coin.get("symbol", "").lower()
        name = coin.get("name", "").lower()
        id_map[cid] = coin
        if symbol:
            symbol_map.setdefault(symbol, cid)
        if name:
            name_map.setdefault(name, cid)

    resolved = []

    # Resolve user inputs
    for inp in coin_inputs:
        cs = inp.strip().lower()
        if cs in id_map:
            resolved.append(cs)
        elif cs in symbol_map:
            resolved.append(symbol_map[cs])
        elif cs in name_map:
            resolved.append(name_map[cs])
        else:
            CoreSDK.Log.warn(f"Could not resolve coin: {inp}")

    # If include_top > 0, add top N coins not already in resolved
    if include_top > 0:
        top_size = include_top  # approximate, will be trimmed by API
        # Use resolved order for explicit coins, append top N
        resolved = list(dict.fromkeys(resolved))  # dedupe, preserve order

    if not resolved and include_top > 0:
        resolved = TOP_COINS[:include_top]

    CoreSDK.Log.info(f"Resolved {len(resolved)} coin(s)")
    return resolved


def main():
    try:
        # --- Read inputs ---
        params = CoreSDK.Parameter.get_input_json_dict()
        CoreSDK.Log.debug(f"Input params: {params}")

        coins = params.get("coins", [])
        if isinstance(coins, list) and coins and isinstance(coins[0], dict):
            coins = [c.get("string", "") for c in coins]
        vs_currency = params.get("vs_currency", "usd")
        include_top = int(params.get("include_top", 0))
        max_results = int(
            params.get("max_results", 100) if params.get("max_results") is not None
            else 100
        )

        # --- Resolve coins ---
        coin_ids = _resolve_coin_ids(coins, include_top)
        if not coin_ids:
            raise ValueError("No coins resolved. Provide valid coin names/symbols.")

        # --- Fetch market data ---
        coin_ids_for_api = coin_ids[:max_results]
        ids_param = ",".join(coin_ids_for_api)
        url = (
            f"{COINGECKO_MARKETS_URL}"
            f"?vs_currency={vs_currency}"
            f"&ids={ids_param}"
            f"&order=market_cap_desc"
            f"&per_page=250"
            f"&page=1"
            f"&sparkline=false"
            f"&price_change_percentage=1h,24h,7d,30d"
        )

        CoreSDK.Log.info(f"Fetching market data for {len(coin_ids_for_api)} coins...")
        market_data = _fetch_json(url)
        CoreSDK.Log.info(f"Got {len(market_data)} coins from CoinGecko")

        # --- Set output headers ---
        headers = [
            {"label": "ID", "key": "id", "format": "text"},
            {"label": "Symbol", "key": "symbol", "format": "text"},
            {"label": "Name", "key": "name", "format": "text"},
            {"label": "Price", "key": "current_price", "format": "number"},
            {"label": "Market Cap", "key": "market_cap", "format": "number"},
            {"label": "Rank", "key": "market_cap_rank", "format": "number"},
            {"label": "Volume 24h", "key": "total_volume", "format": "number"},
            {"label": "Price Δ 1h%", "key": "price_change_1h_pct", "format": "number"},
            {"label": "Price Δ 24h%", "key": "price_change_24h_pct", "format": "number"},
            {"label": "Price Δ 7d%", "key": "price_change_7d_pct", "format": "number"},
            {"label": "Price Δ 30d%", "key": "price_change_30d_pct", "format": "number"},
            {"label": "24h High", "key": "high_24h", "format": "number"},
            {"label": "24h Low", "key": "low_24h", "format": "number"},
            {"label": "Circulating Supply", "key": "circulating_supply", "format": "number"},
            {"label": "Total Supply", "key": "total_supply", "format": "number"},
            {"label": "Max Supply", "key": "max_supply", "format": "number"},
            {"label": "ATH", "key": "ath", "format": "number"},
            {"label": "ATH Date", "key": "ath_date", "format": "text"},
            {"label": "ATL", "key": "atl", "format": "number"},
            {"label": "ATL Date", "key": "atl_date", "format": "text"},
            {"label": "FDV", "key": "fully_diluted_valuation", "format": "number"},
            {"label": "Last Updated", "key": "last_updated", "format": "text"},
        ]
        CoreSDK.Result.set_table_header(headers)

        # --- Push results ---
        pushed = 0
        for coin in market_data:
            row = {
                "id": coin.get("id", ""),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name", ""),
                "current_price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "total_volume": coin.get("total_volume"),
                "high_24h": coin.get("high_24h"),
                "low_24h": coin.get("low_24h"),
                "circulating_supply": coin.get("circulating_supply"),
                "total_supply": coin.get("total_supply"),
                "max_supply": coin.get("max_supply"),
                "ath": coin.get("ath"),
                "ath_date": coin.get("ath_date", ""),
                "atl": coin.get("atl"),
                "atl_date": coin.get("atl_date", ""),
                "fully_diluted_valuation": coin.get("fully_diluted_valuation"),
                "last_updated": coin.get("last_updated", ""),
                "price_change_1h_pct": coin.get("price_change_percentage_1h_in_currency"),
                "price_change_24h_pct": coin.get("price_change_percentage_24h_in_currency"),
                "price_change_7d_pct": coin.get("price_change_percentage_7d_in_currency"),
                "price_change_30d_pct": coin.get("price_change_percentage_30d_in_currency"),
            }
            CoreSDK.Result.upsert_data(row, "id")
            pushed += 1

        CoreSDK.Log.info(f"Push complete: {pushed} rows")

    except Exception as e:
        CoreSDK.Log.error(f"Script execution error: {e}")
        error_headers = [
            {"label": "Error", "key": "error", "format": "text"},
            {"label": "Status", "key": "status", "format": "text"},
        ]
        CoreSDK.Result.set_table_header(error_headers)
        CoreSDK.Result.push_data({
            "error": str(e),
            "status": "failed",
        })
        raise


if __name__ == "__main__":
    main()
