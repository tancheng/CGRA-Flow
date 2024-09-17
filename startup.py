import os
import tkinter

import customtkinter
from PIL import Image

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")

master = customtkinter.CTk()

def launchUI(theme_radio_var):
    print(f'Get theme radio var: {theme_radio_var.get()}')
    if theme_radio_var.get() == 1:
        print('Activate light mode.')
        os.system("./launchUI.bash light &")
    elif theme_radio_var.get() == 2:
        print('Activate classic mode.')
        os.system("./launchUI.bash classic &")
    else:
        print('Activate dark mode.')
        os.system("./launchUI.bash &")
    master.destroy()

# configure window
master.title("Startup theme selector")
master.geometry(f"{1078}x{580}")
master.resizable(False, False)

main_frame = customtkinter.CTkFrame(master)
main_frame.grid(row=0, column=0, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_rowconfigure(1, weight=3)
main_frame.grid_columnconfigure(0, weight=1)

radiobutton_frame = customtkinter.CTkFrame(main_frame)
radiobutton_frame.grid(row=0, column=0, sticky="nsew")

radiobutton_frame.grid_rowconfigure(0, weight=1)
radiobutton_frame.grid_rowconfigure(1, weight=2)
radiobutton_frame.grid_columnconfigure(0, weight=1)
radiobutton_frame.grid_columnconfigure(1, weight=1)
radiobutton_frame.grid_columnconfigure(2, weight=1)

theme_radio_var = tkinter.IntVar(value=0)

main_frame_label = customtkinter.CTkLabel(radiobutton_frame, text='Please choose the theme mode: ', font=customtkinter.CTkFont(size=15, weight="bold"))
main_frame_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 10), sticky="w")
launch_button = customtkinter.CTkButton(master=radiobutton_frame, text='LaunchUI', command=lambda: launchUI(theme_radio_var))
launch_button.grid(row=0, column=1, pady=(10, 10), sticky="w")

# create radiobutton frame
light_theme_button = customtkinter.CTkRadioButton(master=radiobutton_frame, text='Light', variable=theme_radio_var, value=1)
light_theme_button.grid(row=1, column=0, pady=(10, 30), padx=(10,0), sticky="w")
dark_theme_button = customtkinter.CTkRadioButton(master=radiobutton_frame, text='Dark', variable=theme_radio_var, value=0)
dark_theme_button.grid(row=1, column=1, pady=(10, 30), padx=(10,0), sticky="w")
classic_theme_button = customtkinter.CTkRadioButton(master=radiobutton_frame, text='Classic', variable=theme_radio_var, value=2)
classic_theme_button.grid(row=1, column=2, pady=(10, 30), padx=(10,0), sticky="w")

image_path = './'
theme_selector_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "theme_selector.png")), size=(1078, 450))
theme_selector_image_label = customtkinter.CTkLabel(main_frame, text="", image=theme_selector_image)
theme_selector_image_label.grid(row=1, column=0)

master.mainloop()


