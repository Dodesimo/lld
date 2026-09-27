from typing import List
from FileSystemEntry import FileSystemEntry
from File import File
from Folder import Folder

class InvalidPathException(Exception):
    pass

class NotFoundException(Exception):
    pass

class AlreadyExistsException(Exception):
    pass

class NotADirectoryException(Exception):
    pass

class FileSystem:
    def __init__(self):
        self._root = Folder("/")
    
    def create_file(path, content):
        if path == "/":
            raise InvalidPathException("can't create file at root")
        
        parent = self._resolve_parent(path)
        file_name = self.extract_name(path)

        if parent.has_child(file_name):
            raise AlreadyExistsException("entry alr exists")
        
        file = File(file_name, content)
        parent.add_child(file)
        return file
    
    def create_folder(path):
        if path == "/":
            raise AlreadyExistsException("root exist")
        
        parent = self._resolve_parent(path)
        folder_name = self.extract_name(path)

        if parent.has_child(folder_name):
            raise AlreadyExistsException(f"entry already exists")
        
        folder = Folder(folder_name)
        parent.add_child(folder)
        return folder
    
    def delete(self, path):
        if path == "/":
            raise InvalidPathException("can't delete root")
        
        parent = self._resolve_parent(path)
        name = self._extract_name(path)

        removed = parent.remove_child(name)
        if removed is None:
            raise NotFoundException("entry not found")
        
    def list(path):
        entry = self._resolve_parent(path)
        if not entry.is_directory():
            raise NotADirectoryException("can't list file")
        return entry.get_children()
    
    def get(path):
        return self._resolve_path(path)
    
    def rename(self, path, new_name):
        if path == "/":
            raise InvalidPathException("can't rename root")
        
        if not new_name or "/" in new_name:
            raise InvalidPathException("invalid name")
        
        parent = self._resolve_parent(path)
        old_name = self._extract_name(path)

        # the old file isn't found in the children of this parent
        if not parent.has_child(old_name):
            raise NotFoundException("entry not found")
        
        # there's a duplicate file because this new file is present
        if parent.has_child(new_name):
            raise AlreadyExistsException("entry found")
        
        # so we remove the child from the hash map, reinsert w/ new name
        entry = parent.remove_child(old_name)
        entry.set_name(new_name)
        parent.add_child(entry)
    
    def move(src_path, dest_path):
        if src_path == "/":
            raise InvalidPathException("can't move root")
        
        # get the source parent, name, and the actual file 
        src_parent = self._resolve_parent(src_path)
        src_name = self._extract_name(src_path)
        entry = src_parent.get_child(src_name)

        if entry is None:
            raise NotFoundException("not found source")

        # get the dest parent, dest_name    
        dest_parent = self._resolve_parent(dest_path)
        dest_name = self._extract_name(dest_path)

        # check for loop. if the source shows up walking up to the root for the dest, bad cuz we are moving source to leaf
        if entry.is_directory():
            current = dest_parent
            while current is not None:
                if current is entry:
                    raise InvalidPathException("can't move folder into itself")
                current = current.get_parent() # keep going upward till root
        
        if dest_parent.has_child(dest_name):
            raise AlreadyExistsException("destination already exists")
        
        src_parent.remove_child(src_name) # take it out of source directory
        entry.set_name(dest_name) # change the name to the destination one
        dest_parent.add_child(entry) # add the entry to the destination parent 
    
    def _resolve_path(path):
        if not path:
            raise InvalidPathException("path can't be empty")
        
        if not path.startswith("/"):
            raise InvalidPathException("path must be absolute")
        
        if path == "/":
            return self._root
        
        parts = path[1:].split("/") # so for /home/dev/docs/text.txt, we get ['home', 'dev', 'docs', 'text.txt']
        current = self._root
        for part in parts:
            if not part:
                raise InvalidPathException("invalid path, consecutive slashes") # having 2 slashes would mean '', ''
            if not current.is_directory():
                raise NotADirectoryException("not a directory")
            child = current.get_child(part)
            if child is None:
                raise NotFoundException("path not found")
            current = child # this means that current is always one behind the value in the path, so when we hit the actual file current will be the directory right before
        return current
    
    def _resolve_parent(self, path):
        if path == "/":
            raise InvalidPathException("root has no parent")
        
        last_slash = path.rfind("/") # everything after the last slash is the file
        parent_path = "/" if last_slash == 0 else path[:last_slash] # everything before the slash is the parent path 
        parent = self._resolve_path(parent_path)

        if not parent.is_directory(): # so the parent has to be a directory
            raise NotADirectoryException("parent not a directory")
        
        return parent
    
    def _extract_name(self, path):
        last_slash = path.rfind("/") # so we find the right most slash
        return path[last_slash + 1:] # and we get everything right of it 