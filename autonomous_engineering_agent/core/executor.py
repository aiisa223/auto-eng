"""
Code execution and validation system for the autonomous engineering agent.
"""

import ast
import logging
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class CodeExecutor:
    """Handles code execution and validation."""
    
    def __init__(self, working_dir: Optional[str] = None):
        """Initialize the code executor.
        
        Args:
            working_dir: Optional working directory for code execution
        """
        self.working_dir = working_dir or tempfile.mkdtemp()
        os.makedirs(self.working_dir, exist_ok=True)
        
    def execute_code(self,
                    code: str,
                    timeout: int = 30) -> Tuple[bool, str, Any]:
        """Execute Python code and capture its output.
        
        Args:
            code: The Python code to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (success, output, result)
        """
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.working_dir,
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name
            
        try:
            # Execute the code in a separate process
            import subprocess
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                success = process.returncode == 0
                output = stdout if success else stderr
                
                # Try to parse the output as a Python literal
                try:
                    result = ast.literal_eval(output.strip())
                except (ValueError, SyntaxError):
                    result = output.strip()
                    
                return success, output, result
                
            except subprocess.TimeoutExpired:
                process.kill()
                return False, "Execution timed out", None
                
        except Exception as e:
            return False, str(e), None
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except OSError:
                pass
                
    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Python code for safety and correctness.
        
        Args:
            code: The Python code to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for potentially dangerous operations
        dangerous_operations = [
            "os.system",
            "subprocess.call",
            "subprocess.Popen",
            "eval",
            "exec",
            "__import__",
            "open",
            "file"
        ]
        
        try:
            tree = ast.parse(code)
            
            # Check for dangerous operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in dangerous_operations:
                            issues.append(f"Dangerous operation: {node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        if f"{node.func.value.id}.{node.func.attr}" in dangerous_operations:
                            issues.append(
                                f"Dangerous operation: {node.func.value.id}.{node.func.attr}"
                            )
                            
            # Check for syntax errors
            compile(code, "<string>", "exec")
            
            # Check for undefined variables
            undefined_vars = set()
            defined_vars = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        defined_vars.add(node.id)
                    elif isinstance(node.ctx, ast.Load):
                        if node.id not in defined_vars and node.id not in dir(__builtins__):
                            undefined_vars.add(node.id)
                            
            if undefined_vars:
                issues.append(f"Undefined variables: {', '.join(undefined_vars)}")
                
            return len(issues) == 0, issues
            
        except SyntaxError as e:
            return False, [f"Syntax error: {str(e)}"]
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
            
    def run_tests(self,
                 code: str,
                 test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run test cases against the code.
        
        Args:
            code: The Python code to test
            test_cases: List of test cases to run
            
        Returns:
            Test results
        """
        results = {
            "passed": 0,
            "failed": 0,
            "total": len(test_cases),
            "details": []
        }
        
        # Create a temporary module for the code
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.working_dir,
            delete=False
        ) as f:
            f.write(code)
            module_path = f.name
            
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location("test_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run each test case
            for i, test_case in enumerate(test_cases):
                test_result = {
                    "test_case": i + 1,
                    "passed": False,
                    "error": None
                }
                
                try:
                    # Get the function to test
                    func_name = test_case["function"]
                    func = getattr(module, func_name)
                    
                    # Run the function with test inputs
                    result = func(*test_case.get("args", []), **test_case.get("kwargs", {}))
                    
                    # Check the result
                    if "expected" in test_case:
                        if result == test_case["expected"]:
                            test_result["passed"] = True
                            results["passed"] += 1
                        else:
                            test_result["error"] = f"Expected {test_case['expected']}, got {result}"
                            results["failed"] += 1
                    else:
                        test_result["passed"] = True
                        results["passed"] += 1
                        
                except Exception as e:
                    test_result["error"] = str(e)
                    results["failed"] += 1
                    
                results["details"].append(test_result)
                
        except Exception as e:
            results["error"] = f"Test execution failed: {str(e)}"
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(module_path)
            except OSError:
                pass
                
        return results
        
    def generate_test_cases(self,
                           code: str,
                           num_cases: int = 5) -> List[Dict[str, Any]]:
        """Generate test cases for the code.
        
        Args:
            code: The Python code to generate tests for
            num_cases: Number of test cases to generate
            
        Returns:
            List of test cases
        """
        test_cases = []
        
        try:
            # Parse the code to find functions
            tree = ast.parse(code)
            functions = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ]
            
            for func in functions:
                # Generate test cases for each function
                for _ in range(num_cases):
                    test_case = {
                        "function": func.name,
                        "args": [],
                        "kwargs": {},
                        "expected": None
                    }
                    
                    # Generate random arguments based on function parameters
                    for arg in func.args.args:
                        if arg.arg != "self":
                            # Generate a random value based on the parameter name
                            if "int" in arg.arg or "num" in arg.arg:
                                test_case["args"].append(random.randint(1, 100))
                            elif "float" in arg.arg:
                                test_case["args"].append(random.uniform(0, 100))
                            elif "str" in arg.arg or "text" in arg.arg:
                                test_case["args"].append("".join(
                                    random.choices(string.ascii_letters, k=10)
                                ))
                            else:
                                test_case["args"].append(None)
                                
                    test_cases.append(test_case)
                    
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            
        return test_cases 