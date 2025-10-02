# --- scripts/build_graph.py ---

import os
import ast
import json
import sys

# --- Path Fix ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Fix ---

import config

def get_relative_path(file_path):
    """Converts an absolute file path to a project-relative path."""
    return os.path.relpath(file_path, config.TARGET_REPO_PATH).replace("\\", "/")

# --- Pass 1: Find all definitions (classes, functions, methods) ---
class DefinitionVisitor(ast.NodeVisitor):
    def __init__(self, relative_path, nodes, symbol_table):
        self.relative_path = relative_path
        self.nodes = nodes
        self.symbol_table = symbol_table
        self.class_stack = []

    def visit_ClassDef(self, node):
        class_id = f"{self.relative_path}::{node.name}"
        self.nodes.append({"id": class_id, "type": "class", "name": node.name, "file": self.relative_path})
        self.symbol_table[class_id] = self.nodes[-1]
        
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        if self.class_stack:
            parent_class = "::".join(self.class_stack)
            func_id = f"{self.relative_path}::{parent_class}::{node.name}"
            node_type = "method"
        else:
            func_id = f"{self.relative_path}::{node.name}"
            node_type = "function"
        
        self.nodes.append({"id": func_id, "type": node_type, "name": node.name, "file": self.relative_path})
        self.symbol_table[func_id] = self.nodes[-1]
        self.generic_visit(node)

# --- Pass 2: Find all calls ---
class CallVisitor(ast.NodeVisitor):
    def __init__(self, relative_path, edges, symbol_table):
        self.relative_path = relative_path
        self.edges = edges
        self.symbol_table = symbol_table
        self.scope_stack = []

    def get_caller_id(self):
        return self.scope_stack[-1] if self.scope_stack else None

    def visit_ClassDef(self, node):
        class_id = f"{self.relative_path}::{node.name}"
        self.scope_stack.append(class_id)
        self.generic_visit(node)
        self.scope_stack.pop()
    
    def visit_FunctionDef(self, node):
        if self.scope_stack and "::" in self.scope_stack[-1]: # Inside a class
            parent_scope = self.scope_stack[-1]
            func_id = f"{parent_scope}::{node.name}"
        else:
            func_id = f"{self.relative_path}::{node.name}"
        
        self.scope_stack.append(func_id)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node):
        caller_id = self.get_caller_id()
        if not caller_id:
            self.generic_visit(node)
            return

        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        if callee_name:
            # Simple heuristic: find any symbol that ends with the called name.
            # This is not perfect but works for many cases.
            for key in self.symbol_table:
                if key.endswith(f"::{callee_name}"):
                    target_id = key
                    self.edges.append({"source": caller_id, "target": target_id, "type": "CALLS"})
                    break # Assume first match is correct
        
        self.generic_visit(node)


def main():
    print("--- 🚀 Starting Code Graph Construction ---")
    all_nodes = []
    all_edges = []
    symbol_table = {}
    files_to_process = []

    for root, _, files in os.walk(config.TARGET_REPO_PATH):
        if any(skip in root for skip in [".venv", "__pycache__", ".git"]):
            continue
        for file in files:
            if file.endswith(".py"):
                files_to_process.append(os.path.join(root, file))

    print(f"\n--- Pass 1: Discovering {len(files_to_process)} files... ---")
    for file_path in files_to_process:
        relative_path = get_relative_path(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            visitor = DefinitionVisitor(relative_path, all_nodes, symbol_table)
            visitor.visit(tree)
        except Exception as e:
            print(f"  - ❌ Error parsing {relative_path}: {e}")
    print(f"--- ✅ Found {len(all_nodes)} total definitions. ---")

    print(f"\n--- Pass 2: Resolving calls... ---")
    for file_path in files_to_process:
        relative_path = get_relative_path(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            visitor = CallVisitor(relative_path, all_edges, symbol_table)
            visitor.visit(tree)
        except Exception as e:
            print(f"  - ❌ Error parsing {relative_path}: {e}")

    # Remove duplicate edges
    unique_edges = [dict(t) for t in {tuple(d.items()) for d in all_edges}]
    print(f"--- ✅ Resolved {len(unique_edges)} total calls. ---")

    full_graph = {"nodes": all_nodes, "edges": unique_edges}
    
    with open(config.CODE_GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(full_graph, f, indent=2)
    
    print(f"\n--- 🎉 Code graph saved to {config.CODE_GRAPH_PATH} ---")

if __name__ == "__main__":
    main()