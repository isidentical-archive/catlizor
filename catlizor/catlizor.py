from collections import defaultdict
from functools import wraps, partial
from contextlib import contextmanager

WATCH_ATTRIB_METHS = {'__getattribute__', '__setattr__', '__delattr__'}

def attrib_wrapper(hooker, f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with hooker.catch(f.__name__, *args, **kwargs):
            val = f(*args, **kwargs)
        return val
        
    return wrapper
    
class AttribWatchHooks:
    def __init__(self, *hooks):
        self.pre_hooks = defaultdict(list)
        self.post_hooks = defaultdict(list)
        
        for hook in hooks:
            for attr in hook['attribs']:
                if 'pre_hooks' in hook:
                    self.pre_hooks[attr].extend(hook['pre_hooks'])
                if 'post_hooks' in hook:
                    self.post_hooks[attr].extend(hook['post_hooks'])
        
    def exc(self, cond, name, *args, **kwargs):
        hooks = getattr(self, f"{cond}_hooks")[args[1]]
        for hook in hooks:
            hook(name, *args, **kwargs)
    
    @contextmanager
    def catch(self, name, *args, **kwargs):
        try:
            self.exc('pre', name, *args, **kwargs)
            yield
        finally:
            self.exc('post', name, *args, **kwargs)
            
            
def catlizor(cls=None, *, watch=None):
    def wrapper(cls):
        if watch:
            watch_hooks = AttribWatchHooks(*watch)
            hooked_wrapper = partial(attrib_wrapper, watch_hooks)
            
            for meth in WATCH_ATTRIB_METHS:
                setattr(cls, meth, hooked_wrapper(getattr(cls, meth)))
                
        cls.__catlized = True
        return cls
        
    if cls is None:
        return wrapper
    
    return wrapper(cls)
