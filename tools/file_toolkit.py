import os


async def manipulate_file(repository_name: str, file_path: str, operation: str, content: str = "") -> str:
    """
    Manipulates a file based on the specified operation.
    
    Args:
        repository_name (str): The name of the repository
        file_path (str): Path to the file.
        operation (str): Operation to perform - "read", "write", or "append".
        content (str): Content to write or append (default: "").
        
    Returns:
        str: Result of the operation or the content of the file.
    """
    file_path = f"./coding/{repository_name}/{file_path}"
    try:
        if operation == "read":
            with open(file_path, "r") as file:
                return file.read()
        elif operation == "write":
            with open(file_path, "w") as file:
                file.write(content)
            return f"File {file_path} written successfully."
        elif operation == "append":
            with open(file_path, "a") as file:
                file.write(content)
            return f"Content appended to {file_path} successfully."
        else:
            return "Invalid operation. Use 'read', 'write', or 'append'."
    except FileNotFoundError:
        return f"File {file_path} not found."
    except Exception as e:
        return f"An error occurred: {e}"


# async def read_file(file_path: str, repo) -> str:
#     """
#     Reads the content of a file and returns it as a string.

#     Args:
#         file_path (str): Path to the file to be read.

#     Returns:
#         str: Content of the file or an error message.
#     """
#     file_path = f"./coding/{repo}/{file_path}"
#     try:
#         with open(file_path, "r") as file:
#             return file.read()
#     except FileNotFoundError:
#         return f"Error: File '{file_path}' not found."
#     except Exception as e:
#         return f"Error: An error occurred while reading the file: {e}"


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