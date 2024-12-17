import sys
import pandas as pd
from data_parser import DataParser
import asyncio
from inspect import iscoroutinefunction
from endpoints import Endpoints


class UI:
    def __init__(self, dataParser: DataParser) -> None:
        self.menu_options = {}
        self.dataParser = dataParser
    
    def add_menu_option(self, name, function):
        """Adds a menu option with a corresponding function."""
        self.menu_options[name] = function
    
    def render_menu(self):
        """Displays the menu and prompts the user for input."""
        while True:
            print("\nMenu")
            print("----")
            print(f"Current token selected is: {self.dataParser.token}")
            print("----")
            for index, option in enumerate(self.menu_options.keys(), start=1):
                print(f"{index}: {option}")
            print("0: Exit")
            
            try:
                choice = int(input("\nEnter your choice: "))
                if choice == 0:
                    self.quit()
                elif 1 <= choice <= len(self.menu_options):
                    option_name = list(self.menu_options.keys())[choice - 1]
                    selected_function = self.menu_options[option_name]

                    # Check if the function is asynchronous
                    if iscoroutinefunction(selected_function):
                        asyncio.run(selected_function())  # Run async function
                    else:
                        selected_function()  # Run sync function
                else:
                    print("Invalid choice. Please try again.")
            except Exception as e:
                print(e)
                print("Invalid input. Please enter a number.")
        
    def quit(self):
        """Exits the program."""
        print("Exiting...")
        sys.exit(0)
    
    async def display_option_data(self):
        """Displays the fetched option data in real time."""
        token = self.dataParser.token
        if not token.endswith("@markPrice"):
            token += "@markPrice"

        # Start fetching data in the background
        task = asyncio.create_task(self.dataParser.get_live_product_data(token=token, endpoint=Endpoints.OPTIONWEBSOCKET.value))
        try:
            try:
                while True:  # Keep displaying the data as it arrives
                    await asyncio.sleep(1)  # Delay for a moment before checking for updates, check for a better way later, should be able to dynamically wait for the thread to be done line wait in c
                    if self.dataParser.data is not None:
                        try:
                            df = pd.DataFrame(self.dataParser.data)

                            df.drop(columns=["e", "E"], errors="ignore")  # Drop 'e' and 'E' columns
    
                            df_puts = df[df['s'].str.endswith('P')].reset_index(drop=True)  # Filter puts
                            df_calls = df[df['s'].str.endswith('C')].reset_index(drop=True)  # Filter calls

                            # Display the results
                            print("Puts:\n", df_puts.tail(self.dataParser.data_rows))
                            print("\nCalls:\n", df_calls.tail(self.dataParser.data_rows))

                        except:
                            continue
            except asyncio.CancelledError:
                print("Data display cancelled. Returning to menu")
                task.cancel()
        except KeyboardInterrupt:
            task.cancel()
