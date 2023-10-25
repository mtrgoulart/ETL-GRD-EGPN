import customtkinter as ctk
import tkinter as tk
import sys
import threading

from src.director import Director,DM
from src.transformations import get_path_name
import turtle


class TextboxRedirector:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, message):
        self.textbox.insert('end', message)
        self.textbox.see('end')  # Scroll to the end of the textbox


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Processor GRD-EGPN")
        #setting window size
        self.geometry(f"{500}x{400}")
        self.folder_path=""
        self.processing_thread = None
        self.resizable(False,False)
        self.process_files_executed=False
        self.move_files_executed=False
        self.selected_folder=False

        #Define apperance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # configure grid layout (3x2)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=50, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=f'GRD-EGPN Processor \nv0.3', font=ctk.CTkFont(size=14, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=10, pady=(20, 10))
        self.signature=ctk.CTkLabel(self,text='by: Goulart, M',font=ctk.CTkFont(size=10, weight="bold"))
        self.signature.grid(row=3,column=0, padx=10, pady=(20, 10))

        self.loading_frame=ctk.CTkFrame(self,width=50, corner_radius=0,bg_color="transparent")
        self.loading_frame.grid(row=2,column=0)

        self.loading_canvas=tk.Canvas(self.loading_frame,width=50, height=50,highlightthickness=0)
        self.loading_canvas.config(bg='#212121')
        self.loading_canvas.grid(row=0,column=0)

        self.select_folder_button = ctk.CTkButton(self.sidebar_frame,text='Select files',command=self.select_and_set_folder_path)
        self.select_folder_button.grid(row=1, column=0, padx=10, pady=10)
        self.process_files_button = ctk.CTkButton(self.sidebar_frame, text='Process files',command=self.process_files)
        self.process_files_button.grid(row=2, column=0, padx=10, pady=10)
        self.process_files_button.configure(state="disabled")
        self.move_files_button = ctk.CTkButton(self.sidebar_frame,text='Move files',command=self.move_files)
        self.move_files_button.grid(row=3, column=0, padx=10, pady=10)
        self.move_files_button.configure(state="disabled")

        self.terminal_frame=ctk.CTkFrame(self,width=350,height=400,corner_radius=5)
        self.terminal_frame.grid(row=0,rowspan=4,column=1,sticky="nsew")
        self.terminal = ctk.CTkTextbox(self.terminal_frame,height=350,width=300,scrollbar_button_color="#3DA1C8",activate_scrollbars="gray")
        self.terminal.grid(padx=10,pady=(10,0))

        self.clear_button = ctk.CTkButton(self.terminal_frame, text='Clear', command=self.clear_terminal)
        self.clear_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    
        self.textbox_redirector = TextboxRedirector(self.terminal)
        sys.stdout = self.textbox_redirector


    def select_and_set_folder_path(self):
        if self.process_files_executed:
            DM.destroy_builders()
        self.director=Director()
        self.director.folder_path()
        self.folder_path=self.director.Folder_path
        folder_path_name=get_path_name(self.folder_path)
        self.terminal.insert('end',f'Selected Folder: {folder_path_name}')
        self.process_files_button.configure(state="normal")
        self.selected_folder=True
    
    def clear_terminal(self):
        self.terminal.delete(1.0, 'end')  # Clear the terminal content

    def execute_with_thread(self, function):
        if self.processing_thread and self.processing_thread.is_alive():
            self.terminal.insert('end', "Another process is already running...\n")
            return

        self.processing_thread = threading.Thread(target=self._execute_function, args=(function,))
        self.processing_thread.start()

    def _execute_function(self, function):
        try:
            function()
        except Exception as e:
            error_message = f"\nAn error occurred: {str(e)}.\n Please contact the support (as know as Goulart)\n"
            self.update_terminal(error_message)
            self.hide_loading_animation()
            threading.Thread(target=self._show_error_window, args=(error_message,)).start()

    def _show_error_window(self,error_message):
        error_window=ErrorWindow()
        error_window.raise_error(error_message)
        error_window.lift()
        error_window.attributes("-topmost",True)

    def process_files(self):
        self.show_loading_animation()
        self.execute_with_thread(self._process_files)
        

    def move_files(self):
        self.show_loading_animation()
        self.execute_with_thread(self._move_files)
        

    def _process_files(self):
        if self.process_files_executed:
            self.select_and_set_folder_path()
        self.director.GRD_EGPN_Validation()
        self.update_terminal("Processing files completed.\n")
        self.move_files_button.configure(state="normal")
        self.selected_folder=False
        self.process_files_executed=True
        self.hide_loading_animation()

    def _move_files(self):
        self.director.execute_movimentation()
        self.update_terminal("Moving files completed.\n")
        self.move_files_button.configure(state="disabled")
        self.process_files_button.configure(state="disabled")
        self.move_files_executed=True
        self.hide_loading_animation()
        self.director.remove_temp_files()

    def update_terminal(self, message):
        self.terminal.insert('end', message)
        self.terminal.see('end')

    def show_loading_animation(self):
        self.pause_loading_animation=False
        self.loading_canvas.delete("all")
        self.animate_loading(0)

    def animate_loading(self, angle):
        if not self.pause_loading_animation:
            if angle <= 360:
                self.loading_canvas.delete("all")
                self.loading_canvas.create_arc(5, 5, 45, 45, start=90, extent=-angle, outline='#c7c7c7', width=3)
                self.after(10, self.animate_loading, angle + 5)
            else:
                self.animate_loading(0)

    def hide_loading_animation(self):
        self.pause_loading_animation=True
        self.loading_canvas.delete("all")

class ErrorWindow(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.geometry("300x150")
        self.title("Error")

    def raise_error(self,error_message):      
        error_label = ctk.CTkLabel(self, text=error_message, padx=20, pady=20,font=("TkDefaultFont",16),wraplength=300)
        error_label.pack(expand=False, fill='both')