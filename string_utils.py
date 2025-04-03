from fractions import Fraction

def clean_repr(obj, precise=False):
     """
     Recursively converts objects to a string representation
     with custom formatting for dictionaries, lists, and fractions.
     """
     if isinstance(obj, dict):
         return "{" + ", ".join(f"{k}: {clean_repr(v)}" for k, v in obj.items()) + "}"
     elif isinstance(obj, list):
         return "[" + ", ".join(clean_repr(v) for v in obj) + "]"
     elif isinstance(obj, Fraction):
         return f"{obj.numerator}/{obj.denominator}" if precise else format_float(float(obj))
     elif isinstance(obj, float):
         return format_float(obj)
     elif isinstance(obj, str):
         return obj  # Return strings without quotes
     else:
         return repr(obj)  # Default representation for other types

def format_float(value):
    """
    Format a floating-point number cleanly:
    - Remove unnecessary decimals and trailing zeros.
    - Keep precision up to meaningful digits.
    """
    if value.is_integer():
        return f"{int(value)}"  # Represent as an integer if no fractional part
    else:
        return f"{value:.6g}"  # Use general format with up to 6 significant digits
