import asyncio
import numpy as np
from scipy.stats import norm
from data_parser import DataParser
from concurrent.futures import ThreadPoolExecutor
import asyncio
from threading import Thread
from multiprocessing import Pool, cpu_count

class OptionsCalculator:
    def __init__(self, dataParser: DataParser) -> None:
        self.dataParser = dataParser

    def account_delta_calculator(self) -> dict[str, int]: 
        """
            Since I am in Australia I do not have access to trade binance options therefore can not verify if the this function works
        """
        options = self.dataParser.get_current_holdings_options()
        spot = self.dataParser.get_current_holdings_spot()
        totalDelta = {}    
        # Loop through the positions
        for option in options:
            delta = float(option["delta"])
            underlying = option["underlying"]
            totalDelta[underlying[0:2]] = delta
        for coin in spot.keys():
            try:
                totalDelta[coin] += spot[coin] 
            except KeyError:
                totalDelta[coin] = spot[coin]

        return totalDelta

    async def mispriced_options(self) -> float:
        # Step 1: Fetch initial options data asynchronously
        await self.dataParser.get_live_product_data(self.dataParser.token + "@markPrice", 2, 2)
        symbolsDf = self.dataParser.data['s']  # Extract symbols dataframe
        tokenPrice = asyncio.create_task(self.dataParser.get_current_coin_price())  # Fetch token price asynchronously and refresh it in the background
        await asyncio.sleep(1) #wait to get token data

        # Step 2: Function to fetch option data in threads
        def fetch_option_data(symbol):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                option_data = loop.run_until_complete(self.dataParser.get_live_product_data(symbol + "@ticker"))
                return option_data
            except Exception as e:
                print(f"Error fetching option data for {symbol}: {e}")
                return None

        # Step 3: Function to process option data with multiprocessing
        def process_option(args):
            token_price, option_data = args
            try:
                symbol_parts = option_data['s'].split("-")
                strike_price = float(symbol_parts[2])
                call_or_put = symbol_parts[3]
                predicted_price = self.black_scholes(
                    token_price,
                    strike_price,
                    option_data['t'],  # Time to expiry
                    option_data['r'],  # Risk-free rate
                    option_data['v'],  # Volatility
                    call_or_put
                )
                return predicted_price
            except Exception as e:
                print(f"Error processing option {option_data}: {e}")
                return None

        # Step 4: Threading for fetching data
        threads = []
        option_data_list = []

        def fetch_data_thread(symbol):
            option_data = fetch_option_data(symbol)
            if option_data:
                option_data_list.append(option_data)

        
        while True:
            for symbol in symbolsDf.tail(10):  # Fetch last 10 symbols
                thread = Thread(target=fetch_data_thread, args=(symbol,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()
            # Step 5: Multiprocessing for calculations
            with Pool(processes=cpu_count()) as pool:
                results = pool.map(process_option, [(tokenPrice, data) for data in option_data_list])

            print("Predicted Prices:", results)
        return results
    
    def black_scholes(self, S, K, T, r, vega, option_type='call') -> float:
        """
        Calculate the Black-Scholes option price.

        Parameters:
        S : float
            Current stock price
        K : float
            Strike price
        T : float
            Time to maturity (in years)
        r : float
            Risk-free interest rate (annualized)
        vega : float
            Volatility of the underlying stock (annualized)
        option_type : str
            Type of option: 'C' or 'P'

        Returns:
        float
            Option price
        """
        d1 = (np.log(S / K) + (r + 0.5 * vega()**2) * T) / (vega() * np.sqrt(T))
        d2 = d1 - vega() * np.sqrt(T)
        
        if option_type == 'C':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        elif option_type == 'P':
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'C' or 'P'")
        
        return price




        