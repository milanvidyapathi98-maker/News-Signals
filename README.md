# 📰 NewsSignal

**AI-powered news sentiment signals for stocks.**

NewsSignal reads the latest news about a company, scores every headline with a finance-trained AI model (FinBERT), and turns the result into a clear **BUY / SELL / HOLD** signal. If you want, it also checks the signal against the price trend first. Everything is shown in an interactive dashboard built with Streamlit.

> 🔗 **Live demo:**(https://news-signals-zww8xqruslnhadjnvl8qgn.streamlit.app/)

![NewsSignal dashboard](docs/screenshot.png)
<!-- Add a screenshot of the running app as docs/screenshot.png -->

---

## ✨ Features

- **206 companies in a dropdown**: the world's top 200 by market cap plus major German DAX stocks. You can also enter any other Yahoo Finance ticker by hand.
- **Company logos** next to each company name, with the company's initials shown when no logo is available.
- **AI sentiment analysis**: every headline is classified as positive, neutral or negative by [FinBERT](https://huggingface.co/ProsusAI/finbert).
- **Recency weighting**: newer news counts more than older news.
- **Trend confirmation**: you can require the price to agree with the news (price vs. 50-day moving average) before a BUY or SELL is given.
- **Dashboard**
  - Live header with a scrolling headline bar
  - Summary row: BUY / SELL / HOLD counts and overall market mood
  - **Overview** tab: a card for each company (with logo) and a sentiment ranking chart
  - **Company detail** tab: 6-month price chart with the 50-day average, plus the latest headlines
  - **News feed** tab: all headlines in one list, filterable by sentiment and company
  - **How it works** tab: the method explained in plain language
- **Adjustable strategy**: set the BUY/SELL levels yourself in the sidebar.

---

## 🧠 How it works

```
 News sources        AI model            Scoring              Decision            Dashboard
┌─────────────┐   ┌─────────────┐   ┌────────────────┐   ┌────────────────┐   ┌─────────────┐
│ Yahoo +     │──▶│  FinBERT    │──▶│ Recency-       │──▶│ BUY / SELL /   │──▶│  Streamlit  │
│ Google News │   │  positive / │   │ weighted score │   │ HOLD (+ trend  │   │  dashboard  │
│ (+ Finnhub) │   │  neutral /  │   │ from −1 to +1  │   │ check vs MA50) │   │             │
└─────────────┘   │  negative   │   └────────────────┘   └────────────────┘   └─────────────┘
                  └─────────────┘
```

1. **Collect**: headlines from the last 7 days are fetched from Yahoo Finance and Google News, and from Finnhub if an API key is set. Duplicates are removed. If a source fails, the app shows which one and why.
2. **Analyse**: FinBERT scores each headline: positive = +1, negative = −1, neutral = 0, multiplied by the model's confidence.
3. **Combine**: scores are averaged with a 48-hour half-life, so a headline from two days ago counts half as much as one from right now.
4. **Decide**:

   | Score | Signal |
   |---|---|
   | above **+0.25** | ▲ **BUY** |
   | below **−0.25** | ▼ **SELL** |
   | in between, or fewer than 3 headlines | ● **HOLD** |

   With trend confirmation on, a BUY also needs the price **above** its 50-day average, and a SELL needs it **below**. Otherwise the signal stays HOLD.

---

## 🛠️ Tech stack

| Area | Tools |
|---|---|
| Language | Python 3.12 |
| Dashboard | Streamlit, Plotly |
| AI / NLP | Hugging Face Transformers, FinBERT, PyTorch |
| Market data & news | yfinance, Google News RSS, Finnhub API (optional) |
| Company logos | Financial Modeling Prep logo service |
| Data handling | pandas |

---

## 🚀 Getting started

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/news-signal.git
cd news-signal
```

### 2. Create a virtual environment (Python 3.12 recommended)
```bash
# Windows
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Install the packages
```bash
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```
The second line installs the CPU-only version of PyTorch. It's much smaller, and you don't need a graphics card.

### 4. Run
```bash
python -m streamlit run app.py
```
The dashboard opens at `http://localhost:8501`.
The first start downloads the FinBERT model (~400 MB), so it takes a few minutes once.

To test the signals in the terminal without the dashboard:
```bash
python signals.py
```

### Optional: more news with Finnhub
Get a free API key at [finnhub.io](https://finnhub.io) and set it as an environment variable:
```bash
# Windows (PowerShell)
$env:FINNHUB_API_KEY = "your_key"

# macOS / Linux
export FINNHUB_API_KEY="your_key"
```

---

## ⚙️ Configuration

You can change all settings in **`config.py`**:

| Setting | Default | Meaning |
|---|---|---|
| `COMPANIES` | 206 companies | Companies shown in the dropdown (`"Name": "Ticker"`) |
| `DEFAULT_COMPANIES` | Apple, Microsoft, Tesla, SAP | Selected when the app opens |
| `LOOKBACK_DAYS` | `7` | How many days of news to use |
| `MAX_HEADLINES` | `50` | Maximum headlines per company |
| `HALF_LIFE_HOURS` | `48` | After how many hours a headline counts half as much |
| `BUY_THRESHOLD` / `SELL_THRESHOLD` | `+0.25` / `−0.25` | Signal levels (also adjustable in the app) |
| `MIN_HEADLINES` | `3` | Minimum headlines needed for a BUY or SELL |
| `LOGO_URL` | Financial Modeling Prep | Where company logos are loaded from (`{ticker}` is replaced by the ticker) |

To add a company, add a line to `COMPANIES`, for example:
```python
"Rheinmetall": "RHM.DE",
```

---

## 📁 Project structure

```
news-signal/
├── app.py              # Streamlit dashboard (layout, charts, styling)
├── signals.py          # Combines scores, price trend check, BUY/SELL/HOLD decision
├── sentiment.py        # FinBERT sentiment scoring
├── news_fetcher.py     # Collects and cleans news from Yahoo Finance / Finnhub
├── config.py           # Companies and settings
├── requirements.txt    # Python packages
├── .streamlit/
│   └── config.toml     # Dark theme
└── README.md
```

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo → main file `app.py`.
3. *(Optional)* Add your Finnhub key under **Settings → Secrets**:
   ```toml
   FINNHUB_API_KEY = "your_key"
   ```
4. *(Recommended)* Add this as the first line of `requirements.txt`, so the cloud installs the small CPU version of PyTorch:
   ```
   --extra-index-url https://download.pytorch.org/whl/cpu
   ```

---

## ⚠️ Limitations

- **Speed:** markets often react to news within minutes, and free news feeds can be slower than that.
- **Headlines only:** the model reads headlines and short summaries, not full articles.
- **Coverage:** some non-US companies (for example Chinese A-shares) have little English news on Yahoo Finance, so they often show HOLD.
- **Not backtested yet:** the signals have not been tested on historical data.

## 🗺️ Roadmap

- [ ] Backtesting: check how past signals would have performed
- [ ] Save daily sentiment history to a database
- [ ] More news sources (RSS feeds, German-language news)
- [ ] Email or Telegram alerts when a signal changes

---

## 📄 Disclaimer

NewsSignal is an **educational and portfolio project**. It does **not** provide financial advice, and its signals are not recommendations to buy or sell any security. Always do your own research before you invest.

---

## 👤 Author

**Milan Vidyapathige**
M.A. International Management & Information Systems · B.Sc. Finance
📍 Frankfurt am Main, Germany

<!-- Add your LinkedIn / GitHub links here -->
