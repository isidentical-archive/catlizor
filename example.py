from catlizor import catlizor

def fancy_print(*args, **kwargs):
    print(f"{stat:8} access to {args[1]}")

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
