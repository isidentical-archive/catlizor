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

tm_catlizor.reset()
tm = TaskManager()
tm.add_task("abc", 1, 2, 3)
