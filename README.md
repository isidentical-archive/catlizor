# Catlizor (v1)
Action Hooks

> It modifies your methods, they aren't same after the hooking operation so you should use catalizor_instance.reset() method or you can wait for [v1-extended](https://github.com/BTaskaya/catlizor/tree/v1-extended) branch get merged. It overrites default behavior of python with doing some magical stuff and slowes your code down. I'm eager to complete it and never merge it.

## Example
```py
from catlizor import Hook, Catlizor

class TaskManager:
    def __init__(self):
        self.tasks = {}
        
    def add_task(self, task: str, *items):
        self.tasks[task] = items
        
    def pop_task(self):
        return self.tasks.popitem()
    
    def get_tasks(self, task: str):
        return self.tasks[task]
        
@Hook.pre
class PreLoggingHook(Hook):
    methods = ['add_task']
    callbacks = [lambda result: print(result.args, result.kwargs)]

@Hook.on_call
class PostLoggingHook(Hook):
    methods = ['pop_task', 'get_tasks']
    callbacks = [lambda result: print(result.result)]

tm_catlizor = Catlizor.hook(TaskManager, PreLoggingHook, PostLoggingHook)
tm = TaskManager()
tm.add_task("süt al", "markete git", "süt reyonuna ulaş")
tm.get_tasks("süt al")
tm.pop_task()
```

Result (stdout);
```
(<__main__.TaskManager object at 0x7fa851743748>, 'süt al', 'markete git', 'süt reyonuna ulaş') {}
('markete git', 'süt reyonuna ulaş')
('süt al', ('markete git', 'süt reyonuna ulaş'))
```
```
