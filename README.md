# manga-translator-gui

Tkinter GUI to OCR manga panels and translate with DeepL. See `pyproject.toml` for requirements.


## Setup (Poetry)

```bash
# clone and install
poetry install
cp .env.example .env   # then set DEEPL_API_KEY
```

## Usage

```bash
poetry run manga-translator --folder images_test
```
The first run will download the pretrained ocr models from `manga-ocr` (~450M).

## Keyboard Shortcuts

Right/Left: next/prev page

Up: print JP lines for current page (console)

Down: delete last line/rect

Delete: clear page

w: save session JSON to <foldername>.json

o: change folder


## How it looks like

<img width="1246" height="1309" alt="image" src="https://github.com/user-attachments/assets/764e99c6-9aee-419b-8d1e-23de69e4b8c3" />
