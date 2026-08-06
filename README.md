# Crypto Market Screener

CoreClaw worker for live cryptocurrency market data from the [CoinGecko](https://www.coingecko.com/) public API. No API key required.

## Features

- **Flexible coin input** — supports CoinGecko IDs (`bitcoin`), symbols (`btc`), or names (`Bitcoin`)
- **Top N mode** — pull top coins by market cap with one click
- **Multi-currency** — prices in USD, EUR, GBP, BTC, or ETH
- **Rich output** — 22 columns: price, market cap, rank, 24h volume, 1h/24h/7d/30d changes, high/low, circulating/total/max supply, ATH/ATL, FDV

## Inputs

| Field | Type | Description |
|-------|------|-------------|
| `coins` | stringList | Coin IDs, symbols, or names |
| `include_top` | number | Auto-include top N coins by market cap |
| `vs_currency` | select | Quote currency (usd/eur/gbp/btc/eth) |
| `max_results` | number | Max coins to return (max 250) |

## Output (22 columns)

`id`, `symbol`, `name`, `current_price`, `market_cap`, `market_cap_rank`, `total_volume`, `price_change_1h_pct`, `price_change_24h_pct`, `price_change_7d_pct`, `price_change_30d_pct`, `high_24h`, `low_24h`, `circulating_supply`, `total_supply`, `max_supply`, `ath`, `ath_date`, `atl`, `atl_date`, `fully_diluted_valuation`, `last_updated`

## Deploy to CoreClaw

1. Go to [console.coreclaw.com](https://console.coreclaw.com) → My Workers → Create Worker
2. Choose **GitHub Import** → paste `https://github.com/blueeyez425-art/coreclaw-crypto-market-screener.git`
3. Category: **Finance**, Tags: `crypto`, `market-data`, `coingecko`
4. Publish
