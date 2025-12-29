"""
Calculator tool for mathematical computations.
"""

import re
from typing import Any, Dict
from .base import Tool, ToolResult


class CalculatorTool(Tool):
    """
    Calculator tool that can perform mathematical calculations.
    Uses Python's eval with restricted globals for safety.
    """
    
    def get_name(self) -> str:
        return "calculator"
    
    def get_description(self) -> str:
        return (
            "Performs mathematical calculations. "
            "Supports basic arithmetic (+, -, *, /), exponents (**), "
            "and common math functions (abs, round, min, max). "
            "Use this whenever you need to compute numerical values."
        )
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 ** 2', 'round(3.14159, 2)')"
                }
            },
            "required": ["expression"]
        }
    
    async def execute(self, expression: str, **kwargs) -> ToolResult:
        """
        Execute a mathematical expression safely.
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            ToolResult with the calculation result or error
        """
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Only allow safe characters
            if not re.match(r'^[0-9+\-*/(). ,]+$', expression.replace('**', '').replace('abs', '').replace('round', '').replace('min', '').replace('max', '')):
                return ToolResult(
                    success=False,
                    error="Expression contains invalid characters. Only numbers and basic operators allowed."
                )
            
            # Safe evaluation with restricted globals
            safe_globals = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
            }
            
            result = eval(expression, safe_globals, {})
            
            return ToolResult(
                success=True,
                result=str(result),
                metadata={"expression": expression}
            )
            
        except ZeroDivisionError:
            return ToolResult(
                success=False,
                error="Cannot divide by zero"
            )
        except SyntaxError:
            return ToolResult(
                success=False,
                error="Invalid mathematical expression"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}"
            )
