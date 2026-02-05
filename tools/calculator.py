"""Safe calculator tool for mathematical expressions."""

import math
import re
from typing import Dict, Any


# Safe math functions available
SAFE_FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'log2': math.log2,
    'exp': math.exp,
    'floor': math.floor,
    'ceil': math.ceil,
    'pi': math.pi,
    'e': math.e,
}


def calculator(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Dict with result or error
    """
    try:
        # Clean the expression
        expression = expression.strip()
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'__', r'import', r'exec', r'eval', r'open', r'file',
            r'os\.', r'sys\.', r'subprocess', r'compile'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return {"error": f"Expression contains forbidden pattern: {pattern}"}
        
        # Evaluate with only safe functions
        result = eval(expression, {"__builtins__": {}}, SAFE_FUNCTIONS)
        
        return {
            "expression": expression,
            "result": result,
            "source_type": "calculation"
        }
        
    except ZeroDivisionError:
        return {"error": "Division by zero"}
    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}
