import fitz
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import io

# ===============================
# IMAGE WATERMARK (NO STRETCH)
# ===============================
def apply_watermark(base_img, wm_img, opacity, scale_ratio=0.6):
    wm = wm_img.copy().convert("RGBA")

    # ---- jaga rasio ----
    target_w = int(base_img.width * scale_ratio)
    scale = target_w / wm.width
    new_size = (int(wm.width * scale), int(wm.height * scale))
    wm = wm.resize(new_size, Image.LANCZOS)

    # ---- opacity ----
    alpha = wm.split()[3].point(lambda p: int(p * opacity / 255))
    wm.putalpha(alpha)

    # ---- posisi tengah ----
    x = (base_img.width - wm.width) // 2
    y = (base_img.height - wm.height) // 2

    layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    layer.paste(wm, (x, y), wm)

    return Image.alpha_composite(base_img, layer)


# ===============================
# CORE PROCESS
# ===============================
def process_pdf(input_pdf, output_pdf, wm_path, dpi, op_under, op_over):
    src = fitz.open(input_pdf)
    dst = fitz.open()

    wm_img = Image.open(wm_path).convert("RGBA")
    zoom = dpi / 72

    for page in src:
        rect = page.rect

        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        base_img = Image.frombytes(
            "RGB", (pix.width, pix.height), pix.samples
        ).convert("RGBA")

        # UNDER
        base_img = apply_watermark(base_img, wm_img, op_under)

        # OVER
        base_img = apply_watermark(base_img, wm_img, op_over)

        buf = io.BytesIO()
        base_img.convert("RGB").save(buf, format="PNG")
        buf.seek(0)

        new_page = dst.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(new_page.rect, stream=buf.read())

    dst.save(output_pdf)
    src.close()
    dst.close()


# ===============================
# GUI
# ===============================
class App:
    def __init__(self, root):
        self.root = root
        root.title("PDF Image Watermark (OVER + UNDER)")

        self.pdf_path = None
        self.wm_path = None
        self.preview_img = None

        main = tk.Frame(root)
        main.pack(fill="both", expand=True)

        self.preview = tk.Label(main, bg="#ddd")
        self.preview.pack(side="left", padx=10, pady=10)

        panel = tk.Frame(main)
        panel.pack(side="right", fill="y", padx=10)

        tk.Button(panel, text="Pilih PDF", command=self.load_pdf).pack(fill="x")
        tk.Button(panel, text="Pilih Gambar Watermark", command=self.load_wm).pack(fill="x", pady=5)

        tk.Label(panel, text="UNDER Opacity").pack(anchor="w")
        self.op_under = tk.Scale(panel, from_=20, to=120, orient="horizontal")
        self.op_under.set(60)
        self.op_under.pack(fill="x")

        tk.Label(panel, text="OVER Opacity").pack(anchor="w")
        self.op_over = tk.Scale(panel, from_=80, to=220, orient="horizontal")
        self.op_over.set(140)
        self.op_over.pack(fill="x")

        tk.Label(panel, text="DPI").pack(anchor="w", pady=(10, 0))
        self.dpi = tk.Scale(panel, from_=200, to=350, orient="horizontal")
        self.dpi.set(300)
        self.dpi.pack(fill="x")

        tk.Button(panel, text="PROSES", command=self.run).pack(fill="x", pady=15)

    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return
        self.pdf_path = path
        self.show_preview()

    def load_wm(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if not path:
            return
        self.wm_path = path

    def show_preview(self):
        doc = fitz.open(self.pdf_path)
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img.thumbnail((400, 550))
        self.preview_img = ImageTk.PhotoImage(img)
        self.preview.config(image=self.preview_img)
        doc.close()

    def run(self):
        if not self.pdf_path or not self.wm_path:
            messagebox.showerror("Error", "Pilih PDF & watermark")
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not output:
            return

        process_pdf(
            self.pdf_path,
            output,
            self.wm_path,
            self.dpi.get(),
            self.op_under.get(),
            self.op_over.get()
        )

        messagebox.showinfo("Selesai", "PDF berhasil dibuat")


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
