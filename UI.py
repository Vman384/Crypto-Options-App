import sys

class UI:
    def __init__(self) -> None:
        self.menu_options = {}
    
    def add_menu_option(self, name, function):
        """Adds a menu option with a corresponding function."""
        self.menu_options[name] = function
    
    def render_menu(self):
        """Displays the menu and prompts the user for input."""
        while True:
            print("\nMenu")
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
                    self.menu_options[option_name]()
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    
    def quit(self):
        """Exits the program."""
        print("Exiting...")
        sys.exit(0)
