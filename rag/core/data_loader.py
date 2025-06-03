import json
import os
import importlib
import os
import json
import importlib
import traceback
from typing import List, Dict, Any

def load_raw_product_data(source_type: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Load raw product data from various sources.
    Currently supports JSON files.
    """
    if source_type == "JSON":
        filepath = kwargs.get("filepath")
        if not filepath:
            raise ValueError("Filepath must be provided for JSON data source.")
            
        if not os.path.exists(filepath):
            print(f"Error: JSON file {filepath} not found. Please check the path.")
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                
            # Check data structure and extract products
            if isinstance(loaded_data, dict) and "products" in loaded_data:
                data = loaded_data["products"]
            elif isinstance(loaded_data, list):
                data = loaded_data
            else:
                print(f"Warning: Unexpected data structure in {filepath}.")
                print(f"Data type: {type(loaded_data)}")
                if isinstance(loaded_data, dict):
                    print(f"Available keys: {list(loaded_data.keys())}")
                data = loaded_data  # Assume it's the data we want
                
            print(f"Successfully loaded {len(data)} products from JSON: {filepath}")
            return data
        except json.JSONDecodeError:
            print(f"Error: JSON file {filepath} contains invalid JSON.")
            return []
        except KeyError as e:
            print(f"Error: Could not find 'products' key in the JSON file: {e}")
            print("Available keys:", list(json.load(open(filepath, 'r')).keys()))
            return []
        except Exception as e:
            print(f"An unexpected error occurred while reading {filepath}: {e}")
            import traceback
            traceback.print_exc()
            return []
    else:
        raise ValueError(f"Unsupported data source type: {source_type}")

def load_skin_condition_profiles(module_name: str) -> Dict[str, str]:
    """
    Load skin condition profiles from a Python module.
    """
    try:
        module = importlib.import_module(module_name)
        profiles = getattr(module, "SKIN_CONDITION_PROFILES", {})
        print(f"Successfully loaded {len(profiles)} skin condition profiles from {module_name}")
        return profiles
    except ImportError:
        print(f"Error: Module {module_name} not found.")
        return {}
    except AttributeError:
        print(f"Error: SKIN_CONDITION_PROFILES not found in {module_name}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while loading skin condition profiles: {e}")
        return {}
