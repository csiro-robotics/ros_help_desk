#!/usr/bin/env python3
import os
import re
import ast
import json
from typing import Optional
from langchain.agents import tool


def find_workspace_root():
    """Find the PenguinPi workspace root by looking for characteristic directories"""
    # Hardcoded path for PenguinPi workspace in Docker
    hardcoded_path = "/PenguinPi_agent/ros_ws"
    if os.path.exists(hardcoded_path):
        return hardcoded_path
    
    # Fallback to auto-detection if hardcoded path doesn't exist
    current_path = os.path.abspath(__file__)
    
    while current_path != os.path.dirname(current_path):
        if (os.path.exists(os.path.join(current_path, "ros_ws")) and 
            os.path.exists(os.path.join(current_path, "ros_ws", "src"))):
            return current_path
        current_path = os.path.dirname(current_path)
    
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

WORKSPACE_ROOT = find_workspace_root()

@tool
def analyze_all_codes_in_directory(query: str, base_dir: str = None) -> str:
    """
    Searches the codebase starting from base_dir for occurrences of the query string or pattern.
    Returns file paths and code snippets where the query is found.
    
    Args:
        query (str): The search query (can be a simple string or a regex pattern).
        base_dir (str): The root directory to start the search from. 
                        If not provided, uses the PenguinPi workspace root
    
    Returns:
        str: A formatted string with results (file paths and matching code snippets), or a message if no matches are found.
    """
    # Always use our correct workspace root, ignore potentially wrong base_dir
    if base_dir is None:
        base_dir = '/PenguinPi_agent/ros_ws' #os.environ.get("CODEBASE_DIR", "."    )
    
    results = []
    for root, dirs, files in os.walk(base_dir):
        if any(skip_dir in root for skip_dir in ['build', 'install', 'log', 'devel', '.git', '__pycache__']):
            continue
            
        for file in files:
            if file.endswith((".py", ".launch", ".yaml", ".yml", ".cpp", ".h", ".hpp", ".c", ".msg", ".srv", ".action")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = list(re.finditer(query, content, re.IGNORECASE))
                    if matches:
                        for match in matches:
                            start = max(match.start() - 40, 0)
                            end = min(match.end() + 40, len(content))
                            snippet = content[start:end].replace("\n", " ")
                            rel_path = os.path.relpath(file_path, base_dir)
                            results.append(f"File: {rel_path}\nSnippet: ...{snippet}...\n")
                except Exception as e:
                    results.append(f"Error reading {file_path}: {e}")
    
    if not results:
        return "No matches found for the query."
    return "\n".join(results)

@tool
def analyze_a_code_file(query: str, file_path: str) -> str:
    """
    Searches a specific file for occurrences of the query string or pattern.
    Returns code snippets where the query is found.
    
    Args:
        query (str): The search query (can be a simple string or a regex pattern).
        file_path (str): The script file to be analyzed (relative to workspace or absolute path)
    
    Returns:
        str: A formatted string with results (matching code snippets), or a message if no matches are found.
    """
    if file_path is None:
        return "You need to provide a file name to analyze"
    
    if not os.path.isabs(file_path):
        file_path = os.path.join(WORKSPACE_ROOT, file_path)
    
    results = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = list(re.finditer(query, content, re.IGNORECASE))
        if matches:
            for match in matches:
                start = max(match.start() - 40, 0)
                end = min(match.end() + 40, len(content))
                snippet = content[start:end].replace("\n", " ")
                results.append(f"File: {file_path}\nSnippet: ...{snippet}...\n")
    except Exception as e:
        results.append(f"Error reading {file_path}: {e}")
    
    if not results:
        return "No matches found for the query."
    return "\n".join(results)

# @tool
def analyze_code_limited(query: str, base_dir: str = None, max_files: int = 10, max_matches: int = 3) -> str:
    """
    Searches the codebase starting from base_dir for occurrences of the query string or pattern.
    Returns a summary of file paths and code snippets where the query is found.

    Args:
        query (str): The search query (can be a simple string or a regex pattern).
        base_dir (str): The root directory to start the search from. If not provided, uses PenguinPi workspace root
        max_files (int): Maximum number of files to scan.
        max_matches (int): Maximum number of matches to return per file.

    Returns:
        str: A formatted string with results, or a message if no matches are found.
    """
    # Always use our correct workspace root, ignore potentially wrong base_dir
    if base_dir is None:
        base_dir = '/PenguinPi_agent/ros_ws' #
    
    results = []
    files_scanned = 0
    
    for root, dirs, files in os.walk(base_dir):
        if any(skip_dir in root for skip_dir in ['build', 'install', 'log', 'devel', '.git', '__pycache__']):
            continue
            
        for file in files:
            if file.endswith((".py", ".launch", ".yaml", ".yml", ".cpp", ".h", ".hpp", ".c", ".msg", ".srv", ".action")):
                file_path = os.path.join(root, file)
                files_scanned += 1
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = list(re.finditer(query, content, re.IGNORECASE))
                    if matches:
                        count = 0
                        for match in matches:
                            if count >= max_matches:
                                results.append(f"... more matches in {os.path.relpath(file_path, base_dir)} ...\n")
                                break
                            start = max(match.start() - 40, 0)
                            end = min(match.end() + 40, len(content))
                            snippet = content[start:end].replace("\n", " ")
                            rel_path = os.path.relpath(file_path, base_dir)
                            results.append(f"File: {rel_path}\nSnippet: ...{snippet}...\n")
                            count += 1
                except Exception as e:
                    results.append(f"Error reading {file_path}: {e}")
                if files_scanned >= max_files:
                    results.append(f"... reached max_files limit ({max_files}); stopping search.\n")
                    break
        if files_scanned >= max_files:
            break

    if not results:
        return "No matches found for the query."
    return "\n".join(results)

@tool
def list_code_hierarchy(base_dir: str = None, max_depth: int = 3) -> str:
    """
    Lists the code hierarchy starting from base_dir up to max_depth levels.
    Directories and files are displayed in a tree-like structure.
    
    Args:
        base_dir (str): The root directory to start the hierarchy from. If not provided, uses PenguinPi workspace root.
        max_depth (int): Maximum depth of recursion for listing directories.
    
    Returns:
        str: A string representing the hierarchical structure of the codebase.
    """
    # Always use our correct workspace root, ignore potentially wrong base_dir
    if base_dir is None or not os.path.exists(base_dir) or "penguinpi" in base_dir.lower():
        base_dir = WORKSPACE_ROOT
    
    def build_tree(current_dir: str, depth: int) -> str:
        if depth > max_depth:
            return ""
        tree_str = ""
        try:
            entries = os.listdir(current_dir)
        except Exception as e:
            return f"Error reading directory {current_dir}: {e}\n"
        
        entries = [e for e in entries if not e.startswith('.') and e not in ['build', 'install', 'log', 'devel', '__pycache__']]
        entries.sort()
        
        for entry in entries:
            path = os.path.join(current_dir, entry)
            indent = "    " * depth
            if os.path.isdir(path):
                tree_str += f"{indent}[D] {entry}\n"
                tree_str += build_tree(path, depth + 1)
            else:
                tree_str += f"{indent}[F] {entry}\n"
        return tree_str

    hierarchy = build_tree(base_dir, 0)
    return hierarchy if hierarchy else "No files found."

@tool
def extract_code_summary(file_path: str) -> str:
    """
    Extracts function and class summaries from a Python script.
    
    Args:
        file_path (str): Path to the Python file to analyze (relative to workspace or absolute)
    
    Returns:
        str: A formatted summary of functions and classes found in the file
    """
    if not os.path.isabs(file_path):
        file_path = os.path.join(WORKSPACE_ROOT, file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)
    except Exception as e:
        return f"Error parsing {file_path}: {e}"
    
    summary = {
        "functions": {},
        "classes": {},
    }
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            summary["functions"][node.name] = ast.get_docstring(node) or "No docstring available"
        elif isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or "No docstring available"
            methods = {}
            for subnode in node.body:
                if isinstance(subnode, ast.FunctionDef):
                    methods[subnode.name] = ast.get_docstring(subnode) or "No docstring available"
            summary["classes"][node.name] = {"doc": class_doc, "methods": methods}
    
    result = f"Code Summary for {os.path.relpath(file_path, WORKSPACE_ROOT)}:\n\n"
    
    if summary["functions"]:
        result += "FUNCTIONS:\n"
        for func_name, doc in summary["functions"].items():
            result += f"  - {func_name}: {doc}\n"
        result += "\n"
    
    if summary["classes"]:
        result += "CLASSES:\n"
        for class_name, class_info in summary["classes"].items():
            result += f"  - {class_name}: {class_info['doc']}\n"
            if class_info["methods"]:
                result += "    Methods:\n"
                for method_name, method_doc in class_info["methods"].items():
                    result += f"      - {method_name}: {method_doc}\n"
            result += "\n"
    
    if not summary["functions"] and not summary["classes"]:
        result += "No functions or classes found in this file.\n"
    
    return result

@tool
def analyze_code_functionality(file_path: str, expected_behavior: str) -> str:
    """
    Analyzes a Python script and compares its functionality with expected behavior.
    
    Args:
        file_path (str): Path to the Python file to analyze (relative to workspace or absolute)
        expected_behavior (str): Description of the expected behavior to compare against
    
    Returns:
        str: Analysis of the code functionality and comparison with expected behavior
    """
    if not os.path.isabs(file_path):
        file_path = os.path.join(WORKSPACE_ROOT, file_path)
        
    if not os.path.exists(file_path) or not file_path.endswith(".py"):
        return "Invalid file path or not a Python script."
    
    summary = extract_code_summary(file_path)
    
    analysis = f"Code Analysis for {os.path.relpath(file_path, WORKSPACE_ROOT)}:\n\n"
    analysis += f"{summary}\n"
    analysis += f"Expected Behavior: {expected_behavior}\n\n"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        
        expected_keywords = expected_behavior.lower().split()
        found_keywords = [keyword for keyword in expected_keywords if keyword in content]
        
        if len(found_keywords) > len(expected_keywords) * 0.5:
            match_score = f"Likely matches expected behavior (found {len(found_keywords)}/{len(expected_keywords)} keywords)"
        else:
            match_score = f"May not fully match expected behavior (found {len(found_keywords)}/{len(expected_keywords)} keywords)"
        
        analysis += f"Comparison: {match_score}\n"
        analysis += f"Found keywords: {', '.join(found_keywords)}\n"
        
    except Exception as e:
        analysis += f"Error analyzing content: {e}\n"
    
    return analysis

@tool
def search_ros_topics_in_code(topic_name: str = None) -> str:
    """
    Searches for ROS topic usage in the codebase.
    
    Args:
        topic_name (str): Specific topic name to search for. If None, searches for all topic-related code.
    
    Returns:
        str: Information about ROS topics found in the codebase
    """
    if topic_name:
        query = topic_name
        description = f"ROS topic '{topic_name}'"
    else:
        query = r"(Publisher|Subscriber|rospy\.Publisher|rospy\.Subscriber|/\w+/\w+)"
        description = "ROS topic-related code"
    
    results = analyze_code_limited(query, max_files=20, max_matches=5)
    
    return f"Search results for {description}:\n\n{results}"

@tool
def find_ros_nodes_in_code() -> str:
    """
    Searches for ROS node definitions and initialization in the codebase.
    
    Returns:
        str: Information about ROS nodes found in the codebase
    """
    query = r"(rospy\.init_node|rclpy\.init|ros::init)"
    results = analyze_code_limited(query, max_files=20, max_matches=3)
    
    return f"ROS node initialization code found:\n\n{results}"

CODE_ANALYZER_TOOLS = [
    analyze_all_codes_in_directory,
    analyze_a_code_file,
    analyze_code_limited,
    list_code_hierarchy,
    extract_code_summary,
    analyze_code_functionality,
    search_ros_topics_in_code,
    find_ros_nodes_in_code,
] 