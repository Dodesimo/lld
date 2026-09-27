'''
abstract class that establishes contract for FileSystem entries
'''

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Folder import folder

class FileSystemEntry(ABC):
    def __init__(self, name: str):
        self._name = name
        self._parent = None
    
    def get_name(self):
        return self._name
    
    def set_name(self, name):
        self._name = name
    
    def get_parent():
        return self._parent
    
    def set_parent(parent):
        self._parent = parent
    
    def get_path(self):
        if self._parent is None:
            return self._name #  if we are at the top return the root name (/)

        parent_path = self._parent.get_path()
        if parent_path == "/":
            return "/" + self._name  # if we are at one level below the root return this
        
        return parent_path + "/" + self._name # this is the path of the current field
    
    @abstractmethod
    def is_directory(self):
        pass # every file/folder overrides this