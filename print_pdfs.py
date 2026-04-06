"""
Print all PDF files in the script's directory (two copies each).
Double-click to run on Windows. Uses a simple tkinter GUI.
"""

import os
import sys
import glob
import time
import threading
import tkinter as tk
from tkinter import messagebox


def get_pdf_files():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return sorted(glob.glob(os.path.join(script_dir, "*.pdf")))


def print_pdfs(status_label, print_button):
    print_button.config(state=tk.DISABLED)
    pdf_files = get_pdf_files()

    if not pdf_files:
        status_label.config(text="No PDF files found.")
        print_button.config(state=tk.NORMAL)
        return

    total = len(pdf_files)
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        for copy in range(1, 3):
            status_label.config(text=f"Printing copy {copy}/2 of ({idx}/{total}): {filename}")
            os.startfile(pdf_path, "print")
            time.sleep(3)

    status_label.config(text=f"Done! Sent {total} PDF(s) to printer (2 copies each).")
    print_button.config(state=tk.NORMAL)


def start_printing(status_label, print_button):
    thread = threading.Thread(target=print_pdfs, args=(status_label, print_button), daemon=True)
    thread.start()


def main():
    pdf_files = get_pdf_files()

    root = tk.Tk()
    root.title("PDF Printer")
    root.geometry("450x200")
    root.resizable(False, False)

    tk.Label(root, text="PDF Printer (2 copies each)", font=("Arial", 14, "bold")).pack(pady=(20, 5))
    tk.Label(root, text=f"{len(pdf_files)} PDF file(s) found in directory").pack()

    status_label = tk.Label(root, text="Ready", fg="gray")
    status_label.pack(pady=10)

    print_button = tk.Button(
        root, text="Print All PDFs", font=("Arial", 12),
        command=lambda: start_printing(status_label, print_button),
    )
    print_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
