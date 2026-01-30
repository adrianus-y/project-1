from youtube_comment_downloader import YoutubeCommentDownloader
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import json
import threading

def download_comments():
    def run_download():
        try:
            video_url = entry_url.get()
            output_format = format_var.get()

            if not video_url:
                messagebox.showerror("Error", "Please enter a YouTube video URL.")
                return
            if output_format not in ('csv', 'json', 'xlsx'):
                messagebox.showerror("Error", "Please select output format (CSV, JSON, or XLSX).")
                return

            downloader = YoutubeCommentDownloader()
            generator = downloader.get_comments_from_url(video_url)

            comments = []
            count = 0
            for comment in generator:
                comments.append(comment)
                count += 1
                status_label.config(text=f"Downloading comments: {count}")
                status_label.update_idletasks()

            if not comments:
                messagebox.showinfo("Info", "No comments found.")
                return

            # Set filetypes and default extension based on selected format
            if output_format == 'csv':
                filetypes = [("CSV Files", "*.csv")]
                default_extension = ".csv"
            elif output_format == 'json':
                filetypes = [("JSON Files", "*.json")]
                default_extension = ".json"
            elif output_format == 'xlsx':
                filetypes = [("Excel Files", "*.xlsx")]
                default_extension = ".xlsx"

            # Choose file save location
            save_path = filedialog.asksaveasfilename(defaultextension=default_extension, filetypes=filetypes)

            if save_path:
                if output_format == 'csv':
                    df = pd.DataFrame(comments)
                    df.to_csv(save_path, index=False, encoding='utf-8-sig')
                elif output_format == 'json':
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(comments, f, ensure_ascii=False, indent=4)
                elif output_format == 'xlsx':
                    df = pd.DataFrame(comments)
                    df.to_excel(save_path, index=False)

                messagebox.showinfo("Success", f"Comments saved to:\n{save_path}")
                status_label.config(text=f"Finished downloading {count} comments.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            status_label.config(text="Download failed.")

    # Run download in a separate thread
    threading.Thread(target=run_download, daemon=True).start()

def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

# GUI setup
app = tk.Tk()
app.title("YouTube Comment Downloader")
app.geometry("500x300")

frame_input = tk.Frame(app)
frame_input.pack(pady=10)

label_url = tk.Label(frame_input, text="Enter YouTube URL:")
label_url.grid(row=0, column=0, padx=5, pady=5)

entry_url = tk.Entry(frame_input, width=50)
entry_url.grid(row=0, column=1, padx=5, pady=5)
entry_url.bind("<Button-3>", show_context_menu)

frame_format = tk.LabelFrame(app, text="Select Output Format")
frame_format.pack(pady=10)

format_var = tk.StringVar(value="csv")

radio_csv = tk.Radiobutton(frame_format, text="CSV", variable=format_var, value="csv")
radio_json = tk.Radiobutton(frame_format, text="JSON", variable=format_var, value="json")
radio_xlsx = tk.Radiobutton(frame_format, text="XLSX", variable=format_var, value="xlsx")

radio_csv.pack(side="left", padx=10, pady=10)
radio_json.pack(side="left", padx=10, pady=10)
radio_xlsx.pack(side="left", padx=10, pady=10)

frame_button = tk.Frame(app)
frame_button.pack(pady=10)

btn_download = tk.Button(frame_button, text="Download Comments", command=download_comments)
btn_download.pack()

status_label = tk.Label(app, text="", font=("Arial", 10))
status_label.pack(pady=10)

# Context menu
context_menu = tk.Menu(app, tearoff=0)
context_menu.add_command(label="Copy", command=lambda: app.clipboard_append(entry_url.get()))
context_menu.add_command(label="Paste", command=lambda: entry_url.insert(0, app.clipboard_get()))
context_menu.add_command(label="Cut", command=lambda: (app.clipboard_append(entry_url.get()), entry_url.delete(0, tk.END)))

app.mainloop()
