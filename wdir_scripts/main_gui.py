# main_gui.py
import gui
from tkinter import *

if __name__ == '__main__':
    window = Tk()
    # Calling the App class function
    object1 = gui.App(window)
    window.title("Running the Steps of Multiplex Pipeline")
    window.geometry('880x510')
    window.config(background="black")
    window.mainloop()
