import tkinter as tk
from tkinter import colorchooser
from tkinter import filedialog
from PIL import Image, ImageTk


def choose_color():
    color_code = colorchooser.askcolor(title="Choose color")
    color_label.config(text=f"Chosen color: {color_code[1]}")
    color_label.config(bg=color_code[1])


def load_image():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
    )
    if file_path:
        img = Image.open(file_path)
        img = img.resize(
            (300, 300), Image.ANTIALIAS
        )  # Resize image to fit in the label
        img = ImageTk.PhotoImage(img)
        image_label.config(image=img)
        image_label.image = img  # Keep a reference to avoid garbage collection


# Create the main window
root = tk.Tk()
root.title("Photo and Color Picker Interface")

# Create and place the widgets
load_button = tk.Button(root, text="Load Image", command=load_image)
load_button.pack(pady=10)

image_label = tk.Label(root)
image_label.pack(pady=10)

color_button = tk.Button(root, text="Choose Color", command=choose_color)
color_button.pack(pady=10)

color_label = tk.Label(root, text="Chosen color: None", bg="white")
color_label.pack(pady=10)

input_label = tk.Label(root, text="Enter text:")
input_label.pack(pady=10)

input_box = tk.Entry(root)
input_box.pack(pady=10)

# Start the main event loop
root.mainloop()
