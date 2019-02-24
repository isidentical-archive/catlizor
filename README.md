# Catlizor
Yet another way to monitor your classes. Watch attribute accesses, method calls and hook actions to them.

## Installation
> Python 3.7+
```
$ pip install catlizor
```
## Usage
`catlizor` is a class decorator that takes your class and modifies it with your specifications. You give the class and the options.

### Options
It is the configuration part of catlizor. You can define your options as python dictionary and then unpack it.

```py
opts = {...}

@catlizor(**opts)
class MyClass:
    ...
```

Catlizor currently accepting 3 options:
- watch > `Sequence[Dict]`
- sign > `bool`
- reset > `bool`

#### Watch
Watch option can take a sequence of monitoring specification.
```
[
    {
        'attribs': ['name', 'age'],
        'funcs': ['person_info'],
        'hooks': {
            'pre': [...],
            'value': [...],
            'post': [...],
        }
        'exclude': {
            'value': ['del', 'set'],
        }
    }
]
```
#### Monitoring Specification
It consists from;
- attribs > `Sequence[Union[str, Ellipsis]]`
- funcs > `Sequence[Union[str, Ellipsis]]`
- hooks > `Dict[str, Sequence[Callable]]`
- exclude > `Dict[str, Sequence[str]`
##### Attribs
Attributes specifies which attributes of an class you are going to watch. By default catlizor watch all get/set/del operations (you can use exclude option to specify operations).

> If you want to watch all attributes you can use `...` (a.k.a Ellipsis)

##### Funcs
Functions specifies functions to watch.

> If you want to watch all attributes you can use `...` (a.k.a Ellipsis)

##### Hooks
Hooks for operations, by default there are 3 hooks;
- pre
- value (called at call-time, also returns value of result as a keyword argument `value`)
- post

##### Exclude
Exclude operations for attribute access, by default there are 3 operations;
- get
- set
- delete

## Example
Lets import our class decorator
```py
from catlizor import catlizor
```
Then create a configuration to our monitoring setup
```py
def fancy_print(*args, **kwargs):
    print(f"{stat:8} access to {args[1]}")

options = {
```
Lets setup up a watching option
```py
    'watch': [
```
it will contain a series of watches
```py
        {
            'attribs': ['name', 'age'],
            'hooks': {
                'post': [fancy_print]
            },
            'exclude': {
                'post': ['del', 'set']
            }
        },
```
Our first watch operation will watch name and age attributes and after every get operation happens it will print which attribute accessed.
```py
        {
            'funcs': ['personal_info'],
            'hooks': {
                'value': [lambda *a, **k: print(f"Personal info acquired, {k['value']}")]
            }
        }
    ]
}
```
The second watch will watch personal_info method and whenever this method called, it print the value.


