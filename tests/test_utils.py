"""
Utility functions for tests
Handles configuration loading from different execution contexts
"""

import json
import os


def load_config(filepath: str = 'config.json') -> dict:
    """Load config from JSON file, handling different execution contexts."""
    # Try multiple paths to support different execution contexts
    paths = [
        filepath,  # Relative path as-is
        os.path.join(os.path.dirname(__file__), '..', 'config', filepath),  # From tests/
        os.path.join(os.path.dirname(__file__), '..', filepath),  # From root
    ]
    
    for path in paths:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
    
    raise FileNotFoundError(f"Could not find {filepath} in any expected location")
