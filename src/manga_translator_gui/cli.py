import os
import argparse
from tkinter import Tk, filedialog, messagebox
from dotenv import load_dotenv

from .app import MangaTranslator

def main():
    parser = argparse.ArgumentParser(
        prog="manga-translator",
        description="OCR and DeepL translation GUI for manga panels"
    )
    parser.add_argument("--folder", type=str, default=None,
                        help="Folder containing numbered images (e.g., 1.jpg, 2.jpg, ...). If omitted, a dialog opens.")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR")
    parser.add_argument("--no-translate", action="store_true", help="Disable translation")
    args = parser.parse_args()

    load_dotenv()  # loads DEEPL_API_KEY from .env if present

    # Choose folder if not provided
    folder = args.folder
    if folder is None:
        folder = filedialog.askdirectory(title="Select images folder")
        if not folder:
            messagebox.showinfo("manga-translator", "No folder selected. Exiting.")
            return

    # Start GUI
    os.chdir(folder)
    root = Tk()
    app = MangaTranslator(
        root,
        do_ocr=not args.no_ocr,
        do_translate=not args.no_translate
    )
    root.mainloop()
