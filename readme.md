# Option Hedging App

The **Option Hedging App** is a Python-based application designed to help users manage and analyze options trading data in real-time. It integrates with the Binance API to fetch live market data using a websocket, calculate option prices using the Black-Scholes model, and execute buy/sell orders. The app also provides tools for delta hedging and identifying mispriced options by leverging multithreading and asynchronous operations.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Real-Time Option Data**: Fetch and display live option data (puts and calls) for a selected token.
- **Black-Scholes Calculator**: Calculate option prices using the Black-Scholes model.
- **Delta Hedging**: Automatically balance deltas by placing buy/sell orders.
- **Misprice Detection**: Identify mispriced options based on theoretical vs. market prices.
- **Binance Integration**: Connect to Binance API for live data and order execution.
- **Interactive UI**: Command-line interface for easy navigation and interaction.

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Vman384/Crypto-Options-App.git
   cd Option-Hedging-App
   ```

2. **Install Dependencies**: Ensure you have Python 3.8+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Binance API Keys**:
   - Obtain your Binance API key and secret from the Binance website.
   - Enter them when prompted during the app's first run.

---

## Usage

### Run the Application:
```bash
python main.py
```

### Main Menu:
The app will display a menu with the following options:
- **Live Option Data**: View real-time option data for the selected token.
- **Change Token**: Set the token (e.g., BTC, ETH) for analysis.
- **Get Coin Price**: Fetch the current price of the selected token.
- **Get Current Spot Holdings**: Display your current spot holdings on Binance.
- **Sell Order**: Place a sell order for a specified symbol and quantity.
- **Buy Order**: Place a buy order for a specified symbol and quantity.
- **Mispriced Options**: Identify mispriced options using the Black-Scholes model.
- **Balance Deltas**: Automatically balance deltas by placing buy/sell orders.

### Example Workflow:
1. Select a token (e.g., BTC).
2. View live option data for puts and calls.
3. Use the Black-Scholes calculator to identify mispriced options.
4. Execute buy/sell orders to hedge your portfolio.

---

## Dependencies

The app relies on the following Python libraries:
- **pandas**: For data manipulation and analysis.
- **numpy**: For numerical calculations.
- **scipy**: For statistical functions (e.g., `norm.cdf` in Black-Scholes).
- **python-binance**: For Binance API integration.
- **websocket-client**: For real-time data streaming.
- **asyncio**: For asynchronous programming.
- **multiprocessing**: For CPU intensive calculations.
- **thread**: For using multithreading when fetching data.


All dependencies are listed in `requirements.txt`.

---

## File Structure

```plaintext
Option-Hedging-App/
├── UI.py                # User interface and menu rendering.
├── main.py              # Entry point for the application.
├── data_parser.py       # Fetches and parses live data from Binance.
├── order_sender.py      # Handles buy/sell orders on Binance.
├── options_calculator.py # Implements Black-Scholes and delta calculations.
├── endpoints.py         # Defines API endpoints for Binance.
├── common.py            # Utility functions (e.g., truncation).
├── requirements.txt     # Lists all dependencies.
```

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/YourFeatureName
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeatureName
   ```
5. Open a pull request.

Please ensure your code follows the project's style and includes appropriate tests.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgments

- **Binance API**: For providing real-time market data and trading functionality.
