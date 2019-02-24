from collections import defaultdict, ChainMap
from functools import wraps, partial
from contextlib import contextmanager

WATCH_ATTRIB_METHS = {"__getattribute__", "__setattr__", "__delattr__"}
WATCH_ATTRIB_ALIAS = {
    "get": "__getattribute__",
    "set": "__setattr__",
    "del": "__delattr__",
}


def attrib_wrapper(hooker, f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with hooker.catch(f.__name__, *args, **kwargs) as c:
            val = c(f(*args, **kwargs))
        return val

    return wrapper


class AttribWatchHooks:
    def __init__(self, *watches):
        self.pre_hooks = defaultdict(list)
        self.post_hooks = defaultdict(list)
        self.value_hooks = defaultdict(list)
        self.exclude = defaultdict(list)

        self._last_val = None

        for watch in watches:
            for attr in watch["attribs"]:
                if "hooks" in watch:
                    for hook, fns in watch["hooks"].items():
                        getattr(self, f"{hook}_hooks")[attr].extend(fns)
                if "exclude" in watch:
                    for hook, aliases in watch["exclude"].items():
                        self.exclude[f"{hook}_{attr}"].extend(
                            map(WATCH_ATTRIB_ALIAS.get, aliases)
                        )

    def exc(self, cond, name, *args, **kwargs):
        excluded = self.exclude.get(f"{cond}_{args[1]}")
        if (not excluded) or (name not in excluded):
            hooks = getattr(self, f"{cond}_hooks")[args[1]]
            for hook in hooks:
                hook(name, *args, **kwargs)

    @contextmanager
    def catch(self, name, *args, **kwargs):
        try:
            self.exc("pre", name, *args, **kwargs)
            yield self
            self.exc(
                "value", name, *args, **ChainMap(kwargs, {"value": self._last_val})
            )
            self._last_val = None
        finally:
            self.exc("post", name, *args, **kwargs)

    def __call__(self, value):
        self._last_val = value
        return value


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
