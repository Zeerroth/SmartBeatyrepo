import requests
import json
import os
def get_products():
    # Check if the cache file exists
    if os.path.exists('product_cache.json'):
        print("Loading data from cache...")
        with open('product_cache.json', 'r') as f:
            return json.load(f)
    else:
        # Fetch data from the API if cache does not exist
        print("Fetching data from API...")
        response = requests.get("https://api.inventra.ca/api/Product/getAllProducts")
        if response.status_code == 200:
            data = response.json()
            # Cache the data for future use
            with open('product_cache.json', 'w') as f:
                json.dump(data, f)
            return data
        return {"products": []}
    

if __name__ == "__main__":
    get_products()