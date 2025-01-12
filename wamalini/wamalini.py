import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageDraw, ImageFont

def apply_watermark(image_path, watermark_text):
    with Image.open(image_path) as image:
        width, height = image.size
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 36)
        textwidth, textheight = draw.textsize(watermark_text, font)

        # Position the text at the bottom right
        x = width - textwidth - 10
        y = height - textheight - 10

        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
        image.save("watermarked_" + image_path.split("/")[-1])

def on_drop(event):
    file_path = event.data
    apply_watermark(file_path, "Watermark")

root = TkinterDnD.Tk()
root.title("Drag & Drop Watermark")

# Create a frame for the drag and drop area
frame = tk.Frame(root, width=300, height=200, bg="lightgray")
frame.pack_propagate(False)
frame.pack()

# Bind the drop event
frame.drop_target_register(DND_FILES)
frame.dnd_bind('<<Drop>>', on_drop)

label = tk.Label(frame, text="Drag and drop an image file here", bg="lightgray")
label.pack(expand=True)

root.mainloop()