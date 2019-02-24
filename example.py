from catlizor import catlizor

def fancy_print(name, *args, **kwargs):
    print(f"Access to {args[1]}")

options = {
    'watch': [
        {
            'attribs': ['name', 'age'],
            'hooks': {
                'post': [fancy_print]
            },
            'exclude': {
                'post': ['del', 'set']
            }
        },
        {
            'funcs': ['personal_info'],
            'hooks': {
                'value': [lambda *a, **k: print(f"Personal info acquired, {k['value']}")]
            }
        }
    ]
}


@catlizor(**options)
class Person:
    def __init__(self, name, age):
        self.age = age
        self.name = name
    
    def personal_info(self):
        return f">{self.name} - {self.age}<"
        

me = Person("batuhan", 15)
me.name
me.age
me.personal_info()
