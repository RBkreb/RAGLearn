"""Math tools for LLM agent."""

from langchain_core.tools import tool


@tool("add", description="Add two numbers. Use this when the user asks to calculate a sum or add values together. Input: two integers a and b. Output: their sum.")
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Sum of a and b.
    """
    return a + b


@tool("subtract", description="Subtract the second number from the first. Use this when the user asks to calculate a difference or subtract values. Input: two integers a (minuend) and b (subtrahend). Output: a minus b.")
def subtract(a: int, b: int) -> int:
    """Subtract b from a.

    Args:
        a: First number (minuend).
        b: Second number (subtrahend).

    Returns:
        Difference of a and b.
    """
    return a - b


@tool("multiply", description="Multiply two numbers. Use this when the user asks to calculate a product or multiply values together. Input: two integers a and b. Output: their product.")
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Product of a and b.
    """
    return a * b


@tool("divide", description="Divide the first number by the second. Use this when the user asks to calculate a quotient or divide values. Input: two numbers a (dividend) and b (divisor, must be non-zero). Output: a divided by b. Raises an error if dividing by zero.")
def divide(a: int, b: int) -> float:
    """Divide a by b.

    Args:
        a: Dividend.
        b: Divisor (must be non-zero).

    Returns:
        Quotient of a divided by b.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b