import requests
import json
import os

# Adjust to Flask host/port
BASE_URL = "http://127.0.0.1:5000"
REF_DIR = "ref"

# Helper functions
def save_json(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {filename}")

def get_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed: {url} Status: {response.status_code}")
        return None

# 1. /coffee_recipes
coffee_recipes = get_json("/coffee_recipes")
if coffee_recipes:
    save_json(os.path.join(REF_DIR, "coffee_recipes.out.json"), coffee_recipes)

# 2. /coffees
coffees = get_json("/coffees")
if coffees:
    save_json(os.path.join(REF_DIR, "coffees.out.json"), coffees)

# 3. /categories
categories = get_json("/categories")
if categories:
    save_json(os.path.join(REF_DIR, "categories.out.json"), categories)

# 4. /category/<category_name>
if categories:
    for cat in categories:
        cat_endpoint = f"/category/{cat}"
        cat_data = get_json(cat_endpoint)
        if cat_data:
            save_json(os.path.join(REF_DIR, "categories", f"{cat}.out.json"), cat_data)

# 5. /coffees/<coffee_name>/sizes
if coffees:
    for coffee in coffees:
        coffee_norm = coffee.lower().replace(' ', '_')
        endpoint = f"/coffees/{coffee_norm}/sizes"
        sizes_data = get_json(endpoint)
        if sizes_data:
            save_json(os.path.join(REF_DIR, "coffee_sizes", f"{coffee_norm}.out.json"), sizes_data)

# 6. /coffees/<size_name>/<coffee_name>/ingredients
if coffees:
    for coffee in coffees:
        coffee_norm = coffee.lower().replace(' ', '_')
        # Load sizes from previous ref/coffee_sizes
        sizes_file = os.path.join(REF_DIR, "coffee_sizes", f"{coffee_norm}.out.json")
        if os.path.exists(sizes_file):
            with open(sizes_file, "r", encoding="utf-8") as f:
                sizes = json.load(f)
            for size in sizes:
                size_norm = str(size).lower()
                ingredients = get_json(f"/coffees/{size_norm}/{coffee_norm}/ingredients")
                if ingredients:
                    save_json(
                        os.path.join(REF_DIR, "coffee_ingredients", coffee_norm, f"{size_norm}.out.json"),
                        ingredients
                    )

# 7. /coffees/<coffee_name>/steps
coffees = get_json("/coffees")
if coffees:
    for coffee in coffees:
        coffee_norm = coffee.lower().replace(' ', '_')
        steps = get_json(f"/coffees/{coffee_norm}/steps")
        if steps:
            save_json(os.path.join(REF_DIR, "coffee_steps", f"{coffee_norm}.out.json"), steps)

# 8. /coffees/filter?category=&name=&size=
filters_dir = os.path.join(REF_DIR, "filters")
os.makedirs(filters_dir, exist_ok=True)

sample_filters = [
    {"category": "espresso"},
    {"category": "cold", "size": "medium"},
    {"name": "frappuccino"},
    {"category": "traditional", "name": "irish_coffee"},
    {"size": "small"}
]

for f in sample_filters:
    params = "&".join(f"{k}={v}" for k, v in f.items())
    endpoint = f"/coffees/filter?{params}"
    filter_data = get_json(endpoint)
    if filter_data:
        # Include final_volume if present
        for coffee in filter_data:
            size_selected = coffee.get("size_selected")
            if size_selected and "final_volume" in coffee:
                coffee["final_volume_for_size"] = coffee["final_volume"].get(size_selected)

        filter_name = "_".join([f"{k}-{v}" for k, v in f.items()])
        save_json(os.path.join(filters_dir, f"{filter_name}.out.json"), filter_data)
