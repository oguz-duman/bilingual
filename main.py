import os
from InquirerPy import inquirer

from document import DocumentCreater


class MenuNavigator:

    def __init__(self):
        self.state = "main_menu"
        self.running = True

        self.states = {
            "main_menu": self.main_menu,
            "start_over": self.start_over,
            "continue": self.continue_process,
            "exit": self.exit_program
        }


    def run(self):
        while self.running:
            self.clear_console()
            self.states[self.state]()  # Call the method associated with the current state


    def main_menu(self):
        choice = inquirer.select(
            message="Start a new process or continue with an existing one?",
            choices=["Start Over", "Continue", "--Exit--"]
        ).execute()

        if choice == "Start Over":
            self.confirm(op1="start_over", op2="main_menu", mes="Starting a new process will delete the all cached data. Are you sure?")

        elif choice == "Continue":
            self.state = "continue"

        else:
            self.state = "exit"


    def start_over(self):
        try:
            document_creater.start_aligning()           
            document_creater.create_bilingual_doc()
        except Exception as e:
            print("Error during process:", e)
            self.running = False                    # exit the program


    def continue_process(self):
        document_creater.continue_aligning()
        document_creater.create_bilingual_doc()
        try:
            pass
        except Exception as e:
            print("Error during process:", e)
            self.running = False                    # exit the program


    def confirm(self, op1, op2, mes):
        choice = inquirer.select(
            message=mes,
            choices=["Yes", "No"]
        ).execute()
        self.state = op1 if choice == "Yes" else op2


    def exit_program(self):
        self.running = False
    

    def clear_console(self):    
        os.system("cls" if os.name == "nt" else "clear")


    def warning_message(self, message):
        self.clear_console()
        print(message, "\n")
        input("Press Enter to continue...")
        self.clear_console()


# create class objects
menu_navigator = MenuNavigator()
document_creater = DocumentCreater()

# run the menu navigator
menu_navigator.run()
