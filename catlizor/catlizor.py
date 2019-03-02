from __future__ import annotations

from collections.abc import Sequence as SequenceBase
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from enum import IntEnum
from functools import partial, reduce, wraps
from types import FunctionType
from typing import Any, Dict, Optional, Sequence, Union, Callable, Tuple

CATLIZOR_SIGN = "__catlized"
HOOK_SIGN = "__condition"
HOOK_SPEC = "hook_spec"


class CallbackStop(Exception):
    pass
    
def get_hooks(cond, hooks: Tuple[Sequence[Hook], ...]):
    def compare_hook(hook):
        return getattr(HookConditions, cond) in getattr(hook, HOOK_SIGN)

    res = sum(getattr(hook, HOOK_SPEC) for hook in filter(compare_hook, hooks))
    if res == 0:
        res = HookSpec()
    return res

@dataclass
class Result:
    meth: FunctionType
    args: Sequence[Any]
    kwargs: Dict[str, Any]
    condition: HookConditions
    result: Optional[Any] = None


@dataclass
class HookSpec:
    methods: Optional[Sequence[str]] = field(default_factory=set)
    callbacks: Optional[Sequence[Callable]] = field(default_factory=set)

    def __post_init__(self):
        for attr in vars(self).keys():
            val = getattr(self, attr)
            if not isinstance(val, set) and isinstance(val, SequenceBase):
                setattr(self, attr, set(val))

    def __add__(self, other: HookSpec):
        spec = {k: (v | getattr(other, k)) for k, v in vars(self).items()}
        return self.__class__(**spec)

    def __radd__(self, other: HookSpec):
        if not isinstance(other, self.__class__):
            return self
        return self.__class__.__add__(other, self)


class HookConditions(IntEnum):
    PRE = 0
    POST = 2
    ON_CALL = 1 


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
        setattr(self.klass, CATLIZOR_SIGN, self)
        
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

    def exc(self, result: Result):
        for callback in self.hook_spec[result.condition][1]:
            try:
                callback(result)
            except CallbackStop:
                break
    
    def exc_capi(self, condition, function, args, result):
        condition = [value for member, value in HookConditions.__members__.items() if value == condition]
        if len(condition) != 1:
            condition = None
        else:
            condition = condition[0]
        
        result = Result(function, args, {}, condition, result)
        return self.exc(result)
                
    def tracked(self, method_name: str, as_int: bool = False):
        result = set(keys for keys, values in self.hook_spec.items() if method_name in values[0])
        if as_int:
            result = set(map(int, result))
        
        print(method_name)
        return result
