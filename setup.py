from pathlib import Path
from setuptools import setup, Extension

current_dir = Path(__file__).parent.resolve()

with open(current_dir / 'README.md', encoding='utf-8') as f:
    long_description = f.read()

hookify = Extension(
    name = 'hookify',
    sources = ['hookify/hookify.c'],
    include_dirs = ['hookify']
)
 
setup(
    name = 'catlizor',
    version = '1.9.0', # 1.9.x series for v1-extended
    author = 'BTaskaya',
    author_email = 'batuhanosmantaskaya@gmail.com',
    packages = ['catlizor'],
    ext_modules = [hookify],
    description = "Action Hooks.",
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/btaskaya/catlizor'
)
