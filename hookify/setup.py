from setuptools import setup, Extension

hookify = Extension(
    name = 'hookify',
    sources = ['hookify.c'],
)
    
setup(
    name = 'hookify',
    version = '1.0.0',
    author = 'BTaskaya',
    author_email = 'batuhanosmantaskaya@gmail.com',
    url = "https://github.com/btaskaya/hookify",
    description = "Helper package to catlizor v1-extended series.",
    ext_modules = [hookify]
)
