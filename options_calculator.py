import numpy as np
import pandas as pd
from scipy.stats import norm
from data_parser import DataParser
from concurrent.futures import ThreadPoolExecutor
import asyncio
from threading import Thread, Semaphore
from queue import Queue
from multiprocessing import Pool, cpu_count
import time
from endpoints import Endpoints


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
        symbolsDf = pd.DataFrame(self.dataParser.data)['s']  # Extract symbols dataframe
        tokenPriceTask = asyncio.create_task(self.dataParser.get_live_product_data(endpoint=Endpoints.TICKERPRICE))  # Fetch token price asynchronously and refresh it in the background
        while True:
            asyncio.sleep(1)
            print(self.dataParser.data)



        # Step 2: Function to fetch option data in threads
        async def fetch_option_data(symbol):
            try:
                asyncio.create_task(self.dataParser.get_live_product_data(symbol + "@ticker"))
                await asyncio.sleep(1)
                optionData = self.dataParser.data
                return optionData
            except Exception as e:
                print(e)
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
        sem = Semaphore() #using a binary semaphore as want only 1 thread writing to the options_data_list at a time

        def fetch_data_thread(symbol):
            option_data = fetch_option_data(symbol)
            if option_data:
                sem.acquire()
                option_data_list.append(option_data)
                sem.release()

        

        for symbol in symbolsDf.tail(10):  # Fetch first 10 symbols
            thread = Thread(target=fetch_data_thread, args=(symbol,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        # Step 5: Multiprocessing for calculations
        with Pool(processes=cpu_count()) as pool:
            results = pool.map(process_option, [(tokenPrice, data) for data in option_data_list]) #using multiprocessing instead of threading as can take advantage of multiple cores and since there is no i/o

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
    
    async def mispriced_options1(self) -> None:
        # Step 1: Fetch initial options data asynchronously
        await self.dataParser.get_live_product_data(self.dataParser.token + "@markPrice", 2, 2)
        symbolsDf = pd.DataFrame(self.dataParser.data[0]['s'])  # Extract symbols dataframe
        tokenPrice = await self.dataParser.get_current_coin_price()  # Fetch token price
        print(f"Token Price: {tokenPrice}")

        # Shared thread-safe queue
        option_data_queue = Queue(maxsize=50)  # Limit queue size to prevent overloading
        semaphore = Semaphore()  # Synchronization mechanism for threads

        # Step 2: Producer - Fetch option data continuously
        def fetch_option_data(symbol):
            try:
                asyncio.create_task(self.dataParser.get_live_product_data(symbol + "@ticker"))
                return
            except Exception as e:
                print(f"Error fetching option data for {symbol}: {e}")
                return None

        def producer_thread(symbol):
            while True:  # Keep fetching data in the background
                option_data = fetch_option_data(symbol)
                if option_data:
                    semaphore.acquire()
                    if not option_data_queue.full():  # Avoid blocking if queue is full
                        option_data_queue.put(option_data)
                    semaphore.release()
                time.sleep(1)  # Pause briefly to avoid excessive API calls

        # Step 3: Consumer - Process option data
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
                print(f"Processed: {option_data['s']} -> Predicted Price: {predicted_price}")
                return predicted_price
            except Exception as e:
                print(f"Error processing option {option_data}: {e}")
                return None

        # Step 4: Start producer threads for continuous data fetching
        producer_threads = []
        print(symbolsDf)
        for symbol in symbolsDf.tail(10):  # Use the last 10 symbols
            thread = Thread(target=producer_thread, args=(symbol,))
            producer_threads.append(thread)
            thread.start()

        # Step 5: Start consumer processes for continuous price calculations
        def consumer():
            with Pool(processes=cpu_count()) as pool:
                while True:  # Continuously consume data from the queue
                    if not option_data_queue.empty():
                        option_data = option_data_queue.get()
                        pool.apply_async(process_option, [(tokenPrice, option_data)])
                    else:
                        time.sleep(0.1)  # Small delay to prevent busy-waiting

        consumer_thread = Thread(target=consumer)
        consumer_thread.start()

        # Step 6: Keep producers and consumers running
        try:
            for thread in producer_threads:
                thread.join()
            consumer_thread.join()
        except KeyboardInterrupt:
            print("Stopping producers and consumers...")




        