from flask import Flask, render_template_string, request, jsonify
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64
import random
from datetime import datetime

app = Flask(__name__)

# We'll store the portfolio performance history (time, value)
portfolio_history = []

# ---------- Helper Functions ----------

def get_stock_price(symbol):
    """
    Returns the current price of the stock.
    If symbol == 'RANDOM', returns a random price each time.
    Otherwise, fetch from Yahoo Finance.
    """
    symbol = symbol.upper()
    if symbol == "RANDOM":
        return round(100 * (1 + random.uniform(-0.1, 0.1)), 2)
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        if hist.empty:
            return 0
        return round(hist['Close'].iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return 0

def get_stock_history(symbol):
    """
    For real symbols, fetch 1-year data from Yahoo Finance.
    For 'RANDOM', no chart is returned (so we return empty).
    """
    if symbol.upper() == "RANDOM":
        return [], []
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")['Close']
        if hist.empty:
            return [], []
        return hist.index, hist.values
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return [], []

# ---------- Navigation HTML Snippet (shared by all pages) ----------
nav_html = '''
<nav style="background: #002400; padding: 10px; text-align: center;">
  <a href="/" style="color: #66ff66; margin: 0 15px; text-decoration: none; font-size: 1.2rem; transition: color 0.3s ease;">Home</a>
  <a href="/simulator" style="color: #66ff66; margin: 0 15px; text-decoration: none; font-size: 1.2rem; transition: color 0.3s ease;">Simulator</a>
  <a href="/widget" style="color: #66ff66; margin: 0 15px; text-decoration: none; font-size: 1.2rem; transition: color 0.3s ease;">Widget</a>
</nav>
'''

# New Chat API (Elfsight)
chat_api = '''
<script src="https://static.elfsight.com/platform/platform.js" async></script>
<div class="elfsight-app-ba02bf77-7e56-4eda-9140-e54ab07839b4" data-elfsight-app-lazy></div>
'''

# ---------- Home Page (Quant Trading Info) - Dark Green Theme ----------
home_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Quant Trading - Home</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Montserrat', sans-serif;
      background: linear-gradient(135deg, #0b0b0b, #1a1a1a);
      margin: 0;
      padding: 0;
      overflow-x: hidden;
      color: #e0e0e0;
    }}
    /* Navigation */
    nav {{
      background: #002400;
      padding: 10px;
      text-align: center;
    }}
    nav a {{
      color: #66ff66;
      margin: 0 15px;
      text-decoration: none;
      font-size: 1.2rem;
      transition: color 0.3s ease;
    }}
    nav a:hover {{
      color: #b8ffb8;
    }}
    .container {{
      max-width: 800px;
      margin: 40px auto;
      background: rgba(15, 30, 15, 0.95);
      border-radius: 10px;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.8);
      padding: 30px;
      margin-bottom: 40px;
    }}
    h1 {{
      text-align: center;
      color: #66ff66;
      margin-bottom: 20px;
      font-size: 3rem;
    }}
    h2 {{
      text-align: center;
      color: #66ff66;
      margin-bottom: 20px;
    }}
    p {{
      line-height: 1.6;
      margin-bottom: 5px;
      color: #cccccc;
    }}
    /* Animated Fan */
    .fan {{
      width: 100px;
      height: 100px;
      margin: 20px auto;
      background: url('https://upload.wikimedia.org/wikipedia/commons/3/3b/Pinwheel_icon.png') no-repeat center center;
      background-size: contain;
      animation: spin 4s linear infinite;
    }}
    @keyframes spin {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    /* FAQ Section */
    .faq {{
      margin-top: 30px;
    }}
    .faq-item {{
      border-bottom: 1px solid #333333;
      padding: 10px 0;
      cursor: pointer;
    }}
    .faq-item h3 {{
      margin: 0;
      font-size: 1.2rem;
      color: #66ff66;
    }}
    .faq-answer {{
      display: none;
      margin-top: 10px;
      color: #bbbbbb;
    }}
    .faq-item.active .faq-answer {{
      display: block;
    }}
    /* Scroll Fade-In Animation */
    .fade-in {{
      opacity: 0;
      transform: translateY(20px);
      animation: fadeIn 1s forwards;
    }}
    @keyframes fadeIn {{
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}
    /* Animated Button Styles */
    .button-group {{
      text-align: center;
      margin-top: 30px;
    }}
    .btn {{
      padding: 12px 25px;
      font-size: 1rem;
      background-color: #002400;
      color: #66ff66;
      border: 2px solid #66ff66;
      border-radius: 6px;
      cursor: pointer;
      margin: 0 10px;
      transition: background-color 0.3s, transform 0.3s;
      outline: none;
    }}
    .btn:hover {{
      background-color: #66ff66;
      color: #002400;
      transform: translateY(-3px);
    }}
    .btn:active {{
      transform: translateY(0);
    }}
  </style>
</head>
<body>
  {nav_html}
  <div class="container fade-in" style="animation-delay: 0.2s;">
    <h1>Quant Trading</h1>
    <p>Explore our interactive features, dive into our real-time widget, and start your journey toward becoming a confident trader. Welcome to our Quant Trading platform where data-driven strategies meet cutting-edge financial modeling. Our educational simulator is designed to help you learn to trade stocks without risking real money. Master risk management, market analysis, and build robust trading strategies—all in a safe, simulated environment.</p>
    <div class="fan"></div>
    <div class="button-group">
      <button class="btn" onclick="window.location.href='/widget'">View Widget</button>
      <button class="btn" onclick="window.location.href='/simulator'">View Simulator</button>
    </div>
  </div>
  <div class="container fade-in" style="animation-delay: 0.4s;" id="faqSection">
    <h2>Frequently Asked Questions</h2>
    <div class="faq">
      <div class="faq-item" onclick="toggleFAQ(this)">
        <h3>What is Quant Trading?</h3>
        <div class="faq-answer">
          <p>Quant Trading uses mathematical models and algorithms to analyze financial markets and execute trades based on statistical analysis.</p>
        </div>
      </div>
      <div class="faq-item" onclick="toggleFAQ(this)">
        <h3>How does the simulator work?</h3>
        <div class="faq-answer">
          <p>Our simulator mimics real market conditions using live data, allowing you to practice trading with virtual funds and learn risk management without risking real money.</p>
        </div>
      </div>
      <div class="faq-item" onclick="toggleFAQ(this)">
        <h3>Can I really learn to trade effectively here?</h3>
        <div class="faq-answer">
          <p>Absolutely! Our platform is designed to provide educational content, practical tools, and interactive experiences to help you develop and refine your trading strategies.</p>
        </div>
      </div>
      <div class="faq-item" onclick="toggleFAQ(this)">
        <h3>Is support available if I need help?</h3>
        <div class="faq-answer">
          <p>Yes, we offer tutorials, guides, and customer support to assist you along your trading journey.</p>
        </div>
      </div>
    </div>
  </div>
  <script>
    function toggleFAQ(element) {{
      element.classList.toggle('active');
    }}
    window.addEventListener('scroll', function() {{
      const fadeInElements = document.querySelectorAll('.fade-in');
      const windowBottom = window.innerHeight + window.scrollY;
      fadeInElements.forEach(el => {{
        if (el.offsetTop < windowBottom - 100) {{
          el.style.animationPlayState = 'running';
        }}
      }});
    }});
  </script>

  {chat_api}
</body>
</html>
'''

# ---------- Simulator Page (Trading Simulator) ----------
# Lighter background, dark text with subtle green highlights.
simulator_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Stock Trading Simulator</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Montserrat', sans-serif;
      background: linear-gradient(135deg, #ffffff, #f0f0f0);
      margin: 0;
      padding: 20px;
      color: #333;
    }}
    nav a:hover {{
      color: #99ff99 !important;
    }}
    .container {{
      max-width: 900px;
      margin: 20px auto;
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 8px 16px rgba(0,0,0,0.1);
      padding: 30px;
    }}
    h1, h3 {{
      text-align: center;
      margin-top: 0;
      color: #006600;
    }}
    h1 {{
      font-size: 2.5rem;
    }}
    h3 {{
      font-size: 1.75rem;
      margin-top: 25px;
    }}
    label {{
      display: block;
      margin: 15px 0 5px;
      font-weight: 600;
      color: #333;
    }}
    input[type="text"], input[type="number"] {{
      width: 100%;
      padding: 12px;
      margin-bottom: 15px;
      border: 1px solid #ccc;
      border-radius: 6px;
      box-sizing: border-box;
      background-color: #f9f9f9;
      color: #333;
    }}
    button {{
      padding: 12px 25px;
      margin: 5px 2px;
      font-size: 1rem;
      background-color: #006600;
      color: #fff;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      transition: background-color 0.3s ease, transform 0.3s ease;
    }}
    button:hover {{
      background-color: #008000;
      transform: translateY(-2px);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      color: #333;
    }}
    th, td {{
      padding: 14px;
      text-align: center;
      border: 1px solid #ddd;
    }}
    th {{
      background-color: #f2f2f2;
      color: #333;
    }}
    .chart-container {{
      text-align: center;
      margin-top: 30px;
    }}
    .chart-container img {{
      width: 100%;
      max-width: 700px;
      border: 1px solid #ccc;
      border-radius: 6px;
    }}
    @media (max-width: 600px) {{
      .container {{ padding: 20px; }}
      h1 {{ font-size: 2rem; }}
      h3 {{ font-size: 1.5rem; }}
    }}
  </style>
</head>
<body>
  {nav_html}
  <div class="container">
    <h1>📈 Stock Trading Simulator</h1>

    <!-- Section to fetch and display stock data -->
    <div>
      <label for="stockSymbol">Enter Stock Symbol (e.g., AAPL, TSLA, NVDA):</label>
      <input type="text" id="stockSymbol" placeholder="Stock Symbol">
      <button onclick="getStockData()">Get Stock Price & Chart</button>
      <p id="stockPrice"></p>
    </div>

    <!-- Section for stock price chart -->
    <div class="chart-container">
      <h3>Stock Price History (1 Year)</h3>
      <img id="stockChart" alt="Stock Price Chart">
    </div>

    <!-- Section for buying and selling stocks -->
    <div>
      <h3>Buy / Sell Stocks</h3>
      <label for="tradeSymbol">Trade Stock Symbol:</label>
      <input type="text" id="tradeSymbol" placeholder="e.g., AAPL, RANDOM">
      <label for="tradeQuantity">Quantity:</label>
      <input type="number" id="tradeQuantity" value="1" min="1">
      <button onclick="buyStock()">Buy Stock</button>
      <button onclick="sellStock()">Sell Stock</button>
    </div>

    <!-- Portfolio Display -->
    <div>
      <h3>Your Portfolio</h3>
      <p>Cash: $<span id="cashAmount">10000.00</span></p>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Shares</th>
            <th>Avg. Price (USD)</th>
            <th>Current Price (USD)</th>
            <th>Value (USD)</th>
          </tr>
        </thead>
        <tbody id="portfolioTable"></tbody>
      </table>
    </div>

    <!-- Portfolio Performance Graph -->
    <div class="chart-container">
      <h3>Portfolio Performance</h3>
      <img id="portfolioChart" alt="Portfolio Performance Chart">
    </div>
  </div>

  {chat_api}

  <script>
    // Local portfolio object
    let portfolio = {{
      cash: 10000.0,
      stocks: {{}}
    }};

    // Load any saved portfolio data from localStorage
    function loadPortfolio() {{
      const savedData = localStorage.getItem('portfolioData');
      if (savedData) {{
        portfolio = JSON.parse(savedData);
      }}
    }}

    // Save portfolio data to localStorage
    function savePortfolio() {{
      localStorage.setItem('portfolioData', JSON.stringify(portfolio));
    }}

    function updatePortfolioTable() {{
      const table = document.getElementById('portfolioTable');
      table.innerHTML = '';
      for (const symbol in portfolio.stocks) {{
        const holding = portfolio.stocks[symbol];
        const currentPrice = holding.currentPrice || holding.avg_price;
        const value = (currentPrice * holding.quantity).toFixed(2);
        const row = `
          <tr>
            <td>${{symbol}}</td>
            <td>${{holding.quantity}}</td>
            <td>$${{holding.avg_price.toFixed(2)}}</td>
            <td>$${{currentPrice.toFixed(2)}}</td>
            <td>$${{value}}</td>
          </tr>
        `;
        table.innerHTML += row;
      }}
      document.getElementById('cashAmount').innerText = portfolio.cash.toFixed(2);
      savePortfolio();
    }}

    function fetchCurrentPrice(symbol) {{
      const xhr = new XMLHttpRequest();
      xhr.open("GET", "/get_stock_price/" + symbol, false);
      xhr.send();
      if (xhr.status === 200) {{
        const data = JSON.parse(xhr.responseText);
        return data.price || 0;
      }}
      return 0;
    }}

    function getStockData() {{
      const symbol = document.getElementById('stockSymbol').value.toUpperCase();
      if (!symbol) {{ alert("Please enter a stock symbol."); return; }}
      fetch("/get_stock_price/" + symbol)
        .then(res => res.json())
        .then(data => {{
          if (data.price) {{
            document.getElementById('stockPrice').innerText = "Stock Price: $" + data.price;
            fetch("/get_stock_price_chart/" + symbol)
              .then(res => res.json())
              .then(chartData => {{
                const chartImage = document.getElementById('stockChart');
                chartImage.src = chartData.chart ? "data:image/png;base64," + chartData.chart : "";
              }});
          }} else {{
            document.getElementById('stockPrice').innerText = "❌ Stock not found.";
          }}
        }});
    }}

    function buyStock() {{
      const symbol = document.getElementById('tradeSymbol').value.toUpperCase();
      const quantity = parseInt(document.getElementById('tradeQuantity').value);
      if (!symbol || quantity <= 0) {{
        alert("Invalid input.");
        return;
      }}
      const price = fetchCurrentPrice(symbol);
      if (!price) {{
        alert("Stock not found or price unavailable.");
        return;
      }}
      const totalCost = price * quantity;
      if (portfolio.cash < totalCost) {{
        alert("Insufficient funds.");
        return;
      }}
      portfolio.cash -= totalCost;
      if (portfolio.stocks[symbol]) {{
        let oldQty = portfolio.stocks[symbol].quantity;
        let oldAvg = portfolio.stocks[symbol].avg_price;
        let newAvg = ((oldQty * oldAvg) + (quantity * price)) / (oldQty + quantity);
        portfolio.stocks[symbol].quantity += quantity;
        portfolio.stocks[symbol].avg_price = newAvg;
        portfolio.stocks[symbol].currentPrice = price;
      }} else {{
        portfolio.stocks[symbol] = {{ quantity: quantity, avg_price: price, currentPrice: price }};
      }}
      updatePortfolioTable();
      alert(`Bought ${{quantity}} shares of ${{symbol}} at $${{price}} each.`);
    }}

    function sellStock() {{
      const symbol = document.getElementById('tradeSymbol').value.toUpperCase();
      const quantity = parseInt(document.getElementById('tradeQuantity').value);
      if (!symbol || quantity <= 0) {{
        alert("Invalid input.");
        return;
      }}
      if (!portfolio.stocks[symbol] || portfolio.stocks[symbol].quantity < quantity) {{
        alert("Not enough shares to sell.");
        return;
      }}
      const price = fetchCurrentPrice(symbol);
      if (!price) {{
        alert("Stock not found or price unavailable.");
        return;
      }}
      portfolio.cash += price * quantity;
      portfolio.stocks[symbol].quantity -= quantity;
      if (portfolio.stocks[symbol].quantity === 0) {{
        delete portfolio.stocks[symbol];
      }}
      updatePortfolioTable();
      alert(`Sold ${{quantity}} shares of ${{symbol}} at $${{price}} each.`);
    }}

    function getPortfolioChart() {{
      fetch("/get_portfolio_chart", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(portfolio)
      }})
      .then(res => res.json())
      .then(data => {{
        const chartElem = document.getElementById('portfolioChart');
        chartElem.src = data.chart ? "data:image/png;base64," + data.chart : "";
      }});
    }}

    loadPortfolio();
    updatePortfolioTable();

    setInterval(() => {{
      if (portfolio.stocks["RANDOM"]) {{
        const newPrice = fetchCurrentPrice("RANDOM");
        portfolio.stocks["RANDOM"].currentPrice = newPrice;
        updatePortfolioTable();
      }}
      getPortfolioChart();
    }}, 10000);
  </script>
</body>
</html>
'''

# ---------- Widget Page (Full-Screen TradingView Widget) ----------
widget_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TradingView Widget</title>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: 'Montserrat', sans-serif;
    }}
    #widgetContainer {{
      width: 100vw;
      height: 100vh;
    }}
    nav {{
      background: #002400;
      padding: 10px;
      text-align: center;
    }}
    nav a {{
      color: #66ff66;
      margin: 0 15px;
      text-decoration: none;
      font-size: 1.2rem;
      transition: color 0.3s ease;
    }}
    nav a:hover {{
      color: #b8ffb8;
    }}
  </style>
</head>
<body>
  {nav_html}
  <div id="widgetContainer">
    <div id="tradingview_f0528" style="width: 100%; height: 100%;"></div>
  </div>

  {chat_api}

  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
    new TradingView.widget(
    {{
      "autosize": true,
      "symbol": "FX:EURUSD",
      "timezone": "Etc/UTC",
      "theme": "light",
      "style": "1",
      "locale": "en",
      "enable_publishing": true,
      "withdateranges": true,
      "range": "YTD",
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "details": true,
      "hotlist": true,
      "calendar": true,
      "show_popup_button": true,
      "popup_width": "1000",
      "popup_height": "650",
      "container_id": "tradingview_f0528"
    }});
  </script>
</body>
</html>
'''

# ---------- Flask Routes ----------

@app.route('/')
def home():
    return render_template_string(home_html)

@app.route('/simulator')
def simulator():
    return render_template_string(simulator_html)

@app.route('/widget')
def widget():
    return render_template_string(widget_html)

@app.route('/get_stock_price/<symbol>')
def api_get_stock_price(symbol):
    symbol_up = symbol.upper()
    if symbol_up == "RANDOM":
        price = round(100 * (1 + random.uniform(-0.1, 0.1)), 2)
        return jsonify({"price": price})
    else:
        try:
            stock = yf.Ticker(symbol_up)
            hist = stock.history(period="1d")
            if hist.empty:
                return jsonify({"price": 0})
            price = round(hist['Close'].iloc[-1], 2)
            return jsonify({"price": price})
        except Exception as e:
            print(f"Error fetching price for {symbol_up}: {e}")
            return jsonify({"price": 0})

@app.route('/get_stock_price_chart/<symbol>')
def api_get_stock_price_chart(symbol):
    if symbol.upper() == "RANDOM":
        return jsonify({"chart": ""})
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")['Close']
        if hist.empty:
            return jsonify({"chart": ""})
    except Exception as e:
        print(f"Error fetching 1y history for {symbol}: {e}")
        return jsonify({"chart": ""})

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(hist.index, hist.values, color="#3d5a80", linewidth=2)
    ax.set_title(f"{symbol.upper()} Price History (1 Year)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.autofmt_xdate()

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    chart_data = base64.b64encode(img.read()).decode('utf-8')
    plt.close(fig)
    return jsonify({"chart": chart_data})

def compute_local_portfolio_value(local_portfolio):
    total = local_portfolio["cash"]
    for sym, data in local_portfolio["stocks"].items():
        cprice = data.get("currentPrice", data["avg_price"])
        total += cprice * data["quantity"]
    return round(total, 2)

@app.route('/get_portfolio_chart', methods=['POST'])
def get_portfolio_chart():
    local_portfolio = request.get_json()
    if not local_portfolio:
        return jsonify({"chart": ""})
    val = compute_local_portfolio_value(local_portfolio)
    now = datetime.now()
    portfolio_history.append((now, val))
    times = [t.strftime("%H:%M:%S") for t, _ in portfolio_history]
    values = [v for _, v in portfolio_history]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(times, values, color="#2f4858", marker='o', linestyle='-', linewidth=2)
    ax.set_title("Portfolio Performance")
    ax.set_xlabel("Time")
    ax.set_ylabel("Portfolio Value (USD)")
    ax.grid(True, linestyle="--", alpha=0.5)
    if len(values) > 1:
        margin = 0.05 * (max(values) - min(values))
        ax.set_ylim(min(values) - margin, max(values) + margin)
    plt.xticks(rotation=45)

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches="tight")
    img.seek(0)
    chart_data = base64.b64encode(img.read()).decode('utf-8')
    plt.close(fig)
    return jsonify({"chart": chart_data})

if __name__ == '__main__':
    app.run(debug=True)
