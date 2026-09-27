'''
file information
'''
from FileSystemEntry import FileSystemEntry

class File(FileSystemEntry):
    def __init__(self, name, content):
        super()._init_(name)
        self._content = content
    
    def get_content(self):
        return self._content
    
    def set_content(self, content):
        self._content = content
    
    def is_directory(self):
        return False

