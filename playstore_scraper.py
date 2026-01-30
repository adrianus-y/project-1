import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from google_play_scraper import Sort, reviews
import time

# ================= KLIK KANAN =================
def add_right_click_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Select All", command=lambda: widget.select_range(0, 'end'))
    widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
    widget.bind("<Button-2>", lambda e: menu.tk_popup(e.x_root, e.y_root))

# ================= FUNCTIONS =================
def scrape_reviews_progress():
    app_id = app_id_var.get().strip()
    if not app_id:
        messagebox.showerror("Error", "Masukkan App ID!")
        return

    try:
        max_review = int(max_review_var.get())
        if max_review <= 0:
            raise ValueError
    except:
        messagebox.showerror("Error", "Masukkan angka valid untuk maksimal review!")
        return

    save_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV File","*.csv")])
    if not save_path:
        return

    root.update()

    all_reviews = []
    count = 0
    next_pagination_token = None

    # setup progressbar
    progress['maximum'] = max_review
    progress['value'] = 0

    try:
        while count < max_review:
            remaining = max_review - count
            batch_count = min(100, remaining)

            result, next_pagination_token = reviews(
                app_id,
                lang="id",
                country="id",
                sort=Sort.MOST_RELEVANT,
                count=batch_count,
                continuation_token=next_pagination_token
            )

            if not result:
                break

            all_reviews.extend(result)
            count += len(result)

            # update progress bar
            progress['value'] = count
            root.update()
            time.sleep(0.05)

            if not next_pagination_token:
                break

        # simpan CSV
        df = pd.DataFrame(all_reviews)
        df.to_csv(save_path, index=False, header=True)

        # selesai, beri notif
        messagebox.showinfo("Selesai", f"Scraping selesai!\nTotal review: {len(all_reviews)}\nDisimpan di:\n{save_path}")
        progress['value'] = progress['maximum']

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ================= GUI =================
root = tk.Tk()
root.title("Play Store Scraper - Progres")
root.geometry("500x200")

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

# App ID
ttk.Label(frame, text="App ID:").grid(row=0, column=0, sticky="w", pady=5)
app_id_var = tk.StringVar()
app_id_entry = ttk.Entry(frame, textvariable=app_id_var, width=40)
app_id_entry.grid(row=0, column=1, pady=5)
add_right_click_menu(app_id_entry)

# Maksimal review
ttk.Label(frame, text="Maksimal Review:").grid(row=1, column=0, sticky="w", pady=5)
max_review_var = tk.StringVar(value="500")  # default 500
ttk.Entry(frame, textvariable=max_review_var, width=10).grid(row=1, column=1, sticky="w", pady=5)

# Button scrape
ttk.Button(frame, text="Scrape Reviews & Save CSV", command=scrape_reviews_progress)\
    .grid(row=2, column=0, columnspan=2, pady=15)

# Progress bar
progress = ttk.Progressbar(frame, orient='horizontal', length=400, mode='determinate')
progress.grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()
