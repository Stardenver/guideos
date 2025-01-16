import tkinter as tk
from tkinter import filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageDraw, ImageFont
import os

watermark_image_path = None  # Variable to store the watermark image path

def apply_text_watermark(image_path, watermark_text, font_size):
    if not os.path.isfile(image_path):
        print(f"File not found: {image_path}")
        return

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                print("Font not found. Using default font.")
                font = ImageFont.load_default()
            textwidth, textheight = draw.textsize(watermark_text, font)

            # Position the text at the bottom right
            x = width - textwidth - 10
            y = height - textheight - 10

            # Draw the text with a semi-transparent fill
            draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
            output_path = os.path.join(os.path.dirname(image_path), "watermarked_" + os.path.basename(image_path))
            image.save(output_path)
            print(f"Watermarked image saved as: {output_path}")
    except Exception as e:
        print(f"Error applying watermark: {e}")

def apply_image_watermark(image_path, watermark_image_path, scale_factor):
    if not os.path.isfile(image_path):
        print(f"File not found: {image_path}")
        return
    if not os.path.isfile(watermark_image_path):
        print(f"Watermark image not found: {watermark_image_path}")
        return

    try:
        with Image.open(image_path) as image:
            with Image.open(watermark_image_path) as watermark:
                width, height = image.size
                watermark_width, watermark_height = watermark.size

                # Scale the watermark
                scale = scale_factor / 100.0
                watermark = watermark.resize((int(watermark_width * scale), int(watermark_height * scale)), Image.ANTIALIAS)
                watermark_width, watermark_height = watermark.size

                # Position the watermark at the bottom right
                x = width - watermark_width - 10
                y = height - watermark_height - 10

                # Apply the watermark
                image.paste(watermark, (x, y), watermark)
                output_path = os.path.join(os.path.dirname(image_path), "watermarked_" + os.path.basename(image_path))
                image.save(output_path)
                print(f"Watermarked image saved as: {output_path}")
    except Exception as e:
        print(f"Error applying watermark: {e}")

def on_drop(event):
    global watermark_image_path
    file_path = event.data.strip('{}')
    print(f"File dropped: {file_path}")
    if watermark_type.get() == "Text":
        watermark_text = watermark_entry.get()
        try:
            font_size = int(font_size_spinbox.get())
        except ValueError:
            print("Invalid font size. Using default size 36.")
            font_size = 36
        apply_text_watermark(file_path, watermark_text, font_size)
    else:
        if not watermark_image_path:
            watermark_image_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if watermark_image_path:
            try:
                scale_factor = int(scale_factor_spinbox.get())
            except ValueError:
                print("Invalid scale factor. Using default scale 100.")
                scale_factor = 100
            apply_image_watermark(file_path, watermark_image_path, scale_factor)

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

# Create an option to select watermark type
watermark_type = tk.StringVar(value="Text")
text_radio = tk.Radiobutton(root, text="Text Watermark", variable=watermark_type, value="Text")
text_radio.pack()
image_radio = tk.Radiobutton(root, text="Image Watermark", variable=watermark_type, value="Image")
image_radio.pack()

# Create an entry for the watermark text
watermark_entry = tk.Entry(root)
watermark_entry.pack(pady=10)
watermark_entry.insert(0, "Watermark")

# Create a spinbox for the font size
font_size_spinbox = ttk.Spinbox(root, from_=10, to=100, increment=1)
font_size_spinbox.pack(pady=10)
font_size_spinbox.set(36)

# Create a spinbox for the scale factor
scale_factor_spinbox = ttk.Spinbox(root, from_=10, to=200, increment=10)
scale_factor_spinbox.pack(pady=10)
scale_factor_spinbox.set(100)

root.mainloop()