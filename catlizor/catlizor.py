from __future__ import annotations

from collections.abc import Sequence as SequenceBase
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from functools import partial, reduce, wraps
from types import FunctionType
from typing import Any, Dict, Optional, Sequence, Union, Callable, Tuple

HOOK_SIGN = "__condition"
HOOK_SPEC = "hook_spec"


def get_hooks(cond, hooks: Tuple[Sequence[Hook], ...]):
    def compare_hook(hook):
        return getattr(HookConditions, cond) in getattr(hook, HOOK_SIGN)

    res = sum(getattr(hook, HOOK_SPEC) for hook in filter(compare_hook, hooks))
    if res == 0:
        res = HookSpec(None, None)
    return res


def meth_wrapper(function: FunctionType, catlizor: Catlizor):
    @wraps(function)
    def wrapper(*args, **kwargs):
        with catlizor.dispatch(function, args, kwargs) as catch:
            res = catch(function(*args, **kwargs))
        return res
    return wrapper


@dataclass
class Result:
    meth: FunctionType
    args: Sequence[Any]
    kwargs: Dict[str, Any]
    condition: HookConditions
    result: Optional[Any] = None


@dataclass
class HookSpec:
    methods: Optional[Sequence[str]]
    callbacks: Optional[Sequence[Callable]]

    def __post_init__(self):
        for attr in vars(self).keys():
            val = getattr(self, attr)
            if not isinstance(val, set) and isinstance(val, SequenceBase):
                setattr(self, attr, set(val))

    def __add__(self, other: HookSpec):
        return self.__class__(
            **{k: (v | getattr(other, k)) for k, v in vars(self).items()}
        )

    def __radd__(self, other: HookSpec):
        if not isinstance(other, self.__class__):
            return self
        return other.__class__(
            **{k: (v | getattr(self, k)) for k, v in vars(other).items()}
        )


class HookConditions(Enum):
    PRE = auto()
    POST = auto()
    ON_CALL = auto()


def hook_condition(cls: type, condition: HookConditions):
    if not hasattr(cls, HOOK_SIGN):
        setattr(cls, HOOK_SIGN, [condition])
    else:
        getattr(cls, HOOK_SIGN).append(condition)

    return cls


class Hook:
    pre = partial(hook_condition, condition=HookConditions.PRE)
    post = partial(hook_condition, condition=HookConditions.POST)
    on_call = partial(hook_condition, condition=HookConditions.ON_CALL)

    def __init_subclass__(cls):
        methods: Sequence[str] = getattr(cls, "methods", [])
        callbacks: Sequence[callable] = getattr(cls, "callbacks", [])
        
        setattr(cls, HOOK_SPEC, HookSpec(methods, callbacks))
        super().__init_subclass__()
    
    @classmethod
    def update_hookspec(cls):
        methods: Sequence[str] = getattr(cls, "methods", [])
        callbacks: Sequence[callable] = getattr(cls, "callbacks", [])
        
        setattr(cls, HOOK_SPEC, HookSpec(methods, callbacks))

class Catlizor:
    """A dispatcher class between your hooks and classes."""
    def __init__(self, klass: type, hook_spec: Dict):
        self.klass = klass
        self.hook_spec = hook_spec
        
        catlizor_wrapper = partial(meth_wrapper, catlizor=self)
        for spec in hook_spec.values():
            for meth in spec[0]:
                try:
                    setattr(self.klass, meth, catlizor_wrapper(getattr(self.klass, meth)))
                except AttributeError as exc:
                    raise Exception(f"Class doesnt have a method named {meth}") from exc
    @classmethod
    def hook(cls, klass: type, *hooks: Sequence[Hook]):
        pre_hooks, post_hooks, on_call_hooks = (
            get_hooks("PRE", hooks),
            get_hooks("POST", hooks),
            get_hooks("ON_CALL", hooks),
        )
        hook_spec = {
            HookConditions.PRE: [pre_hooks.methods, pre_hooks.callbacks],
            HookConditions.POST: [post_hooks.methods, post_hooks.callbacks],
            HookConditions.ON_CALL: [on_call_hooks.methods, on_call_hooks.callbacks],
        }
        return cls(klass, hook_spec)

    @contextmanager
    def dispatch(self, function: FunctionType, args, kwargs):
        spec = (function, args, kwargs)
        tracked_by = self.tracked(function.__name__)
        if tracked_by:
            try:
                if HookConditions.PRE in tracked_by:
                    self.exc(Result(*spec, HookConditions.PRE))
                yield self
                if HookConditions.ON_CALL in tracked_by:
                    self.exc(Result(*spec, HookConditions.ON_CALL, self.last_result))
            finally:
                if HookConditions.POST in tracked_by:
                    self.exc(Result(*spec, HookConditions.POST, kwargs))

    def exc(self, result: Result):
        for callback in self.hook_spec[result.condition][1]:
            callback(result)

    def __call__(self, result: Any):
        self._last_result = result
        return result

    def tracked(self, method_name: str):
        return [
            keys for keys, values in self.hook_spec.items() if method_name in values[0]
        ]

    @property
    def last_result(self):
        result = self._last_result
        self._last_result = None
        return result
