import numpy as np
import pandas as pd
from scipy.stats import norm
from data_parser import DataParser
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import asyncio
from threading import Thread, Semaphore
from queue import Queue
from multiprocessing import Pool, cpu_count
import time
from endpoints import Endpoints


class OptionsCalculator:
    def __init__(self, dataParser: DataParser) -> None:
        self.dataParser = dataParser
        self.tokenPrice = None

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

    async def mispriced_options1(self) -> float:
        if len(self.dataParser.token) <= 4: #Did not just do an ends with check so other coins can be checked such as BTCETH price
            token = self.dataParser.token.lower() + "usdt@aggTrade"
        else:
            print("Invalid token, can only price against usdt")
            return
        # Step 1: Fetch initial options data asynchronously
        await self.dataParser.get_live_product_data(self.dataParser.token + "@markPrice", 2, 2, Endpoints.OPTIONWEBSOCKET.value) #should make api call later
        symbolsDf = pd.DataFrame(self.dataParser.data)['s']  # Extract symbols dataframe
        print(token)
        tokenPriceTask = asyncio.create_task(self.dataParser.get_live_product_data(token=token, endpoint=Endpoints.TOKENWEBSOCKET.value))  # Fetch token price asynchronously and refresh it in the background
        try:
            while True:
                await asyncio.sleep(1)
                try:
                    print(self.dataParser.data)
                    tokenPrice = self.dataParser.data['p']
                    print(tokenPrice)
                except ValueError:
                    continue

                if tokenPrice:

                    # Step 2: Function to fetch option data in threads
                    def fetch_option_data(symbol):
                        try:
                            asyncio.run(self.dataParser.get_live_product_data(symbol + "@ticker"))
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
                        print(option_data_list)
                        if option_data:
                            sem.acquire()
                            option_data_list.append(option_data)
                            sem.release()

                    

                    for symbol in symbolsDf.tail(10):  # Fetch first 10 symbols
                        optionDataTask = asyncio.create_task(self.dataParser.get_live_product_data(token=symbol+ "@ticker", endpoint=Endpoints.OPTIONWEBSOCKET.value))  # Fetch token price asynchronously and refresh it in the background
                        await asyncio.sleep(1)
                        print(self.dataParser.data)
                        # thread = Thread(target=fetch_data_thread, args=(symbol,), daemon=True)
                        # threads.append(thread)
                        # thread.start()

                    # # Wait for all threads to finish
                    # for thread in threads:
                    #     thread.join()
                    # Step 5: Multiprocessing for calculations
                    with Pool(processes=cpu_count()) as pool:
                        results = pool.map(process_option, [(tokenPrice, data) for data in option_data_list]) #using multiprocessing instead of threading as can take advantage of multiple cores and since there is no i/o

                    print("Predicted Prices:", results)
        except KeyboardInterrupt:
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
    
    

    async def fetch_token_price_background(self, token: str):
        """
        Continuously fetch the live token price and update self.dataParser.data.
        """
        try:
            tokenDataParser = DataParser(self.dataParser.client)
            asyncio.create_task(tokenDataParser.get_live_product_data(token=token, endpoint=Endpoints.TOKENWEBSOCKET.value))
            while True:
                await tokenDataParser.get_live_product_data(token=token, endpoint=Endpoints.TOKENWEBSOCKET.value)
                await asyncio.sleep(0.5)  # Fetch data every 0.5 seconds
                self.tokenPrice = tokenDataParser.data['p']
                print(self.tokenPrice)
        except asyncio.CancelledError:
            print("Token price background task was cancelled.")

    async def fetch_option_data_background(self, symbol: str, queue: asyncio.Queue):
        """
        Continuously fetch live option data and put it into a queue.
        """
        optionDataParser = DataParser(self.dataParser.client)
        try:
            while True:
                await optionDataParser.get_live_product_data(symbol + "@ticker", endpoint=Endpoints.OPTIONWEBSOCKET.value)
                option_data = optionDataParser.data
                await queue.put(option_data)  # Place fetched data into the queue
                await asyncio.sleep(1)  # Fetch data every 1 second
        except asyncio.CancelledError:
            print(f"Option data task for {symbol} was cancelled.")

    def process_option(self, args):
        """
        Process option data using Black-Scholes calculation.
        """
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
            print(f"Processed Price: {predicted_price}")
            return predicted_price
        except Exception as e:
            print(f"Error processing option {option_data}: {e}")
            return None

    async def mispriced_options(self):
        """
        Main function to fetch live token price, fetch options data, and process it.
        """
        # Step 1: Validate token
        if len(self.dataParser.token) <= 4:
            token = self.dataParser.token.lower() + "usdt@aggTrade"
        else:
            print("Invalid token, can only price against usdt")
            return

        # Step 2: Start token price fetcher using executor to run in background
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor()
        # loop.run_in_executor(executor, asyncio.create_task, self.fetch_token_price_background(token))
        loop.create_task(self.fetch_token_price_background(token))
        
        await asyncio.sleep(1)  # Allow initial data to populate

        # Step 3: Fetch initial options data and prepare symbols
        await self.dataParser.get_live_product_data(self.dataParser.token + "@markPrice", 2, 2, Endpoints.OPTIONWEBSOCKET.value)
        symbolsDf = pd.DataFrame(self.dataParser.data)['s']
        print("Symbols to fetch:", symbolsDf)

        # Step 4: Create an asyncio.Queue for communication
        option_data_queue = asyncio.Queue()

        # Step 5: Start option data fetchers
        option_tasks = []
        for symbol in symbolsDf.tail(10):  # Limit to 10 symbols
            task = asyncio.create_task(self.fetch_option_data_background(symbol, option_data_queue))
            option_tasks.append(task)

        # Step 6: Process fetched data with ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            try:
                while True:
                    # Get the latest token price
                    token_price = self.tokenPrice
                    if not token_price:
                        print("Waiting for token price data...")
                        await asyncio.sleep(1)
                        continue

                    # Fetch option data from the queue
                    option_data = await option_data_queue.get()
                    if option_data:
                        # Submit the processing task to the process pool
                        executor.submit(self.process_option, (token_price, option_data))

            except KeyboardInterrupt:
                print("Stopping all tasks...")

            finally:
                # Step 7: Cancel all background tasks
                for task in option_tasks:
                    task.cancel()
                print("All tasks stopped.")




        