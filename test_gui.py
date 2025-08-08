import tkinter as tk
root = tk.Tk()
print("Tk 버전:", root.tk.call('info', 'patchlevel'))
root.destroy()