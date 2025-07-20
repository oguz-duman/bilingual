import os
import tempfile
import subprocess
import re
import pickle
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

from deep_translator import GoogleTranslator
from rich.progress import Progress
from InquirerPy import inquirer


class BilingualCreater():

    def __init__(self):
        # variables to hold the paragraphs
        self.tr_par = []
        self.en_par = []
        self.trans_par = []
        self.index_pos = 0      # to keep the position of last processed text 
        self.tot_mismatch = 0


    def start_over(self):
        """  """
        self.clear_cache()
        self.read_paragraphs()        
        self.translate_tr_to_en()
        self.cache_data()               # cache the translated data
        self.align_unmatchings()
        self.cache_data()               # cache the corrections made so far


    def continue_process(self):
        """  """
        self.fetch_cached_data()
        self.align_unmatchings()
        self.cache_data()               # cache the corrections made so far


    def select_file(self, message):
        """  """
        self.warning_message(message)

        Tk().withdraw()
        file_path = askopenfilename(
            title=message,
            filetypes=[("TXT files", "*.txt")]
        )
        if not file_path:
            raise FileNotFoundError("No file is chosen!")

        return file_path


    def read_paragraphs(self):
        """  """
        # prompt user to select the input files
        tr_path = self.select_file("Select the Turkish input file.")
        en_path = self.select_file("Select the English input file.")

        # Read the turkish and english texts
        with open(tr_path, 'r', encoding='utf-8') as file:
            tr_text = file.read()

        with open(en_path, 'r', encoding='utf-8') as file:
            en_text = file.read()

        # remove the extra newlines
        tr_text = re.sub(r'[\n]{2,}', '\n\n', tr_text)
        en_text = re.sub(r'[\n]{2,}', '\n\n', en_text)
    
        # split to paragraphs
        self.tr_par = tr_text.split('\n\n') 
        self.en_par = en_text.split('\n\n') 


    def translate_tr_to_en(self):
        """  """
        # Translate the turkish paragraphs to english
        translator = GoogleTranslator(source='tr', target='en')
        
        with Progress(transient=True) as progress:
            task = progress.add_task("[green]Creating translated data...", total=len(self.tr_par))

            for i, paragraph in enumerate(self.tr_par):
                try:
                    self.trans_par.append(translator.translate(paragraph))
                except:
                    time.sleep(1) 
                    self.trans_par.append(translator.translate(paragraph))      # try again

                # Update progress
                progress.update(task, advance=1, description=f"[green]Creating translated data {i+1}/{len(self.tr_par)}...")
            

    def cache_data(self):
        """  """
        # cache the turkish paragraphs
        with open("cache/tr_par.pickle", "wb") as f:
            pickle.dump(self.tr_par, f)
        # cache the english paragraphs
        with open("cache/en_par.pickle", "wb") as f:
            pickle.dump(self.en_par, f)
        # cache the translated data
        with open("cache/trans_par.pickle", "wb") as f:
            pickle.dump(self.trans_par, f)
        # cache the index position
        with open("cache/index_pos.pickle", "wb") as f:
            pickle.dump(self.index_pos, f)
        # cache the total mismatch number
        with open("cache/tot_mismatch.pickle", "wb") as f:
            pickle.dump(self.tot_mismatch, f)


    def fetch_cached_data(self):
        """  """
        # fetch the turkish paragraphs
        with open("cache/tr_par.pickle", 'rb') as f:
            self.tr_par = pickle.load(f)
        # fetch the english paragraphs
        with open("cache/en_par.pickle", 'rb') as f:
            self.en_par = pickle.load(f)
        # fetch the translated data
        with open("cache/trans_par.pickle", 'rb') as f:
            self.trans_par = pickle.load(f)
        # fetch the index position
        with open("cache/index_pos.pickle", 'rb') as f:
            self.index_pos = pickle.load(f)
        # fetch the total mismatch number
        with open("cache/tot_mismatch.pickle", 'rb') as f:
            self.tot_mismatch = pickle.load(f)


    def align_unmatchings(self):
        """  """
        unmatching_indexes = self.similarity_check()

        # While there is a mismatch
        while unmatching_indexes:  
            self.print_mismatch(unmatching_indexes[0])       # print the first mismatch
            
            # print the progress
            print("\n")
            if self.tot_mismatch != 0:
                print(f"{self.tot_mismatch - len(unmatching_indexes)}/{self.tot_mismatch} -- {int((self.tot_mismatch - len(unmatching_indexes)) / self.tot_mismatch * 100)}%\n")
            
            # prompt the user to selecet the operation
            choice = inquirer.select(
                message="Select an option",
                choices=["Ok", "Remove", "Merge", "Edit", "Add", "--Finish--", "--Save and Exit--"]
            ).execute()

            # Take actions according to selected operation
            if choice == "Ok":
                self.index_pos = unmatching_indexes[0]
            
            elif choice == "Remove":
                lan = self.promt_for_language()
                indexes = self.prompt_for_index_list()

                # check if the index input is valid
                if indexes is None:
                    continue

                # remove the selected index
                if lan == "en":
                    for index in indexes:
                        self.en_par.pop(int(index))
                elif lan == "tr":
                    for index in indexes:
                        self.tr_par.pop(int(index))
                        self.trans_par.pop(int(index))
                else:
                    continue


            elif choice == "Merge":
                lan = self.promt_for_language()
                indexes = self.prompt_for_index_list()

                # check if the index input is valid
                if indexes is None and len(indexes) != 2:
                    continue

                # merge the texts of selected indexes
                if lan == "en":
                    self.en_par[min(indexes)] += " " + self.en_par[max(indexes)]
                    self.en_par.pop(max(indexes))
                elif lan == "tr":
                    self.tr_par[min(indexes)] += " " + self.tr_par[max(indexes)]
                    self.tr_par.pop(max(indexes))

                    self.trans_par[min(indexes)] += " " + self.trans_par[min(indexes)]
                    self.trans_par.pop(max(indexes))
                else:
                    continue      

            
            elif choice == "Edit":
                lan = self.promt_for_language()
                index = self.prompt_for_index()
            
                # check if the index and text input is valid
                if index is None:
                    continue
                
                # add the text to the selected index
                if lan == "en":
                    self.en_par[index] = self.edit_text_with_editor(self.en_par[index])

                elif lan == "tr":
                    self.tr_par[index] = self.edit_text_with_editor(self.tr_par[index])
                    self.trans_par[index] = self.tr_par[index]
                else:
                    continue
                
            elif choice == "Add":
                lan = self.promt_for_language()
                index = self.prompt_for_index()
                text = self.prompt_for_text()

                # check if the index and text input is valid
                if index is None or text is None:
                    continue
                
                # add the text to the selected index
                if lan == "en":
                    self.en_par.insert(index, text)
                elif lan == "tr":
                    self.tr_par.insert(index, text)
                    self.trans_par.insert(index, text)
                else:
                    continue

            elif choice == "--Finish--":
                self.cache_data()
                self.create_doc()

            elif choice == "--Save and Exit--":
                self.cache_data()
                exit()

            # Find the all unmatching paragraph indexes again
            unmatching_indexes = self.similarity_check()

        self.cache_data()
        self.create_doc()


    def similarity_check(self):
        """  """
        unmatching_indexes = []
        for i, (trans_par, en_par) in enumerate(zip(self.trans_par, self.en_par)):     
            if i <= self.index_pos:
                continue 
            # calculate the Jaccard similarity
            trans_words, en_words = set(trans_par.split()), set(en_par.split())
            intersection = len(trans_words & en_words)
            union = len(trans_words | en_words)
            similarity = intersection / union if union != 0 else 0
            
            # if the similarity is less than the threshold, add the index to the list
            if similarity < 0.05:
                unmatching_indexes.append(i)
            
        if self.tot_mismatch == 0:
            self.tot_mismatch = len(unmatching_indexes)
                
        return unmatching_indexes


    def print_mismatch(self, index):
        """  """
        self.clear_console()
        left = []
        right = []

        # prepare the text to print
        for x in range(index-3, index+3):
            if x > len(self.en_par)-1 or x < 0:
                continue
            if x == index:
                left.append(f"\033[31m------------------------ {x} ------------------------\033[0m")
            else:
                left.append(f"------------------------ {x} ------------------------")
            left.append(f"{self.en_par[x]}")
        
        # prepare the text to print
        for x in range(index-3, index+3):
            if x > len(self.tr_par)-1 or x < 0:
                continue
            if x == index:
                right.append(f"\033[31m------------------------ {x} ------------------------\033[0m")
            else:
                right.append(f"------------------------ {x} ------------------------")
            right.append(f"{self.tr_par[x]}")

        self.print_side_by_side(left, right)
    

    def print_side_by_side(self, left_texts, right_texts, row_len=70):

        def wrap_text(text, max_len):
            words = text.split()
            lines = []
            line = ""

            for word in words:
                if len(line) + len(word) + 1 <= max_len:
                    line += word + " "
                else:
                    lines.append(line.strip())
                    line = word + " "
            if line:
                lines.append(line.strip())
            return lines

        # Wrap all texts from left and right lists
        left_lines = []
        right_lines = []

        for txt_left, txt_right in zip(left_texts, right_texts):
            wrapped_left = wrap_text(txt_left, row_len)
            wrapped_right = wrap_text(txt_right, row_len)

            # equalize left and right block heights
            while len(wrapped_right) < len(wrapped_left):
                wrapped_right.append("")
            while len(wrapped_left) < len(wrapped_right):
                wrapped_left.append("")

            left_lines.extend(wrapped_left)
            left_lines.append("")  # Add blank line between blocks

            right_lines.extend(wrapped_right)
            right_lines.append("")  # Add blank line between blocks

        # Print line by line
        for l, r in zip(left_lines, right_lines):
            if "\033[31m" in l:
                print(l.ljust(row_len+9) + " | " + r)
            else:
                print(l.ljust(row_len) + " | " + r)
            

    def clear_cache(self):
        """  """
        # clear all the docx, pdf and txt files in the cahce directory
        folder_path = os.path.join(os.getcwd(), "cache")
        for file in os.listdir(folder_path):
            if file.endswith(".docx") or file.endswith(".pdf") or file.endswith(".txt"):
                os.remove(file)
            

    def warning_message(self, message):
        """  """
        self.clear_console()
        print(message, "\n")
        input("Press Enter to continue...")
        self.clear_console()


    def clear_console(self):    
        os.system("cls" if os.name == "nt" else "clear")


    def promt_for_language(self):
        lan = inquirer.select(
            message="Remove from",
            choices=["en", "tr", "Cancel"]
        ).execute()

        return lan


    def prompt_for_index_list(self):
        try:
            indexes = inquirer.text(message="Index or indexes:").execute()
            indexes = indexes.replace(" ", "").split(",")
            indexes = [int(index) for index in indexes]
            indexes.reverse()
        except:
            self.warning_message("incorrect input for index")
            return None

        return indexes


    def prompt_for_index(self):
        try:
            index = inquirer.text(message="Index:").execute()
            index = int(index)
        except:
            self.warning_message("incorrect input for index")
            return None

        return index


    def prompt_for_text(self):
        try:
            text = inquirer.text(message="Text:").execute()
        except:
            self.warning_message("incorrect input for text")
            return None

        return text


    def edit_text_with_editor(self, initial_text=""):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w+', encoding='utf-8') as tf:
            tf.write(initial_text)
            tf.flush()
            temp_filename = tf.name

        # Determine which editor to use
        editor = os.environ.get('EDITOR', 'nano' if os.name != 'nt' else 'notepad')

        # Open the editor
        subprocess.call([editor, temp_filename])

        # Read the edited content
        with open(temp_filename, 'r', encoding='utf-8') as tf:
            edited_text = tf.read()

        # Clean up temp file
        os.unlink(temp_filename)

        return edited_text


    def create_doc(self):
        """  """
        pass


