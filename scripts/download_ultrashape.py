"""Download UltraShape with published size and SHA256 verification."""
from pathlib import Path
from scripts import download_hunyuan21 as download

download.URL = 'https://huggingface.co/infinith/UltraShape/resolve/main/ultrashape_v1.pt'
download.TARGET = Path('C:/_IA/models/ultrashape/ultrashape_v1.pt')
download.TOTAL = 7366231254
download.SHA256 = 'c96ae010c4169597fd0006dcb08056bf6104a1fca249b10fed7ddded324c3f0f'
download.STATUS = Path('C:/_IA/downloads/ultrashape-download.json')

if __name__ == '__main__':
    download.main()
