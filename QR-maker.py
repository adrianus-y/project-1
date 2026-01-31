import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import qrcode
from datetime import datetime
from PIL import Image, ImageTk

# ===================== GLOBAL =====================
qr_image = None
qr_photo = None

# ===================== CONTEXT MENU =====================
def create_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Select All", command=lambda: widget.event_generate("<<SelectAll>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)
    widget.bind("<Control-Button-1>", show_menu)

# ===================== BUILD QR DATA =====================
def build_qr_data():
    qr_type = qr_choice.get()
    if qr_type == "Link":
        data = link_entry.get().strip()
        if not data:
            raise ValueError("Link tidak boleh kosong")
        return data
    elif qr_type == "Kontak":
        name = name_entry.get().strip()
        wa = wa_entry.get().strip()
        if not name:
            raise ValueError("Nama kontak wajib diisi")
        if wa and not wa.startswith("62"):
            raise ValueError("No WhatsApp harus diawali 62")
        address = address_text.get("1.0", "end").strip()
        vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{name}
FN:{name}
"""
        if wa:
            vcard += f"TEL:+{wa}\nURL:https://wa.me/{wa}\n"
        if email_entry.get():
            vcard += f"EMAIL:{email_entry.get()}\n"
        if address:
            vcard += f"ADR:;;{address};;;;\n"
        if maps_entry.get():
            vcard += f"URL:{maps_entry.get()}\n"
        vcard += "END:VCARD"
        return vcard
    elif qr_type == "Event":
        title = event_title_entry.get().strip()
        if not title:
            raise ValueError("Judul Event wajib diisi")

        # Mulai
        try:
            if all([start_year_entry.get(), start_month.get(), start_day.get(),
                    start_hour.get(), start_minute.get()]):
                start = datetime(
                    int(start_year_entry.get()),
                    int(start_month.get()),
                    int(start_day.get()),
                    int(start_hour.get()),
                    int(start_minute.get())
                )
            else:
                start = None
        except:
            raise ValueError("Format tanggal mulai salah")

        # Selesai
        try:
            if all([end_year_entry.get(), end_month.get(), end_day.get(),
                    end_hour.get(), end_minute.get()]):
                end = datetime(
                    int(end_year_entry.get()),
                    int(end_month.get()),
                    int(end_day.get()),
                    int(end_hour.get()),
                    int(end_minute.get())
                )
            else:
                end = None
        except:
            raise ValueError("Format tanggal selesai salah")

        loc = location_entry.get().strip()
        desc = desc_text.get("1.0", "end").strip()

        # Build vCalendar
        event_text = "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\n"
        event_text += f"SUMMARY:{title}\n"
        if start:
            event_text += f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}\n"
        if end:
            event_text += f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}\n"
        if loc:
            event_text += f"LOCATION:{loc}\n"
        if desc:
            event_text += f"DESCRIPTION:{desc}\n"
        event_text += "END:VEVENT\nEND:VCALENDAR"
        return event_text

# ===================== QR WITH SAFE LOGO =====================
def make_qr_safe_logo(data, logo_path=None, qr_size=500, logo_ratio=0.2):
    qr_size = min(qr_size, 1500)
    logo_ratio = min(max(logo_ratio, 0.05), 0.25)  # logo max 25%
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((qr_size, qr_size))

    if logo_path:
        logo = Image.open(logo_path)
        if logo.mode != "RGBA":
            logo = logo.convert("RGBA")

        # Buat space lebih besar dari logo untuk keamanan scan
        safe_ratio = logo_ratio * 1.2
        safe_size = int(qr_size * safe_ratio)
        x0 = (qr_size - safe_size) // 2
        y0 = (qr_size - safe_size) // 2
        x1 = x0 + safe_size
        y1 = y0 + safe_size

        for x in range(x0, x1):
            for y in range(y0, y1):
                qr_img.putpixel((x, y), (255, 255, 255))

        # Resize logo agar pas di safe space
        logo_size = int(qr_size * logo_ratio)
        logo.thumbnail((logo_size, logo_size))
        x_logo = (qr_size - logo.size[0]) // 2
        y_logo = (qr_size - logo.size[1]) // 2
        qr_img.paste(logo, (x_logo, y_logo), mask=logo)

    return qr_img



# ===================== PREVIEW =====================
def preview_qr():
    global qr_image, qr_photo
    try:
        data = build_qr_data()
        qr_size_val = int(qr_size_entry.get() or 500)
        logo_ratio_val = float(logo_size_entry.get() or 0.2)
        qr_image = make_qr_safe_logo(data, logo_path_var.get(), qr_size=qr_size_val, logo_ratio=logo_ratio_val)
        preview = qr_image.resize((260, 260))
        qr_photo = ImageTk.PhotoImage(preview)
        qr_label.config(image=qr_photo, text="")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ===================== SAVE AS =====================
def save_as_qr():
    global qr_image
    if qr_image is None:
        messagebox.showwarning("Peringatan", "Klik Preview terlebih dahulu")
        return
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG Image", "*.png"), ("JPG Image", "*.jpg")],
        title="Save QR Code As"
    )
    if not file_path:
        return
    try:
        qr_image.save(file_path)
        messagebox.showinfo("Sukses", f"QR berhasil disimpan:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ===================== SWITCH FRAME =====================
def show_frame(event=None):
    for frame in frames.values():
        frame.grid_forget()
    frames[qr_choice.get()].grid(sticky="nsew", padx=10, pady=10)

# ===================== GUI =====================
root = tk.Tk()
root.title("QR Generator All-in-One")
root.geometry("1000x700")
root.columnconfigure(0, weight=3)
root.columnconfigure(1, weight=2)
root.rowconfigure(4, weight=1)

logo_path_var = tk.StringVar()

tk.Label(root, text="QR Generator", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

qr_choice = tk.StringVar(value="Link")
dropdown = ttk.Combobox(root, values=["Link", "Kontak", "Event"],
                        textvariable=qr_choice, state="readonly", width=20)
dropdown.grid(row=1, column=0, sticky="w", padx=10)
dropdown.bind("<<ComboboxSelected>>", show_frame)

# LOGO & QR SETTINGS
tk.Label(root, text="Logo (opsional)").grid(row=1, column=1, sticky="w", padx=10)
logo_entry = tk.Entry(root, textvariable=logo_path_var, width=40)
logo_entry.grid(row=1, column=1, sticky="w", padx=100)
create_context_menu(logo_entry)

def browse_logo():
    path = filedialog.askopenfilename(
        title="Pilih Logo",
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if path:
        logo_path_var.set(path)

tk.Button(root, text="Browse Logo", command=browse_logo).grid(row=1, column=2, padx=5)

# QR Size
tk.Label(root, text="Resolusi QR (px)").grid(row=2, column=1, sticky="w", padx=10)
qr_size_entry = tk.Entry(root, width=10)
qr_size_entry.insert(0, "500")
qr_size_entry.grid(row=2, column=1, sticky="w", padx=130)

# Logo size ratio
tk.Label(root, text="Ukuran Logo (0-1)").grid(row=3, column=1, sticky="w", padx=10)
logo_size_entry = tk.Entry(root, width=10)
logo_size_entry.insert(0, "0.2")
logo_size_entry.grid(row=3, column=1, sticky="w", padx=130)


# ===================== FORM CONTAINER =====================
container = tk.Frame(root)
container.grid(row=4, column=0, sticky="nsew")
frames = {}

# ----- LINK -----
frames["Link"] = tk.Frame(container)
frames["Link"].columnconfigure(1, weight=1)
tk.Label(frames["Link"], text="URL").grid(row=0, column=0, sticky="w", padx=5)
link_entry = tk.Entry(frames["Link"], width=80)
link_entry.grid(row=0, column=1, sticky="ew", padx=5)
create_context_menu(link_entry)

# ----- KONTAK -----
frames["Kontak"] = tk.Frame(container)
frames["Kontak"].columnconfigure(1, weight=1)
def add_row(frame, text, row):
    tk.Label(frame, text=text).grid(row=row, column=0, sticky="w", padx=5)

add_row(frames["Kontak"], "Nama", 0)
name_entry = tk.Entry(frames["Kontak"])
name_entry.grid(row=0, column=1, sticky="ew", padx=5)
create_context_menu(name_entry)

add_row(frames["Kontak"], "No WhatsApp (62xxxx)", 1)
wa_entry = tk.Entry(frames["Kontak"])
wa_entry.grid(row=1, column=1, sticky="ew", padx=5)
create_context_menu(wa_entry)

add_row(frames["Kontak"], "Email", 2)
email_entry = tk.Entry(frames["Kontak"])
email_entry.grid(row=2, column=1, sticky="ew", padx=5)
create_context_menu(email_entry)

add_row(frames["Kontak"], "Alamat", 3)
address_text = tk.Text(frames["Kontak"], height=3)
address_text.grid(row=3, column=1, sticky="ew", padx=5)
create_context_menu(address_text)

add_row(frames["Kontak"], "Link Google Maps", 4)
maps_entry = tk.Entry(frames["Kontak"])
maps_entry.grid(row=4, column=1, sticky="ew", padx=5)
create_context_menu(maps_entry)

# ----- EVENT -----
frames["Event"] = tk.Frame(container)
frames["Event"].columnconfigure(1, weight=1)
days = [str(d) for d in range(1, 32)]
months = [str(m) for m in range(1, 13)]
hours = [str(h).zfill(2) for h in range(0, 24)]
minutes = [str(m).zfill(2) for m in range(0, 60)]

# Judul Event
add_row(frames["Event"], "Judul Event", 0)
event_title_entry = tk.Entry(frames["Event"])
event_title_entry.grid(row=0, column=1, sticky="ew", padx=5)

# Mulai
add_row(frames["Event"], "Mulai", 1)
start_frame = tk.Frame(frames["Event"])
start_frame.grid(row=1, column=1, sticky="w", pady=2)
tk.Label(start_frame, text="Tanggal").grid(row=0, column=0)
tk.Label(start_frame, text="Bulan").grid(row=0, column=1)
tk.Label(start_frame, text="Jam").grid(row=0, column=2)
tk.Label(start_frame, text="Menit").grid(row=0, column=3)
tk.Label(start_frame, text="Tahun").grid(row=0, column=4)
start_day = ttk.Combobox(start_frame, values=days, width=3)
start_day.grid(row=1, column=0, padx=2)
start_month = ttk.Combobox(start_frame, values=months, width=3)
start_month.grid(row=1, column=1, padx=2)
start_hour = ttk.Combobox(start_frame, values=hours, width=3)
start_hour.grid(row=1, column=2, padx=2)
start_minute = ttk.Combobox(start_frame, values=minutes, width=3)
start_minute.grid(row=1, column=3, padx=2)
start_year_entry = tk.Entry(start_frame, width=5)
start_year_entry.grid(row=1, column=4, padx=2)

# Selesai
add_row(frames["Event"], "Selesai", 2)
end_frame = tk.Frame(frames["Event"])
end_frame.grid(row=2, column=1, sticky="w", pady=2)
tk.Label(end_frame, text="Tanggal").grid(row=0, column=0)
tk.Label(end_frame, text="Bulan").grid(row=0, column=1)
tk.Label(end_frame, text="Jam").grid(row=0, column=2)
tk.Label(end_frame, text="Menit").grid(row=0, column=3)
tk.Label(end_frame, text="Tahun").grid(row=0, column=4)
end_day = ttk.Combobox(end_frame, values=days, width=3)
end_day.grid(row=1, column=0, padx=2)
end_month = ttk.Combobox(end_frame, values=months, width=3)
end_month.grid(row=1, column=1, padx=2)
end_hour = ttk.Combobox(end_frame, values=hours, width=3)
end_hour.grid(row=1, column=2, padx=2)
end_minute = ttk.Combobox(end_frame, values=minutes, width=3)
end_minute.grid(row=1, column=3, padx=2)
end_year_entry = tk.Entry(end_frame, width=5)
end_year_entry.grid(row=1, column=4, padx=2)

# Lokasi opsional
add_row(frames["Event"], "Lokasi", 3)
location_entry = tk.Entry(frames["Event"])
location_entry.grid(row=3, column=1, sticky="ew", padx=5)

# Deskripsi opsional
add_row(frames["Event"], "Deskripsi", 4)
desc_text = tk.Text(frames["Event"], height=4)
desc_text.grid(row=4, column=1, sticky="ew", padx=5)

# ===================== PREVIEW PANEL =====================
preview_frame = tk.Frame(root, bd=2, relief="groove")
preview_frame.grid(row=4, column=1, sticky="nsew", padx=10, pady=10)
tk.Label(preview_frame, text="Preview QR", font=("Arial", 12, "bold")).pack(pady=10)
qr_label = tk.Label(preview_frame, text="Belum ada preview", fg="gray")
qr_label.pack(expand=True)

# ===================== BUTTONS =====================
btn_frame = tk.Frame(root)
btn_frame.grid(row=6, column=0, columnspan=2, pady=15)
tk.Button(btn_frame, text="Preview", command=preview_qr, width=15,
          bg="#455A64", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=10)
tk.Button(btn_frame, text="Save As...", command=save_as_qr, width=15,
          bg="#1976D2", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=10)

# ===================== INIT =====================
show_frame()
root.mainloop()
