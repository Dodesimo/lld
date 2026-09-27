- requirements:
	- hierarchical system w/  a single root directory
	- files have string content
	- folders have files and other folders
	- create/delete files and folders
	- list contents of a folder
	- navigate/resolve absolute paths
	- rename and move files and folders
	- get the full path
	- scale
- entities:
	- file: name, content, exists at a specific location
	- folder: has name, contains other entires (files or more folders), doesn't store content
	- path: isn't a object/class, something that gets parsed
	- file system: owns root folder
	- FileSystem owns root Folder, each Folder can have a mix of files, and other folders
- design:
	- FileSystem:
		- can expose root Folder and let callers navigate it, but not good
		- callers would have to navigate manually + parse paths manually (putting a lot of work on the caller)
		- better solution: the FileSystem orchestrator owns the path resolution
			- each operation takes an absolute path, parsing, navigating, validating, delegating to right Folder or File
			- Face: hide complexity of tree navigation behind path-based API
		- stores only the root
		- operations:
			- `createFile(path, content)`
			- `createFolder(path)`
			- `delete(path)`
			- `list(path)`
			- `get(path)`
			- `rename(path, newName)`
			- `move(srcPath, destPath)`
			- throws error all of them
		- ```
		  class FileSystem:
			- root: Folder
			
			+ FileSystem()
			+ createFile(path, content) -> File
			+ createFolder(path) -> Folder
			+ delete(path) 
			+ list(path) -> List<FileSystemEntry>
			+ get(path) -> FileSystemEntry
			+ rename(path, newName)
			+ move(srcPath, destPath)
		  ```
	* File:
		* must track internal content of strings
		* how are paths resolved?
			* storing path as string is bad because any update to the path would require updates to everything below it
			* better: have a reference to the parent folder
				* rename and move operations are only for the entry itself
				* descendants have correct paths because the paths are computed dynamically
				* getting the path is O(depth) instead of O(1)
				* there's bidirectional references
		* ```
		  class File:
			- name: string
			- content: string
			- parent: Folder?
			  
			+ File(name, content)
			+ getName() -> String
			+ setName(name)
			+ getContent() -> String
			+ setContent(content)
			+ getParent() -> Folder?
			+ setParent(Folder?)
			+ getParent() -> String
			+ isDirectory() -> false
		  ```
	* Folder:
		* don't store the children as a list (as that would mean for path resolution, we go through every single child in the list and seeing if theres's a match)
		* better: map from the name to the entry
			* looking up child by name is O(1) regardless of how many siblings
			* also enforces name uniqueness
		* ```
		  class Folder:
			- name: string
			- parent: Folder?
			- children: Map<string, ???>
			
			+ Folder(name)
			+ getName() -> string
			+ setName(name)
			+ getParent() -> Folder?
			+ setParent(Folder?)
			+ getPath() -> string
			+ isDirectory() -> true
			+ addChild(entry) -> boolean
			+ removeChild(name) -> ????
			+ getChild(name) -> ????
			+ hasChild(name) -> boolean
			+ getChildren() -> List<???>
		  ```
	- there needs to be a shared abstraction (FileSystemEntry)
		- there's duplication in the File and Folder
			- every node has name, parent, report its own path
			- only diff: node stores content or contains children
			- can use a shared interface, but that doesn't eliminate duplication as both File and Folder have their own name field and getName() implementation 
			- better approach: abstract base class that have both shared state and behavior
			- ```
			abstract class FileSystemEntry:
				- name: string
				- parent: Folder?
				
				+ getName() -> string
				+ getParent() -> Folder?
				+ setParent(Folder?)
				+ getPath() -> string
				+ isDirectory() -> boolean // abstract (overridden by respective child class)
			
			class File extends FileSystemEntry:
				- content: string
				+ isDirectory() -> false // guards on the access to content/children
			
			class Folder extends FileSystemEntry:
				- children: Map<string, FileSystemEntry>
				+ isDirectory() -> true
			
			class Folder extends FileSystemEntry:
				- children: Map<string, FileSystemEntry>
				+ isDirectory() -> true
			  ```
			- inheritance here is good because subtypes share behavior not just data
			- behavior: stable and unlikely to change
			- subtypes have a "is-a" relationship w/ base
- implementation:
	- create file:
		- ```
		  createFile(path, content)
			  if path == "/":
				  throw InvalidPathException("Cannot create file at root")
			  parent = resolveParent(path)
			  fileName = extractName(path)
			  if parent.hasChild(fileName)
				  throw AlreadyExistsException("Entry exists" + fileName)
			  file = File(fileName, content)
			  parent.addChild(file)
			  return file
		  ```
	* create folder:
		* ```
		  createFolder(path, content)
			  if path == "/":
				  throw InvalidPathException("Cannot create file at root")
			  parent = resolveParent(path)
			  folderName = extractName(path)
			  if parent.hasChild(folderName)
				  throw AlreadyExistsException("Entry exists" + folderName)
			  folder = Folder(folderName)
			  parent.addChild(folder)
			  return folder
		  ```
	* get:
		* ```
		  get(path)
			  return resolvePath(path)
		  ```
	* list:
		* ```
		  list(path)
			  entry = resolvePath(path)
			  if !entry.isDirectory()
				  throw NotADirectoryException("can't list a file")
			  return entry.getChildren()
		  ```
	* delete
		* ```
		  delete(path)
			  if path == "/":
				  throw InvalidPathException("can't delete root")
			  
			  parent = resolveParent(path)
			  name = extractName(path)
			  
			  removed = parent.removeChild(name)
			  if removed == null:
				  throw NotFoundException("entry not found" + path)
		  ```
		* this allows for deletion of non-empty folders
			* sometimes you want to ensure folders are empty so check above that if the entry is a directory and its not empty
	* rename:
		* ```
		  rename(path, newName)
			  if path == "/":
				  throw InvalidPathException("cannot rename")
			  if newName == null or newName is empty or newName.contains("/")
				  throw InvalidPathException("invalid name")
			  parent = resolveParent(path)
			  oldName = extractName(path)
			  
			  if !parent.hasChild(oldName):
				  throw NotFoundException("entry not found") # we didn't find old
			  if parent.hasChild(newName):
				  throw AlreadyExistsException("Entry already exists" + newName) # means we have a duplicate file of this name
			  
			  entry = parent.removeChild(oldName)
			  entry.setName(newName)
			  parent.addChild(entry) # we need to remove child and add child because the hashmap stores it by name string key. we want to get rid of this old name string key and have the object be mapped to new name string key
				
		  ```
	* move:
		* ```
		  move(srcPath, destPath):
			  if srcPath == "/":
				  throw InvalidPathException("Cannot move root")
			  srcParent = resolveParent(srcPath)
			  srcName = extractName(srcPath)
			  entry = srcParent.getChild(srcName) # get the entry of the src
			  
			  if entry == null:
				  throw NotFoundException("source not found")
			  
			  destParent = resolveParent(destPath)
			  destName = extractName(destPath)
			  
			  // if the src is the same as the dest or any of its parents we create a loop so avoid. we don't want the folder moved to be an ancestor of the destination
			  if entry.isDirectory():
				  current = destParent
				  while current != null
					  if current == entry:
						  throw InvalidPathException("cannot move folder into itself")
					  current = current.getParent()
			  
			  if destParent.hasChild(destName)
				  throw AlreadyExistsException("destination already exists: " + destPath)
			  
			  # do the move
			  srcParent.removeChild(srcName)
			  entry.setName(destName)
			  destParent.addChild(entry)
		  ```
	* resolve path:
		* ```
		  resolvePath(path):
			  if path == null or path is empty
				  throw InvalidPathException
			  if !path.startsWith("/")
				  throw InvalidPathException("path must be absolute")
			  if path == "/"
				  return root
			  parts = path.substring(1).split("/")
			  current = root
			  for part in parts:
				if part is empty
					throw InvalidPathException("invalid path: consecutive slashes") # since slashes resolve to empty
				if !current.isDirectory():
					throw NotADirectoryException
				
				child = current.getChild(part)
				if child == null:
					throw NotFoundException("path not found")
				current = child # we are always one folder before the current part if that makes sense
			return current
		  ```
	- resolve parent:
		- ```
		  resolveParent(path)
			  if path == "/":
				  throw InvalidPathException("root has no parent")
			  lastSlash = path.lastIndexOf("/")
			  if lastSlash == 0:
				  parentPath = "/"
			  else:
				  parentPath = path.substring(0, lastIndex)
			  parent = resolvePath(parentPath)
			  if !parent.isDirectory()
				  throw NotADirectoryException
			  return parent
		  ```
	* extract name:
		* ```
		  extractName(path)
			  lastSlash = path.lastIndexOf("/")
			  return path.substring(lastSlash + 1)
		  ```
	* FileSystemEntry getPath()
		* ```
		  getPath()
			  if parent == null:
				  return name # if we are at the root return "/"
			  parentPath = parent.getPath()
			  if parentPath == "/": # if we are at one level below the root 
				  return "/" + name
			  else:
				  return parentPath + "/" + name # get parent + "/" + name
		  ```
	* folder:
		* ```
		  addChild(entry)
			  if entry == null:
				  return false
			  if entry.getName() in children:
				  return False # we have name collision
			  children[entry.getName()] = entry
			  entry.setParent(this) # maintain bidirectional consistency of names
			  return true
		  
		  removeChild(name)
			  if name in children:
				  entry = children[name]
				  entry.setParnet(null) # clear backreference
				  del children[name]
				  return entry
		  
		  getChild(name)
			  return children[name]
		  
		  hasChild(name):
			  return name in children
		  
		  getChildren()
			  return new List(children.values()) # return a copy of values rather than expose internal map
		  ```
		- file:
			- literally just has data
			- ```
			  getContent():
				  return content
				
				setContent(newContent):
					content = newContent
				
				isDirectory()
					return False
			  ```
 - extensibility:
	 - thread-safe:
		 - if two threads write same file, duplicates/files get overwritten
		 - use coarse grained lock:
			 - lock every single method
			 - not good since we have less throughput
		 - or synchronize parent folder (since we can only modify one folder)
		 - process two threads in different folders
		 - this could cause locks if deadlock, sort the lock ids
		 - read/write locks for concurrent readers
		 - searches:
			 - finding a file, do recursive traversal
			 - visiting every entry from root and if name matches search, add to list
			 - if search is frequent, trade space for time with index
				 - for every single entry, we add to index
				 - when we delete, remove it from index
				 - when we create, add to index, delete it, remove, rename, update index
		- have prefix search w/ trie or something, wildcard with secondary index constant search with inverted index
	-  