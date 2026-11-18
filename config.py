"""Settings for NewsSignal. Change these to tune the program."""

import os

# Companies in the dropdown: "Name": "Yahoo Finance ticker"
COMPANIES = {
    # Top 100 by market cap (companiesmarketcap.com, 17 Nov 2026), in rank order
    "Apple":                             "AAPL",
    "Microsoft":                         "MSFT",
    "NVIDIA":                            "NVDA",
    "Alphabet (Google)":                 "GOOG",
    "Amazon":                            "AMZN",
    "TSMC":                              "TSM",
    "SpaceX":                            "SPCX",
    "Saudi Aramco":                      "2222.SR",
    "Meta Platforms (Facebook)":         "META",
    "Broadcom":                          "AVGO",
    "Tesla":                             "TSLA",
    "Eli Lilly":                         "LLY",
    "Berkshire Hathaway":                "BRK-B",
    "Walmart":                           "WMT",
    "Samsung":                           "005930.KS",
    "JPMorgan Chase":                    "JPM",
    "AMD":                               "AMD",
    "Micron Technology":                 "MU",
    "Visa":                              "V",
    "Exxon Mobil":                       "XOM",
    "Johnson & Johnson":                 "JNJ",
    "SK Hynix":                          "000660.KS",
    "Mastercard":                        "MA",
    "ASML":                              "ASML",
    "AbbVie":                            "ABBV",
    "Costco":                            "COST",
    "China Construction Bank":           "601939.SS",
    "Tencent":                           "TCEHY",
    "Coca-Cola":                         "KO",
    "Chevron":                           "CVX",
    "Procter & Gamble":                  "PG",
    "Roche":                             "RO.SW",
    "Agricultural Bank of China":        "601288.SS",
    "CXMT":                              "688825.SS",
    "Palantir":                          "PLTR",
    "Cisco":                             "CSCO",
    "Oracle":                            "ORCL",
    "UnitedHealth":                      "UNH",
    "ICBC":                              "1398.HK",
    "Merck":                             "MRK",
    "Bank of China":                     "601988.SS",
    "Home Depot":                        "HD",
    "Bank of America":                   "BAC",
    "General Electric":                  "GE",
    "Philip Morris International":       "PM",
    "Novartis":                          "NVS",
    "HSBC":                              "HSBC",
    "Intel":                             "INTC",
    "Morgan Stanley":                    "MS",
    "AstraZeneca":                       "AZN",
    "Applied Materials":                 "AMAT",
    "Royal Bank of Canada":              "RY",
    "Shell":                             "SHEL",
    "Nestlé":                            "NESN.SW",
    "Kweichow Moutai":                   "600519.SS",
    "SAP":                               "SAP.DE",
    "L'Oréal":                           "OR.PA",
    "Texas Instruments":                 "TXN",
    "Lam Research":                      "LRCX",
    "RTX":                               "RTX",
    "Caterpillar":                       "CAT",
    "Palo Alto Networks":                "PANW",
    "Goldman Sachs":                     "GS",
    "Thermo Fisher Scientific":          "TMO",
    "Wells Fargo":                       "WFC",
    "Toyota":                            "TM",
    "Amgen":                             "AMGN",
    "Netflix":                           "NFLX",
    "PetroChina":                        "0857.HK",
    "Linde":                             "LIN",
    "Mitsubishi UFJ Financial":          "MUFG",
    "Arista Networks":                   "ANET",
    "Siemens":                           "SIE.DE",
    "IBM":                               "IBM",
    "CrowdStrike":                       "CRWD",
    "Alibaba":                           "BABA",
    "China Mobile":                      "0941.HK",
    "LVMH":                              "MC.PA",
    "American Express":                  "AXP",
    "Inditex":                           "ITX.MC",
    "Gilead Sciences":                   "GILD",
    "Walt Disney":                       "DIS",
    "Dell":                              "DELL",
    "GE Vernova":                        "GEV",
    "Citigroup":                         "C",
    "Commonwealth Bank":                 "CBA.AX",
    "Allianz":                           "ALV.DE",
    "PepsiCo":                           "PEP",
    "Toronto-Dominion Bank":             "TD",
    "TotalEnergies":                     "TTE",
    "McDonald's":                        "MCD",
    "Reliance Industries":               "RELIANCE.NS",
    "Verizon":                           "VZ",
    "BHP Group":                         "BHP",
    "Shopify":                           "SHOP",
    "MediaTek":                          "2454.TW",
    "KLA":                               "KLAC",
    "International Holding Company":     "IHC.AE",
    "Arm Holdings":                      "ARM",
    "Amphenol":                          "APH",
    # More German companies (DAX)
    "Deutsche Bank":                     "DBK.DE",
    "Deutsche Telekom":                  "DTE.DE",
    "Mercedes-Benz Group":               "MBG.DE",
    "BMW":                               "BMW.DE",
    "Volkswagen":                        "VOW3.DE",
    "BASF":                              "BAS.DE",
    "Bayer":                             "BAYN.DE",
    "Infineon":                          "IFX.DE",
    "adidas":                            "ADS.DE",
}

# Companies selected when the app opens
DEFAULT_COMPANIES = ["Apple", "Microsoft", "Tesla", "SAP"]
DEFAULT_TICKERS = [COMPANIES[c] for c in DEFAULT_COMPANIES]

# Only use news from the last N days
LOOKBACK_DAYS = 3

# Max headlines per ticker
MAX_HEADLINES = 30

# Recency weighting: a headline this many hours old counts half as much
HALF_LIFE_HOURS = 24

# Decision thresholds on the final score (range -1 .. +1)
BUY_THRESHOLD = 0.25
SELL_THRESHOLD = -0.25

# Need at least this many headlines before giving BUY/SELL
MIN_HEADLINES = 3

# Optional: free key from https://finnhub.io for more news (set as environment variable)
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Hugging Face model used for sentiment
SENTIMENT_MODEL = "ProsusAI/finbert"