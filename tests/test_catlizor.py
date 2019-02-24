from catlizor import catlizor
from functools import partial


def fancy_print(cons, name, *args, **kwargs):
    print(f"{cons:8} access to {name} with {args} and {kwargs}")


pre_print = partial(fancy_print, "pre")
post_print = partial(fancy_print, "post")

options = {
    "watch": [
        {
            "attribs": ["name", "age"],
            "pre_hooks": [pre_print],
            "post_hooks": [post_print],
        },
        {
            "attribs": ["__dict__"],
            "pre_hooks": [lambda *a, **k: print('ALERT')],
            "might_missing": True
        }
    ]
}


@catlizor(**options)
class MyClass:
    def __init__(self, name, age=15):
        self.name = name
        self.age = age


mc = MyClass("batuhan")
print(mc.name)
