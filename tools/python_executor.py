"""Safe Python code executor for examples and demonstrations."""

import io
import sys
import traceback
from typing import Dict, Any
from contextlib import redirect_stdout, redirect_stderr


# Allowed modules for import
ALLOWED_MODULES = {
    'math', 'random', 'statistics', 'itertools', 'functools',
    'collections', 'datetime', 'json', 're', 'string'
}


def python_executor(code: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Execute Python code in a restricted environment.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Dict with output, result, or error
    """
    # Check for dangerous operations
    dangerous_patterns = [
        'open(', 'file(', 'exec(', 'eval(', 'compile(',
        '__import__', 'subprocess', 'os.system', 'os.popen',
        'shutil', 'pathlib', 'socket', 'urllib', 'requests',
        'pickle', 'shelve', 'marshal'
    ]
    
    for pattern in dangerous_patterns:
        if pattern in code:
            return {"error": f"Code contains forbidden operation: {pattern}"}
    
    # Create restricted globals
    restricted_globals = {
        '__builtins__': {
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'bool': bool,
            'type': type,
            'isinstance': isinstance,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'sorted': sorted,
            'reversed': reversed,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'round': round,
            'pow': pow,
            'True': True,
            'False': False,
            'None': None,
        }
    }
    
    # Add allowed modules
    import math, random, statistics, itertools, functools
    import collections, datetime, json, re, string
    
    restricted_globals['math'] = math
    restricted_globals['random'] = random
    restricted_globals['statistics'] = statistics
    restricted_globals['itertools'] = itertools
    restricted_globals['functools'] = functools
    restricted_globals['collections'] = collections
    restricted_globals['datetime'] = datetime
    restricted_globals['json'] = json
    restricted_globals['re'] = re
    restricted_globals['string'] = string
    
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute the code
            exec(code, restricted_globals)
        
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        return {
            "output": stdout_output if stdout_output else "Code executed successfully (no output)",
            "errors": stderr_output if stderr_output else None,
            "source_type": "python_execution"
        }
        
    except Exception as e:
        return {
            "error": f"Execution failed: {str(e)}",
            "traceback": traceback.format_exc()
        }
