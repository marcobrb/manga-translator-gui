# manga-translator-gui

Tkinter GUI to OCR manga panels and translate with DeepL.

## Requirements
- Python 3.10–3.12
- Tkinter (Linux: `sudo apt install python3-tk`)

## Setup (Poetry)
```bash
# install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -

# clone and install
poetry install
cp .env.example .env   # then set DEEPL_API_KEY

## Usage
```
poetry run manga-translator --folder images_test
```
The first run will download the pretrained ocr models from `manga-ocr` (~450M)

## Keyboard Shortcuts

Right/Left: next/prev page

Up: print JP lines for current page (console)

Down: delete last line/rect

Delete: clear page

w: save session JSON to <foldername>.json

o: change folder