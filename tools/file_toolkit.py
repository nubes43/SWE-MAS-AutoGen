import os
import ast
import re
from typing import Annotated, List, Optional

def write_file(repository_name: str, file_path: str, content: str = "") -> str:
    """
    Create a new File with content or Overwrite an existing file with new content.
    
    Args:
        repository_name (str): The name of the repository
        file_path (str): Path to the file.
        content (str): Content to write or append (default: "").
        
    Returns:
        str: Result of the operation or the content of the file.
    """
    file_path = f"./coding/{repository_name}/{file_path}"
    try:
        with open(file_path, "w") as file:
            file.write(content)
        return f"File {file_path} written successfully."
    except FileNotFoundError:
        return f"File {file_path} not found."
    except Exception as e:
        return f"An error occurred: {e}"


def read_file(file_path: str, repo: str) -> str:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): Path to the file to be read.
        repo (str): Name of repository.

    Returns:
        str: Content of the file or an error message.
    """
    file_path = f"./coding/{repo}/{file_path}"
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error: An error occurred while reading the file: {e}"


def list_files_in_repository(repo: str) -> list:
    """
    Lists all files in a given repository directory recursively.
    
    Args:
        repo (str): Name of the repository.

    Returns:
        list: A list of file paths relative to the repository root, or an error message.
    """
    repo_path = f"./coding/{repo}"
    try:
        if not os.path.exists(repo_path):
            return [f"Error: Repository path '{repo_path}' does not exist."]
        
        file_list = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                # Construct the relative file path
                relative_path = os.path.relpath(os.path.join(root, file), repo_path)
                file_list.append(relative_path)
        
        return file_list
    except Exception as e:
        return [f"Error: An error occurred while listing files: {e}"]
    
def modify_function(
                   repository_name: Annotated[str, "The name of the repository"], 
                   file_path: Annotated[str, "Path to the file."], 
                   function_name: Annotated[str, "Name of the Python Function to Edit."],
                   content: Annotated[str, "content to write to the function"]
                ) -> Annotated[str, "Success/Error Message"]:
    
    """This Function is able to modify a specific Python Method within a python file."""
    
    file_path = f"./coding/{repository_name}/{file_path}"
    
    with open(file_path, "r") as file:
        tree = ast.parse(file.read())
        
    class FunctionModifier(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == function_name:
                node.body = [ast.parse(content).body[0]]
            return node
        
    modified_tree = FunctionModifier().visit(tree)
    modified_code = ast.unparse(modified_tree)
    
    with open(file_path, "w") as file:
        file.write(modified_code)
    
    return f"MODIFY FUNCTION {function_name} in {file_path} successful!"
            
                
def find_and_replace(
                repository_name: Annotated[str, "The name of the repository"], 
                file_path: Annotated[str, "Path to the file."],
                pattern: Annotated[str, "The Regex Pattern to replace."], 
                replacement: Annotated[str, "The replacement for the Regex Pattern."]
            ) -> Annotated[str, "Success or Error Message"]:
    
    """Allows to use search and replace writing operations via Regex expressions."""
    
    file_path = f"./coding/{repository_name}/{file_path}"
    
    with open(file_path, "r") as file:
        content = file.read()
    
    modified_content = re.sub(pattern, replacement, content)
    with open(file_path, "w") as file:
        file.write(modified_content)
        
    return f"FIND AND REPLACE in {file_path} successful!"
    
def list_functions(repository_name: Annotated[str, "Name of the Repository."], filename: Annotated[str, "Path to the Python file"]) -> List[str]:
    """Returns a list of all function names in a Python file."""
    filename = f"./coding/{repository_name}/{filename}"

    with open(filename, "r") as file:
        tree = ast.parse(file.read())
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

def extract_function(repository_name: Annotated[str, "Name of the Repository."], 
                        filename: Annotated[str, "Path to the Python file"], 
                        function_name: Annotated[str, "Function name to extract"]) -> Optional[str]:
    """Extracts the entire source code of a given function."""
    
    filename = f"./coding/{repository_name}/{filename}"
    with open(filename, "r") as file:
        tree = ast.parse(file.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.unparse(node)  # Returns function source code
    return None
    
def modify_function_args(repository_name: Annotated[str, "Name of the Repository."], 
                        filename: Annotated[str, "Path to the Python file"], 
                            function_name: Annotated[str, "Function to modify"], 
                            new_args: Annotated[List[str], "List of new argument names"]):
    """Replaces the arguments of a given function."""
    
    filename = f"./coding/{repository_name}/{filename}"

    with open(filename, "r") as file:
        tree = ast.parse(file.read())
    
    class ArgModifier(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == function_name:
                node.args.args = [ast.arg(arg=name) for name in new_args]
            return node
    
    modified_tree = ArgModifier().visit(tree)
    with open(filename, "w") as file:
        file.write(ast.unparse(modified_tree))

def modify_return_type(repository_name: Annotated[str, "Name of the Repository."], 
                        filename: Annotated[str, "Path to the Python file"], 
                        function_name: Annotated[str, "Function to modify"], 
                        new_return_type: Annotated[str, "New return type annotation"]):
    """Changes the return type annotation of a function."""
    filename = f"./coding/{repository_name}/{filename}"

    with open(filename, "r") as file:
        tree = ast.parse(file.read())
    
    class ReturnTypeModifier(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == function_name:
                node.returns = ast.Name(id=new_return_type)
            return node
    
    modified_tree = ReturnTypeModifier().visit(tree)
    with open(filename, "w") as file:
        file.write(ast.unparse(modified_tree))


def convert_function_to_method(repository_name: Annotated[str, "Name of the Repository."], 
                        filename: Annotated[str, "Path to the Python file"], 
                                function_name: Annotated[str, "Function to convert"], 
                                class_name: Annotated[str, "Class name to place function in"]):
    """Converts a standalone function into a method inside a given class."""
    filename = f"./coding/{repository_name}/{filename}"

    with open(filename, "r") as file:
        tree = ast.parse(file.read())
    
    class FunctionToMethodTransformer(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            if node.name == class_name:
                for func_node in ast.walk(tree):
                    if isinstance(func_node, ast.FunctionDef) and func_node.name == function_name:
                        func_node.args.args.insert(0, ast.arg(arg="self"))  # Add self argument
                        node.body.append(func_node)
                        return node
            return node

    modified_tree = FunctionToMethodTransformer().visit(tree)
    with open(filename, "w") as file:
        file.write(ast.unparse(modified_tree))


def remove_function(repository_name: Annotated[str, "Name of the Repository."], 
                        filename: Annotated[str, "Path to the Python file"], 
                    function_name: Annotated[str, "Function to remove"]):
    """Deletes a function from the Python file."""
    filename = f"./coding/{repository_name}/{filename}"
    with open(filename, "r") as file:
        tree = ast.parse(file.read())

    class FunctionRemover(ast.NodeTransformer):
        def visit_Module(self, node):
            node.body = [stmt for stmt in node.body if not (isinstance(stmt, ast.FunctionDef) and stmt.name == function_name)]
            return node

    modified_tree = FunctionRemover().visit(tree)
    with open(filename, "w") as file:
        file.write(ast.unparse(modified_tree))