"""
Example Custom Tools for DeepAgent Server

Add your custom tools here using the @tool decorator from LangChain.
The server will automatically load and make them available to the agent.

Guidelines:
1. Use type hints for all parameters
2. Provide clear, concise docstrings
3. Keep tool descriptions under 2 lines
4. Return strings or simple JSON-serializable types
"""

from langchain_core.tools import tool
from typing import Optional
import math


@tool
def calculator(a: float, b: float, operation: str = "add") -> float:
    """
    Perform basic arithmetic operations.
    
    Args:
        a: First number
        b: Second number
        operation: Operation to perform (add, subtract, multiply, divide)
    
    Returns:
        Result of the operation
    """
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: Division by zero"
    }
    
    result = operations.get(operation, "Error: Unknown operation")
    return result


@tool
def calculate_percentage(value: float, percentage: float) -> float:
    """
    Calculate percentage of a value.
    
    Args:
        value: The base value
        percentage: The percentage to calculate
    
    Returns:
        The calculated percentage
    """
    return (value * percentage) / 100


@tool
def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert temperature between Celsius, Fahrenheit, and Kelvin.
    
    Args:
        value: Temperature value
        from_unit: Source unit (C, F, K)
        to_unit: Target unit (C, F, K)
    
    Returns:
        Converted temperature
    """
    from_unit = from_unit.upper()
    to_unit = to_unit.upper()
    
    # Convert to Celsius first
    if from_unit == "F":
        celsius = (value - 32) * 5/9
    elif from_unit == "K":
        celsius = value - 273.15
    else:
        celsius = value
    
    # Convert from Celsius to target
    if to_unit == "F":
        return celsius * 9/5 + 32
    elif to_unit == "K":
        return celsius + 273.15
    else:
        return celsius


@tool
def text_statistics(text: str) -> dict:
    """
    Calculate statistics about a text string.
    
    Args:
        text: The text to analyze
    
    Returns:
        Dictionary with character count, word count, and sentence count
    """
    import re
    
    char_count = len(text)
    word_count = len(text.split())
    sentence_count = len(re.split(r'[.!?]+', text))
    
    return {
        "characters": char_count,
        "words": word_count,
        "sentences": sentence_count,
        "avg_word_length": round(char_count / word_count, 2) if word_count > 0 else 0
    }


@tool
def generate_uuid() -> str:
    """Generate a random UUID."""
    import uuid
    return str(uuid.uuid4())


@tool
def encode_base64(text: str) -> str:
    """
    Encode text to base64.
    
    Args:
        text: Text to encode
    
    Returns:
        Base64 encoded string
    """
    import base64
    return base64.b64encode(text.encode()).decode()


@tool
def decode_base64(encoded: str) -> str:
    """
    Decode base64 to text.
    
    Args:
        encoded: Base64 encoded string
    
    Returns:
        Decoded text
    """
    import base64
    try:
        return base64.b64decode(encoded.encode()).decode()
    except Exception as e:
        return f"Error decoding: {str(e)}"


@tool
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
    
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)


@tool
def json_formatter(json_string: str, indent: int = 2) -> str:
    """
    Format JSON string with proper indentation.
    
    Args:
        json_string: JSON string to format
        indent: Number of spaces for indentation
    
    Returns:
        Formatted JSON string
    """
    import json
    try:
        obj = json.loads(json_string)
        return json.dumps(obj, indent=indent)
    except Exception as e:
        return f"Error formatting JSON: {str(e)}"


# Add your own custom tools below!
# Example template:
"""
@tool
def my_custom_tool(param1: str, param2: int) -> str:
    '''
    Brief description of what this tool does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
    
    Returns:
        Description of return value
    '''
    # Your implementation here
    return "result"
"""