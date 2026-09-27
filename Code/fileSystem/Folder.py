from typing import Dict, List, Optional
from FileSystemEntry import FileSystem

class Folder(FileSystemEntry):
    def __init__(self, name):
        super().__init__(name)
        self._children: Dict[str, FileSystemEntry] = {}
    
    def is_directory(self):
        return True

    def add_child(self, entry):
        if entry is None:
            return False

        # if there's duplicate, return false
        if entry.get_name() in self._children:
            return False
        
        self._children[entry.get_name()] = entry
        entry.set_parent(self)
        return True # so we set the name to entry map, and then set the parent of the child
    
    def remove_child(name):
        if name in self.children:
            entry = self._children[name]
            del self._children[name]
            # get the entry
            if entry:
                entry.set_parent(None) # get rid of the dict value, and reset parent
            return entry
        return None
    
    def get_child(name):
        return self._children[name] 
    
    def has_child(name):
        return name in self._children 
    
    def get_children(self):
        return list(self._children.values()) # read only list so that callers don't mutate the map
