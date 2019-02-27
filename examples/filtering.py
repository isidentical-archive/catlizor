from catlizor import Hook, Catlizor, CallbackStop

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
class GoMarketHooks(Hook):
    def market_check(result):
        if not any(filter(lambda arg: isinstance(arg, str) and 'market' in arg, result.args)):
            raise CallbackStop
    
    def market_print(result):
        print('Market action !!!')
    
    def other_market_actions(result):
        return NotImplemented

    methods = ['add_task']
    callbacks = [market_check, market_print, other_market_actions]

tm_catlizor = Catlizor.hook(TaskManager, GoMarketHooks)
tm = TaskManager()
tm.add_task('not a m!rket task')
tm.add_task('go to market', 'buy milk')
tm.add_task('back to the home', 'fastly')
tm.add_task('go market again', 'buy eggs')

