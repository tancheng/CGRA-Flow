import os
import tkinter

import customtkinter
from PIL import Image

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")

master = customtkinter.CTk()
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, "theme")
theme_selector_dark_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "dark_theme.png")), size=(500, 410))
theme_selector_light_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "light_theme.png")), size=(500, 410))
theme_selector_classic_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "classic_theme.png")), size=(500, 410))

def launchUI(theme_radio_var):
    print(f'Get theme radio var: {theme_radio_var.get()}')
    if theme_radio_var.get() == 1:
        print('Activate light mode.')
        os.system("sh ./launchUI.bash light &")
    elif theme_radio_var.get() == 2:
        print('Activate classic mode.')
        os.system("sh ./launchUI.bash classic &")
    else:
        print('Activate dark mode.')
        os.system("sh ./launchUI.bash &")
    master.destroy()


def switchUI(theme_radio_var, radiobutton_frame, launch_button, theme_selector_image_label):
    theme_selector_image_label.forget()
    if theme_radio_var.get() == 1:
        print('light mode.')
        customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("dark-blue")
        radiobutton_frame.configure(fg_color='#D9D9D9')
        launch_button.configure(fg_color='#3A7EBF')
        theme_selector_image_label = customtkinter.CTkLabel(main_frame, text="", image=theme_selector_light_image,
                                                            compound="bottom", anchor="center")
        theme_selector_image_label.grid(row=1, column=0)
    elif theme_radio_var.get() == 2:
        print('classic mode.')
        customtkinter.set_appearance_mode("light")
        # customtkinter.set_default_color_theme("green")
        radiobutton_frame.configure(fg_color='#F0F0F0')
        launch_button.configure(fg_color='#808080')
        theme_selector_image_label = customtkinter.CTkLabel(main_frame, text="", image=theme_selector_classic_image,
                                                            compound="bottom", anchor="center")
        theme_selector_image_label.grid(row=1, column=0)
    else:
        print('dark mode.')
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")
        radiobutton_frame.configure(fg_color='#292929')
        launch_button.configure(fg_color='#1F538D')
        theme_selector_image_label = customtkinter.CTkLabel(main_frame, text="", image=theme_selector_dark_image,
                                                            compound="bottom", anchor="center")
        theme_selector_image_label.grid(row=1, column=0)


# configure window
master.title("Startup theme selector")
master.geometry(f"{500}x{500}")
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
main_frame_label.grid(row=0, column=0, columnspan=2, padx=(10, 5), pady=(10, 10), sticky="w")
launch_button = customtkinter.CTkButton(master=radiobutton_frame, text='LaunchUI', command=lambda: launchUI(theme_radio_var))
launch_button.grid(row=0, column=2, pady=(10, 10), sticky="w")

theme_selector_image_label = customtkinter.CTkLabel(main_frame, text="", image=theme_selector_dark_image, compound="bottom", anchor="center")
theme_selector_image_label.grid(row=1, column=0)

# create radiobutton frame
light_theme_button = customtkinter.CTkRadioButton(master=radiobutton_frame, text='Light', variable=theme_radio_var, value=1, command=lambda: switchUI(theme_radio_var, radiobutton_frame, launch_button, theme_selector_image_label))
light_theme_button.grid(row=1, column=0, pady=(10, 10), padx=(10,0), sticky="w")
dark_theme_button = customtkinter.CTkRadioButton(master=radiobutton_frame, text='Dark', variable=theme_radio_var, value=0, command=lambda: switchUI(theme_radio_var, radiobutton_frame, launch_button, theme_selector_image_label))
dark_theme_button.grid(row=1, column=1, pady=(10, 10), padx=(10,0), sticky="w")
classic_theme_button = customtkinter.CTkRadioButton(master=radiobutton_frame, text='Classic', variable=theme_radio_var, value=2, command=lambda: switchUI(theme_radio_var, radiobutton_frame, launch_button, theme_selector_image_label))
classic_theme_button.grid(row=1, column=2, pady=(10, 10), padx=(10,0), sticky="w")

master.mainloop()


