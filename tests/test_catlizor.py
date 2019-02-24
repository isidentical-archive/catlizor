import unittest
from catlizor import catlizor

class TestCatlizor(unittest.TestCase):
    def setUp(self):
        class MyClass:
            def __init__(self, name, age=15):
                self.name = name
                self.age = age

        self.cls = MyClass
        
if __name__ == '__main__':
    unittest.main()
