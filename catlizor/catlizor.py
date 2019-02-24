from collections import defaultdict, ChainMap
from functools import wraps, partial
from contextlib import contextmanager

SIGNATURE = "__catlized"
WATCH_ATTRIB_METHS = {"__getattribute__", "__setattr__", "__delattr__"}
WATCH_ATTRIB_ALIAS = {
    "get": "__getattribute__",
    "set": "__setattr__",
    "del": "__delattr__",
}


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

    def __init__(self, watches):
        for hook in self.HOOKS:
            setattr(self, f"{hook}_hooks", defaultdict(list))

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

    def exc(self, cond, name, args, kwargs):

        excluded = self.exclude.get(f"{cond}_{args[1]}")
        if (not excluded) or (name not in excluded):
            hooks = getattr(self, f"{cond}_hooks")[args[1]]
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
    def __init__(self, watches):
        for hook in self.HOOKS:
            setattr(self, f"{hook}_hooks", defaultdict(list))

        self.methods = []
        for watch in watches:
            self.methods.extend(watch["funcs"])
            for meth in watch["funcs"]:
                if "hooks" in watch:
                    for hook, fns in watch["hooks"].items():
                        getattr(self, f"{hook}_hooks")[meth].extend(fns)

    def __iter__(self):
        return iter(self.methods)

    def exc(self, cond, name, args, kwargs):
        hooks = getattr(self, f"{cond}_hooks")[name]
        for hook in hooks:
            hook(name, *args, **kwargs)


def catlizor(cls=None, *, watch=None, sign=True):
    def wrapper(cls):
        if watch:
            attr_watch_hooks = AttribWatchHooks(
                filter(lambda watch: watch.get("attribs"), watch)
            )
            hooked_attr_wrapper = partial(attrib_wrapper, attr_watch_hooks)

            for meth in WATCH_ATTRIB_METHS:
                setattr(cls, meth, hooked_attr_wrapper(getattr(cls, meth)))

            if any(filter(lambda watch: watch.get("funcs"), watch)):
                call_watch_hooks = CallWatchHooks(
                    filter(lambda watch: watch.get("funcs"), watch)
                )
                hooked_call_wrapper = partial(attrib_wrapper, call_watch_hooks)

                for meth in call_watch_hooks:
                    setattr(cls, meth, hooked_call_wrapper(getattr(cls, meth)))

        if sign:
            setattr(cls, SIGNATURE, True)

        return cls

    if cls is None:
        return wrapper

    return wrapper(cls)
