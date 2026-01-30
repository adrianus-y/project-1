import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json, base64
import qrcode
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime, timezone, timedelta

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature

# ================= ROOT & VAR ================= #
root = tk.Tk()
root.title("QR Signature - Verification")
root.geometry("1250x800")

logo_mode = tk.IntVar(value=1)
logo_path = tk.StringVar()
logo_opacity = tk.IntVar(value=255)
privkey_path = tk.StringVar()
pubkey_path = tk.StringVar()

qr_color = "#000000"
bg_color = "#FFFFFF"

qr_image = None
qr_preview = None

add_timestamp = tk.IntVar(value=0)
tz_var = tk.StringVar(value="UTC")
add_expiration = tk.IntVar(value=0)

# ================= RIGHT CLICK ================= #
def add_right_click_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Select All", command=lambda: widget.tag_add("sel", "1.0", "end"))
    widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

# ================= LOGO =================
def add_logo_safe(qr_img):
    qr_img = qr_img.convert("RGBA")
    w, h = qr_img.size

    if logo_mode.get() == 1 or not logo_path.get():
        return qr_img.convert("RGB")

    logo = Image.open(logo_path.get()).convert("RGBA")
    size = int(w * 0.20)
    logo = logo.resize((size, size), Image.LANCZOS)

    alpha = logo.split()[3].point(lambda _: logo_opacity.get())
    logo.putalpha(alpha)

    if logo_mode.get() == 3:
        safe = int(size * 1.1)
        mask = Image.new("RGBA", qr_img.size, (255,255,255,0))
        draw = ImageDraw.Draw(mask)
        draw.rectangle(
            [(w-safe)//2,(h-safe)//2,(w+safe)//2,(h+safe)//2],
            fill=(255,255,255,255)
        )
        qr_img = Image.alpha_composite(qr_img, mask)

    qr_img.paste(logo, ((w-size)//2,(h-size)//2), logo)
    return qr_img.convert("RGB")

# ================= LOAD KEY =================
def load_private_key():
    p = filedialog.askopenfilename(filetypes=[("PEM File","*.pem")])
    if p: privkey_path.set(p)

def load_public_key():
    p = filedialog.askopenfilename(filetypes=[("PEM File","*.pem")])
    if p: pubkey_path.set(p)

def pick_qr_color():
    global qr_color
    c = colorchooser.askcolor(title="QR COLOUR")[1]
    if c: qr_color = c

# ================= QR GENERATOR =================
def preview_qr():
    global qr_image, qr_preview
    try:
        data = data_text.get("1.0","end").strip()
        if not data: raise ValueError("required")
        if not privkey_path.get(): raise ValueError("Private key is not loaded")

        payload = {"data": data}

        if doc_id_entry.get(): payload["doc_id"] = doc_id_entry.get()
        if created_by_entry.get(): payload["created_by"] = created_by_entry.get()

        tz = timezone.utc
        if tz_var.get()=="WIB": tz=timezone(timedelta(hours=7))
        if tz_var.get()=="WITA": tz=timezone(timedelta(hours=8))
        if tz_var.get()=="WIT": tz=timezone(timedelta(hours=9))

        now = None
        if add_timestamp.get():
            now = datetime.now(tz)
            payload["timestamp"] = now.isoformat()

        if add_expiration.get() and now:
            exp = datetime(
                dt_exp_year.get(),
                dt_exp_month.get(),
                dt_exp_day.get(),
                dt_exp_hour.get(),
                dt_exp_minute.get(),
                tzinfo=tz
            )
            payload["expires_at"] = exp.isoformat()

        sign_bytes = json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()

        with open(privkey_path.get(),"rb") as f:
            priv = serialization.load_pem_private_key(f.read(),password=None)

        payload["signature"] = base64.b64encode(
            priv.sign(sign_bytes, ec.ECDSA(hashes.SHA256()))
        ).decode()

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4
        )
        qr.add_data(json.dumps(payload,ensure_ascii=False))
        qr.make(fit=True)

        qr_image = add_logo_safe(
            qr.make_image(fill_color=qr_color, back_color=bg_color).convert("RGB")
        )

        qr_preview = ImageTk.PhotoImage(qr_image.resize((320,320)))
        qr_label.config(image=qr_preview)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= VERIFY ================= #
def verify_qr():
    try:
        payload = json.loads(verify_text.get("1.0","end"))
        sig = base64.b64decode(payload.pop("signature"))

        verify_bytes = json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()

        with open(pubkey_path.get(),"rb") as f:
            pub = serialization.load_pem_public_key(f.read())

        pub.verify(sig, verify_bytes, ec.ECDSA(hashes.SHA256()))

        text = "✅ VALID\n"
        color = "green"

        if "expires_at" in payload:
            exp = datetime.fromisoformat(payload["expires_at"])
            now = datetime.now(exp.tzinfo)
            if now > exp:
                text += f"⛔ Expires on: {exp}\n"
                color = "red"
            else:
                text += f"⏳ Expires on: {exp}\n"

        verify_result.config(text=text, fg=color)

    except InvalidSignature:
        verify_result.config(text="❌ INVALID", fg="red")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= GUI ================= #
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

tab_qr = ttk.Frame(notebook)
notebook.add(tab_qr, text="✍️ QR Generator")

left = tk.Frame(tab_qr)
left.pack(side="left", fill="both", expand=True, padx=10)

right = tk.Frame(tab_qr)
right.pack(side="right", padx=20)

tk.Label(left,text="Document ID").pack(anchor="w")
doc_id_entry = tk.Entry(left); doc_id_entry.pack(fill="x")

tk.Label(left,text="Signed by").pack(anchor="w")
created_by_entry = tk.Entry(left); created_by_entry.pack(fill="x")

tk.Label(left,text="Data").pack(anchor="w")
data_text = tk.Text(left,height=6); data_text.pack(fill="x")
add_right_click_menu(data_text)

frame_h = tk.LabelFrame(left,text="QR Settings")
frame_h.pack(anchor="w", pady=10, fill="x")

# Private key
tk.Label(frame_h,text="Private Key").grid(row=0,column=0,sticky="w")
tk.Entry(frame_h,textvariable=privkey_path,width=25).grid(row=1,column=0)
tk.Button(frame_h,text="Browse",command=load_private_key).grid(row=1,column=1,padx=5)

# Timestamp
tk.Checkbutton(frame_h,text="Add Timestamp",variable=add_timestamp)\
    .grid(row=0,column=2,sticky="w",padx=10)
ttk.Combobox(frame_h,textvariable=tz_var,
             values=["UTC","WIB","WITA","WIT"],
             state="readonly",width=6)\
    .grid(row=1,column=2,sticky="w",padx=10)

# ================= EXPIRED =================
tk.Checkbutton(frame_h,text="QR Validity Limit Period",variable=add_expiration)\
    .grid(row=2,column=0,sticky="w",pady=(10,0))

dt_exp_day = tk.IntVar(value=1)
dt_exp_month = tk.IntVar(value=1)
dt_exp_year = tk.IntVar(value=datetime.now().year)
dt_exp_hour = tk.IntVar(value=0)
dt_exp_minute = tk.IntVar(value=0)

# Line 1: Date, Month. Year
tk.Label(frame_h,text="Date").grid(row=3,column=0,sticky="w",padx=3)
tk.Label(frame_h,text="Month").grid(row=3,column=1,sticky="w",padx=3)
tk.Label(frame_h,text="Year").grid(row=3,column=2,sticky="w",padx=3)

ttk.Combobox(frame_h,textvariable=dt_exp_day,values=list(range(1,32)),width=4).grid(row=4,column=0,padx=3)
ttk.Combobox(frame_h,textvariable=dt_exp_month,values=list(range(1,13)),width=4).grid(row=4,column=1,padx=3)
tk.Entry(frame_h,textvariable=dt_exp_year,width=6).grid(row=4,column=2,padx=3)

# Line 2: time
tk.Label(frame_h,text="Hour(s)").grid(row=5,column=0,sticky="w",padx=3,pady=(5,0))
tk.Label(frame_h,text="Minute(s)").grid(row=5,column=1,sticky="w",padx=3,pady=(5,0))

ttk.Combobox(frame_h,textvariable=dt_exp_hour,values=list(range(0,24)),width=4).grid(row=6,column=0,padx=3)
ttk.Combobox(frame_h,textvariable=dt_exp_minute,values=list(range(0,60)),width=4).grid(row=6,column=1,padx=3)


# Warna & Logo
tk.Button(frame_h,text="QR Colour",command=pick_qr_color)\
    .grid(row=0,column=3,padx=10)

tk.Radiobutton(frame_h,text="No Logo",variable=logo_mode,value=1)\
    .grid(row=1,column=3,sticky="w")
tk.Radiobutton(frame_h,text="Embedded",variable=logo_mode,value=2)\
    .grid(row=2,column=3,sticky="w")
tk.Radiobutton(frame_h,text="White Space",variable=logo_mode,value=3)\
    .grid(row=3,column=3,sticky="w")

tk.Entry(frame_h,textvariable=logo_path,width=22).grid(row=1,column=4)
tk.Button(frame_h,text="Browse Logo",
          command=lambda: logo_path.set(
              filedialog.askopenfilename(filetypes=[("Image","*.png *.jpg *.jpeg")])
          )).grid(row=2,column=4)

tk.Scale(frame_h,from_=50,to=255,variable=logo_opacity,
         orient="horizontal",label="Logo Opacity")\
    .grid(row=4,column=3,columnspan=2)

tk.Button(left,text="Preview QR",command=preview_qr).pack(pady=5)
tk.Button(left,text="Save QR",command=preview_qr).pack(pady=5)

qr_label = tk.Label(right,relief="sunken",bd=2)
qr_label.pack(pady=20)

# Verifier
tab_v = ttk.Frame(notebook)
notebook.add(tab_v,text="🔍 Verifier")

verify_text = tk.Text(tab_v,height=10)
verify_text.pack(fill="x",padx=10,pady=10)

tk.Entry(tab_v,textvariable=pubkey_path).pack(fill="x",padx=10)
tk.Button(tab_v,text="Browse Public Key",command=load_public_key).pack()

tk.Button(tab_v,text="VERIFY",font=("Arial",12,"bold"),
          bg="#4CAF50",fg="white",command=verify_qr).pack(pady=20)

verify_result = tk.Label(tab_v,font=("Arial",14,"bold"))
verify_result.pack()

root.mainloop()
