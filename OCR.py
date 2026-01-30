import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pytesseract
import os

# Path Tesseract Configuration
# ex: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR with Tesseract")
        self.root.geometry("600x500")

        # UI Elements
        self.label_instruksi = tk.Label(root, text="Browse Image", font=("Arial", 12))
        self.label_instruksi.pack(pady=10)

        self.btn_pilih = tk.Button(root, text="Open Image", command=self.pilih_gambar, bg="#4CAF50", fg="white", padx=10)
        self.btn_pilih.pack()

        self.canvas = tk.Label(root) # Preview
        self.canvas.pack(pady=10)

        self.text_result = tk.Text(root, height=10, width=60)
        self.text_result.pack(pady=10)

        self.btn_copy = tk.Button(root, text="Copy Text", command=self.salin_teks)
        self.btn_copy.pack()

    def pilih_gambar(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            # Image Preview (Resize Fit to Display)
            img = Image.open(file_path)
            img.thumbnail((200, 200))
            img_display = ImageTk.PhotoImage(img)
            self.canvas.config(image=img_display)
            self.canvas.image = img_display

            # Run OCR
            self.proses_ocr(file_path)

    def proses_ocr(self, path):
        try:
            # Language en/id
            extracted_text = pytesseract.image_to_string(Image.open(path), lang='ind+eng')
            self.text_result.delete(1.0, tk.END)
            self.text_result.insert(tk.END, extracted_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def salin_teks(self):
        content = self.text_result.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Ok", "Copied to clipboard!")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()