import sys
from data_parser import DataParser
import asyncio
from inspect import iscoroutinefunction


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
            except ValueError:
                print("Invalid input. Please enter a number.")
        
    def quit(self):
        """Exits the program."""
        print("Exiting...")
        sys.exit(0)
