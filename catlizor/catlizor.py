from __future__ import annotations

from collections.abc import Sequence as SequenceBase
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from functools import partial, wraps, reduce
from types import FunctionType
from typing import Optional, Dict, Sequence, Union, Any

DEFAULT_CONDITION = 'PRE'
HOOK_SIGN = '__condition'
HOOK_SPEC = 'hook_spec'

def get_hooks(cond, hooks: Sequence[Hooks]):
    def compare_hook(hook):
        return getattr(HookConditions, cond) in getattr(hook, HOOK_SIGN)
    
    res = sum(getattr(hook, HOOK_SPEC) for hook in filter(compare_hook, hooks))
    if res == 0:
        res = HookSpec({}, {})
    return res
    
def meth_wrapper(function: FunctionType, catlizor: Catlizor):
    @wraps(function)
    def wrapper(*args, **kwargs):
        with catlizor.dispatch(function, args, kwargs) as catch:
            res = catch(function(*args, **kwargs))
        return res

@dataclass
class Result:
    name: str
    args: Sequence[Any]
    kwargs: Dict[str, Any]
    condition: HookConditions
    result: Optional[Any] = None

@dataclass
class HookSpec:
    methods: Sequence[str]
    callbacks: Sequence[Callable]
    
    def __post_init__(self):
        for attr in vars(self).keys():
            val = getattr(self, attr)
            if not isinstance(val, set) and isinstance(val, SequenceBase):
                setattr(self, attr, set(val))
    
    def __add__(self, other: HookSpec):
        return self.__class__(**{k: (v | getattr(other, k)) for k, v in vars(self).items()})

    def __radd__(self, other: HookSpec):
        if not isinstance(other, self.__class__):
            return self
        return other.__class__(**{k: (v | getattr(self, k)) for k, v in vars(other).items()})
                
class HookConditions(Enum):
    PRE = auto()
    POST = auto()
    ON_CALL = auto()

def hook_condition(cls: type, condition: HookCondition):
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
        methods: Sequence[str] = getattr(cls, 'methods', [])
        callbacks: Sequence[callable] = getattr(cls, 'callbacks', [])
        if not hasattr(cls, HOOK_SIGN):
            setattr(cls, HOOK_SIGN, [getattr(HookConditions, DEFAULT_CONDITION)])
        
        setattr(cls, HOOK_SPEC, HookSpec(methods, callbacks))
        super().__init_subclass__()
        
class Catlizor:
    
    def __init__(self, klass, hook_spec):
        self.klass = klass
        self.hook_spec = hook_spec
        
    @classmethod
    def hook(cls, klass: type, *hooks: Sequence[Hook]):
        pre_hooks, post_hooks, on_call_hooks = get_hooks('PRE', hooks), get_hooks('POST', hooks), get_hooks('ON_CALL', hooks)
        hook_spec = {
            HookConditions.PRE: [
                pre_hooks.methods,
                pre_hooks.callbacks
            ],
            HookConditions.POST: [
                post_hooks.methods,
                post_hooks.callbacks
            ],
            HookConditions.ON_CALL: [
                on_call_hooks.methods,
                on_call_hooks.callbacks
            ]
        }
        return cls(klass, hook_spec)
        
    @contextmanager
    def dispatch(self, function: FunctionType, args, kwargs):
        spec = (method_name, args, kwargs)
        tracked_by = self.tracked(method_name)
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
        for _, callback in self.hook_spec[result.condition]:
            callback(result)
            
    def catch(self, result: Any):
        self._last_result = result
        return result

    def tracked(self, method_name: str):
        return [keys for keys, values in self.hook_spec.items() if method_name in values[1]]
        
    @property
    def last_result(self):
        result = self._last_result
        self._last_result = None
        return result
