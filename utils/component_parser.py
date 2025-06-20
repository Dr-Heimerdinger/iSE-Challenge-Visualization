import ast
import re

def extract_ui_components(ui_code: str) -> list:
    """
    Extract Gradio UI components from Python code
    Returns list of components with type and variable name
    """
    components = []
    pattern = r"(\w+)\s*=\s*gr\.(\w+)\("
    
    try:
        # Try regex first for simplicity
        matches = re.findall(pattern, ui_code)
        for var_name, comp_type in matches:
            components.append({
                "var_name": var_name,
                "type": comp_type
            })
            
        # Fallback to AST if regex fails
        if not components:
            tree = ast.parse(ui_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (isinstance(target, ast.Name) and 
                            isinstance(node.value, ast.Call) and
                            isinstance(node.value.func, ast.Attribute) and
                            node.value.func.attr in ["Image", "Textbox", "File", "Slider", "Dropdown"] and
                            node.value.func.value.id == "gr"):
                            
                            components.append({
                                "var_name": target.id,
                                "type": node.value.func.attr
                            })
    except Exception:
        # Return empty list if parsing fails
        pass
        
    return components