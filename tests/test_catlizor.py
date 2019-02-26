import unittest
from catlizor import Catlizor, Hook

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
class PreHook(Hook):
    methods = ['add_task']
    callbacks = []

@Hook.on_call
class OnCallHook(Hook):
    methods = ['get_tasks']
    callbacks = []
    
@Hook.post
class PostHook(Hook):
    methods = ['pop_task']
    callbacks = []
    
class TestCatlizor(unittest.TestCase):
    def test_catlizor(self):
        results = []
        def callback(result):
            nonlocal results
            if result.result is not None:
                results.append(result.result)
            else:
                results.append(result.args)
            
        PreHook.callbacks = [callback]
        OnCallHook.callbacks = [callback]
        PostHook.callbacks = [callback]
        
        PreHook.update_hookspec()
        OnCallHook.update_hookspec()
        PostHook.update_hookspec()
        
        tm_catlizor = Catlizor.hook(TaskManager, PreHook, OnCallHook, PostHook)
        tm = TaskManager()
        tm.add_task("a", 1, 2)
        tm.get_tasks("a")
        tm.pop_task()
        
        self.assertEqual(results, [(tm, 'a', 1, 2), (1,2), {}])
        
if __name__ == '__main__':
    unittest.main()
