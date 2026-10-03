"""Exporta a prévia do link da home (ferramentas/previa-home.html) para assets/previa/home.jpg.

Uso:
  python previa.py

Abre a arte no Chrome sem janela, em resolução dobrada, e reduz para 1200x630.
Depois de exportar, rode python gerar.py se mudou algo nas páginas.
"""
import os
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

RAIZ = pathlib.Path(__file__).resolve().parent
ARTE = RAIZ / 'ferramentas' / 'previa-home.html'
DESTINO = RAIZ / 'assets' / 'previa' / 'home.jpg'

CHROMES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    'google-chrome',
    'chromium',
]


def achar_chrome():
    for c in CHROMES:
        if os.path.isfile(c) or (os.sep not in c and subprocess.run(['which', c], capture_output=True).returncode == 0):
            return c
    sys.exit('Não achei o Chrome nem o Edge instalados.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with tempfile.TemporaryDirectory() as tmp:
        png = pathlib.Path(tmp) / 'previa.png'
        subprocess.run([
            achar_chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
            f'--user-data-dir={tmp}', '--force-device-scale-factor=2', '--window-size=1200,630',
            '--virtual-time-budget=8000', f'--screenshot={png}', ARTE.as_uri(),
        ], check=True, capture_output=True)
        im = Image.open(png).convert('RGB')
        if im.size != (2400, 1260):
            im = im.crop((0, 0, 2400, 1260))
        im = im.resize((1200, 630), Image.LANCZOS)
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        im.save(DESTINO, 'JPEG', quality=88, optimize=True, progressive=True)
    print(f'Prévia salva em {DESTINO.relative_to(RAIZ)} ({DESTINO.stat().st_size // 1024} KB).')


if __name__ == '__main__':
    main()
