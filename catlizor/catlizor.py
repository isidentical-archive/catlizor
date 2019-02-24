from collections import defaultdict, ChainMap
from functools import wraps, partial
from contextlib import contextmanager

AFFECTED = "__catlized_fields"
SIGNATURE = "__catlized"

WATCH_ATTRIB_METHS = {"__getattribute__", "__setattr__", "__delattr__"}
WATCH_ATTRIB_ALIAS = {
    "get": "__getattribute__",
    "set": "__setattr__",
    "del": "__delattr__",
}


CUSTOM_CALL = {'__new__', '__class__', '__repr__', *WATCH_ATTRIB_METHS}
CUSTOM_ATTR = {}


def attrib_wrapper(hooker, f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "name" in kwargs:
            kwargs["_name"] = kwargs.pop("name")

        with hooker.catch(f.__name__, *args, **kwargs) as c:
            val = c(f(*args, **kwargs))
        return val
    
    return wrapper


class AttribWatchHooks:
    HOOKS = ("pre", "post", "value")

    def __init__(self, watches, cls=None):
        for hook in self.HOOKS:
            setattr(self, f"{hook}_hooks", defaultdict(list))

        self.exclude = defaultdict(list)

        self._last_val = None


        if any(filter(lambda watch: Ellipsis in watch["attribs"], watches)):
            self.fulfil = True
        else:
            self.fulfil = False
                    
        for watch in watches:            
            for attr in watch["attribs"]:
                if self.fulfil:
                    attr = Ellipsis
                
                if "hooks" in watch:
                    for hook, fns in watch["hooks"].items():
                        getattr(self, f"{hook}_hooks")[attr].extend(fns)
                if "exclude" in watch:
                    for hook, aliases in watch["exclude"].items():
                        self.exclude[f"{hook}_{attr}"].extend(
                            map(WATCH_ATTRIB_ALIAS.get, aliases)
                        )
                
                if self.fulfil:
                    break

    def exc(self, cond, name, args, kwargs):
        attr = Ellipsis if self.fulfil else args[1]
        excluded = self.exclude.get(f"{cond}_{attr}")
        if (not excluded) or (name not in excluded):
            hooks = getattr(self, f"{cond}_hooks")[attr]
            for hook in hooks:
                hook(name, *args, **kwargs)

    @contextmanager
    def catch(self, name, *args, **kwargs):
        try:
            self.exc("pre", name, args, kwargs)
            yield self
            self.exc("value", name, args, ChainMap(kwargs, {"value": self._last_val}))
            self._last_val = None
        finally:
            self.exc("post", name, args, kwargs)

    def __call__(self, value):
        self._last_val = value
        return value


class CallWatchHooks(AttribWatchHooks):
    def __init__(self, watches, cls=None):
        for hook in self.HOOKS:
            setattr(self, f"{hook}_hooks", defaultdict(list))

        self.methods = []
        if any(filter(lambda watch: Ellipsis in watch["funcs"], watches)):
            self.fulfil = True
            self.methods.extend(meth for meth in dir(cls) if callable(getattr(cls, meth)) and (meth not in CUSTOM_CALL))
        else:
            self.fulfil = False
            
        for watch in watches:
            if not self.fulfil:
                self.methods.extend(watch["funcs"])
            
            for meth in watch["funcs"]:
                if "hooks" in watch:
                    for hook, fns in watch["hooks"].items():
                        getattr(self, f"{hook}_hooks")[meth].extend(fns)

    def __iter__(self):
        return iter(self.methods)

    def exc(self, cond, name, args, kwargs):
        hooks = getattr(self, f"{cond}_hooks")
        hooks = hooks[...] if self.fulfil else hooks[name]
        for hook in hooks:
            hook(name, *args, **kwargs)


def catlizor(cls=None, *, watch=None, sign=True, reset=False):
    def wrapper(cls):
        if watch:
            affects = set()
            
            attr_watchers = tuple(filter(lambda watch: watch.get("attribs"), watch))
            call_watchers = tuple(filter(lambda watch: watch.get("funcs"), watch))
            
            if any(attr_watchers):
                attr_watch_hooks = AttribWatchHooks(attr_watchers, cls)
                hooked_attr_wrapper = partial(attrib_wrapper, attr_watch_hooks)

                for meth in WATCH_ATTRIB_METHS:
                    affects.add(meth)
                    setattr(cls, meth, hooked_attr_wrapper(getattr(cls, meth)))

            if any(call_watchers):
                call_watch_hooks = CallWatchHooks(call_watchers, cls)
                hooked_call_wrapper = partial(attrib_wrapper, call_watch_hooks)

                for meth in call_watch_hooks:
                    try:
                        setattr(cls, meth, hooked_call_wrapper(getattr(cls, meth)))
                        affects.add(meth)
                    except TypeError:
                        continue
        if sign:
            setattr(cls, SIGNATURE, True)
            if watch:
                setattr(cls, AFFECTED, affects)
            
        if reset:
            if (hasattr(cls, SIGNATURE) and hasattr(cls, AFFECTED)):
                for meth in getattr(cls, AFFECTED):
                    fn = getattr(cls, meth)
                    if hasattr(fn, '__wrapped__'):
                        setattr(cls, meth, getattr(fn, '__wrapped__'))
                setattr(cls, AFFECTED, {})
            
        return cls

    if cls is None:
        return wrapper

    return wrapper(cls)
