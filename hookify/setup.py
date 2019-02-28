from setuptools import setup, Extension

hookify = Extension(
    name = 'hookify',
    sources = ['hookify/hookify.c'],
    include_dirs = ['hookify']
)
    
setup(
    name = 'hookify',
    version = '0.0.1',
    author = 'BTaskaya',
    author_email = 'batuhanosmantaskaya@gmail.com',
    description = "Internal hooks.",
    ext_modules = [hookify]
)
