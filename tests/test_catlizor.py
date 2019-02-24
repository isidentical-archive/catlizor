import unittest
from catlizor import catlizor

class TestCatlizor(unittest.TestCase):
    def setUp(self):
        class MyClass:
            def __init__(self, name, age=15):
                self.name = name
                self.age = age

        self.cls = MyClass
    def test_watch_attrib(self):
        total_call = []
        
        def hook(name, *a, **k):
            total_call.append(a[1])
        
        options = {
            "watch": [
                {
                    "attribs": ["name", "age"],
                    "post_hooks": [hook],
                },
                {
                    "attribs": ["__dict__"],
                    "pre_hooks": [hook],
                }
            ]
        }
        
        new_cls = catlizor(self.cls, **options)
        mc = new_cls("batuhan", 13)
        mc.__dict__['name']
        
        print(total_call)
        self.assertEqual(total_call, ['name', 'age', '__dict__'])
        
if __name__ == '__main__':
    unittest.main()
