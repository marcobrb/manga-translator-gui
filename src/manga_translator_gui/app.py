import os
import threading
import json

import deepl
from collections import OrderedDict

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from manga_ocr import MangaOcr


class MangaTranslator():

    def __init__(self, master, do_ocr=True, do_translate=True):
        self.master = master
        self.master.title('translate-ocr')
        self.master.protocol('WM_DELETE_WINDOW', self.exit_message)

        if not do_ocr and do_translate:
            do_translate = False

        self.do_translate = do_translate
        self.do_ocr = do_ocr

        # EDIT #1: read DEEPL API key from env
        if self.do_translate:
            api_key = os.getenv("DEEPL_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "DEEPL_API_KEY is not set. Put it in your environment or in a .env file."
                )
            self.translator = deepl.Translator(api_key)

        self.mainframe = ttk.Frame(master, padding="0 0 0 0")
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)
        self.mainframe.grid(column=0, row=0)
        self.mainframe.bind_all('<Escape>', lambda x: self.label.focus_set())

        self.pictureframe = ttk.Frame(self.mainframe)
        self.pictureframe.grid(column=0, row=0, columnspan=1)
        self.pictureframe.columnconfigure(0, weight=1)
        self.label = Label(self.pictureframe)
        self.canvas = Canvas(self.pictureframe, width=90, height=1400)

        self.textframe = ttk.Frame(self.mainframe)
        self.textframe.grid(column=1, row=0)
        self.textframe.columnconfigure(0, weight=1)
        self.textbox = TextBox(self.textframe, width=35, height=20, state='disabled', spacing3=7)
        self.textbox.grid(column=1, row=0)
        self.translatebox = TextBox(self.textframe, width=35, height=20, state='disabled', wrap='word', spacing3=7)
        self.translatebox.grid(column=1, row=1)

        self.print_instructions()
        self.startup_variables()
        if self.do_ocr:
            ocr_thread = threading.Thread(target=self.startup_mocr)
            ocr_thread.start()
        self.change_page(increment=1)

    def startup_variables(self):
        self.page_counter = -1
        self.jap_text_dict = {0: []}
        self.eng_text_dict = {0: []}
        self.coord_dict = {0: []}
        self.restore_from_file()
        self.is_saved = True
        self.get_images()

    def startup_mocr(self):
        self.mocr = MangaOcr()

    def print_instructions(self):
        instructions = 'Up: print current page dict\nDown: Delete last text from dict\nDelete: delete current page dict\nw: write to file\no: open new folder (to do)'
        print(instructions)

    def exit_message(self):
        if not self.is_saved:
            choice = messagebox.askyesno(message='You have made some changes. Exit without saving?', title='You stupid', icon='question')
            if choice:
                self.master.destroy()
        else:
            self.master.destroy()

    def get_images(self):
        images_list = [file for file in os.listdir() if file.endswith(".jpg")]
        if len(images_list) == 0:
            images_list = [file for file in os.listdir() if file.endswith(".jpeg")]
        if len(images_list) == 0:
            images_list = [file for file in os.listdir() if file.endswith(".png")]
        if len(images_list) == 0:
            print('No images found!')

        def sort_images(e):
            return int(e.split('.')[0])  # 123.jpg -> 123

        images_list = [im for im in images_list if im.split('.')[0].isnumeric()]
        images_list = sorted(images_list, key=sort_images)
        self.max_pages = len(images_list) - 1

        self.load_images(images_list)

    def load_images(self, images_list, width=900, height=1400):
        self.change_title(f'Loading {self.max_pages + 1} images...')
        self.images_list = [Image.open(i) for i in images_list]
        sizes = [img.size for img in self.images_list]

        def resize(size, width, height):
            ratio = width / size[0]
            display_size = [int(d * ratio) + 1 for d in size]
            return display_size

        self.display_sizes = list(map(lambda s: resize(s, width, height), sizes))
        self.display_img_list = []
        for img, size in zip(self.images_list, self.display_sizes):
            img = ImageTk.PhotoImage(img.resize(size))
            self.display_img_list.append(img)

    def change_page(self, increment):
        self.page_counter += increment

        if self.page_counter < 0 or self.page_counter > self.max_pages:
            self.page_counter -= increment
            return

        self.current_img = self.images_list[self.page_counter]
        self.current_display_img = self.display_img_list[self.page_counter]
        self.change_title(f'{self.page_counter + 1}/{self.max_pages + 1}')

        self.canvas.destroy()
        self.canvas = Canvas(self.pictureframe, width=900, height=1400, cursor='cross')
        self.canvas.create_image(0, 0, image=self.current_display_img, anchor='nw')

        self.canvas.bind("<Button-1>", self.get_rect_coords)
        self.canvas.bind("<ButtonRelease-1>", self.get_rect_coords)
        self.canvas.bind("<KeyPress>", self.key)
        self.canvas.bind("<MouseWheel>", lambda event: self.change_page(1) if event.delta < 0 else self.change_page(-1))

        self.canvas.focus_set()
        self.canvas.grid(column=0, row=0)

        self.textbox.clear()
        self.translatebox.clear()
        try:
            self.textbox.restore("".join(self.jap_text_dict[self.page_counter]))
            self.translatebox.restore("".join(self.eng_text_dict[self.page_counter]))
        except Exception:
            pass

        try:
            for rect in self.coord_dict[self.page_counter]:
                ratio_w_h = [
                    self.current_img.width / self.current_display_img.width(),
                    self.current_img.height / self.current_display_img.height()
                ]
                rect = [
                    rect[0] / ratio_w_h[0],
                    rect[1] / ratio_w_h[1],
                    rect[2] / ratio_w_h[0],
                    rect[3] / ratio_w_h[1]
                ]
                self.canvas.create_rectangle(rect[0], rect[1], rect[2], rect[3], fill='', outline='red')
        except Exception:
            pass

    def key(self, event):
        if event.keysym == 'Right':
            self.change_page(increment=1)
        elif event.keysym == 'Left':
            self.change_page(increment=-1)
        elif event.keysym == 'Up':
            print(self.jap_text_dict[self.page_counter])
        elif event.keysym == 'Down':
            try:
                del self.jap_text_dict[self.page_counter][-1]
                del self.eng_text_dict[self.page_counter][-1]
                del self.coord_dict[self.page_counter][-1]
            except IndexError:
                print('No more lines to delete!')
            self.textbox.update("".join(self.jap_text_dict[self.page_counter]))
            self.translatebox.update("".join(self.eng_text_dict[self.page_counter]))
            self.is_saved = False
        elif event.keysym == 'Delete':
            self.jap_text_dict[self.page_counter] = []
            self.eng_text_dict[self.page_counter] = []
            self.coord_dict[self.page_counter] = []
            self.textbox.clear()
            self.translatebox.clear()
            self.is_saved = False

        elif event.keysym == 'w':
            self.write_to_file()
        elif event.keysym == 'o':
            self.change_folder()

    def get_rect_coords(self, event):
        if event.type == EventType.Button:
            self.tl = (event.x, event.y)
        elif event.type == EventType.ButtonRelease:
            self.br = (event.x, event.y)
            new_rect = (*self.tl, *self.br)
            if abs(new_rect[0] - new_rect[2]) < 5:
                return
            self.ocr_img(new_rect)

    def get_ratioed_rect(self, rect):
        ratio_w_h = [
            self.current_img.width / self.current_display_img.width(),
            self.current_img.height / self.current_display_img.height()
        ]
        ratioed_rect = [
            rect[0] * ratio_w_h[0],
            rect[1] * ratio_w_h[1],
            rect[2] * ratio_w_h[0],
            rect[3] * ratio_w_h[1]
        ]
        return ratioed_rect

    def ocr_img(self, rect):
        ratioed_rect = self.get_ratioed_rect(rect)
        self.canvas.create_rectangle(rect[0], rect[1], rect[2], rect[3], fill='', outline='red')

        try:
            self.coord_dict[self.page_counter].append(ratioed_rect)
        except KeyError:
            self.coord_dict[self.page_counter] = []
            self.coord_dict[self.page_counter].append(ratioed_rect)

        if self.do_ocr:
            region = self.current_img.crop(ratioed_rect)
            text = self.mocr(region)
            self.append_text(text, self.jap_text_dict)
            self.textbox.append(text + '\n')
        if self.do_translate:
            self.translate_text(text)
        self.is_saved = False

    def translate_text(self, text):
        result = self.translator.translate_text(text, target_lang='EN-GB')
        self.translatebox.append(result.text + "\n")
        self.append_text(result.text, self.eng_text_dict)

    def append_text(self, text, text_dict):
        try:
            text_dict[self.page_counter].append(text + '\n')
        except KeyError:
            text_dict[self.page_counter] = []
            text_dict[self.page_counter].append(text + '\n')

    def change_folder(self):
        new_folder_path = filedialog.askdirectory()
        if new_folder_path is None or new_folder_path == "":
            return
        for i in self.images_list:
            i.close()
        os.chdir(new_folder_path)
        self.startup_variables()
        self.change_page(1)

    # EDIT #2: cross-platform folder name
    def change_title(self, title):
        folder_name = os.path.basename(os.getcwd())
        self.master.title(folder_name + ' - ' + title)

    def write_to_file(self):
        def order_dict(text_dict):
            temp = [(k, v) for k, v in text_dict.items()]
            sorted_temp = sorted(temp, key=lambda x: x[0])
            return OrderedDict(sorted_temp)

        self.jap_text_dict = order_dict(self.jap_text_dict)
        self.eng_text_dict = order_dict(self.eng_text_dict)
        self.coord_dict = order_dict(self.coord_dict)

        json_dict = {
            "JapPages": self.jap_text_dict,
            "EngPages": self.eng_text_dict,
            "RectCoords": self.coord_dict
        }
        with open(f'{self.folder_name}.json', 'w+', encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=4)
            self.is_saved = True

    def restore_from_file(self):
        self.folder_path, self.folder_name = os.path.split(os.getcwd())
        try:
            with open(f'{self.folder_name}.json', 'r', encoding='utf-8') as f:
                print('Restoring previous session')
                file_dict = json.load(f)

                def parse_str_keys(text_dict):
                    for k in list(text_dict):
                        text_dict[int(k)] = text_dict.pop(k)
                    for k in list(text_dict):
                        if isinstance(k, str):
                            text_dict[int(k)] = text_dict.pop(k)
                    return text_dict

                self.jap_text_dict = parse_str_keys(file_dict['JapPages'])
                self.eng_text_dict = parse_str_keys(file_dict['EngPages'])
                try:
                    self.coord_dict = parse_str_keys(file_dict['RectCoords'])
                except Exception:
                    pass
        except FileNotFoundError:
            print('Previous session not found')
            return None


class TextBox(Text):
    def append(self, text):
        self.configure(state='normal')
        self.insert("end +1 lines", text)
        self.see('end')
        self.configure(state='disabled')

    def clear(self):
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self.configure(state='disabled')

    def restore(self, text):
        self.configure(state='normal')
        self.insert('1.0', text)
        self.see('end')
        self.configure(state='disabled')

    def update(self, text):
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self.insert('1.0', text)
        self.see('end')
        self.configure(state='disabled')
