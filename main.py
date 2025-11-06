from flask import Flask, jsonify, request, abort
import json
import os

app = Flask(__name__)

# Load the combined JSON data
RECIPES_FILE = "recipes.json"
with open(RECIPES_FILE, "r", encoding="utf-8") as f:
    recipes_data = json.load(f)

# Helper function to create arrays coffee sizes
def get_sizes_for_coffee(coffee):
    if coffee.get("size"):
        return [coffee["size"]]
    elif coffee.get("sizes"):
        return list(coffee["sizes"].keys())
    else:
        return []

# 1. /coffee_recipes -> Returns all coffees with ingredients and recipe steps
@app.route("/coffee_recipes", methods=["GET"])
def coffee_recipes():
    return jsonify(recipes_data), 200

# 2. /coffees -> return all coffee names
@app.route("/coffees", methods=["GET"])
def coffee_names():
    names = [c["name"] for c in recipes_data]
    return jsonify(names), 200

# 3. /categories -> return all category names (standardized to lowercase)
@app.route("/categories", methods=["GET"])
def categories():
    cats = list(set(c["category"].lower() for c in recipes_data))
    return jsonify(cats), 200

# 4. /category/<category_name> -> coffee names under category
@app.route("/category/<category_name>", methods=["GET"])
def coffees_by_category(category_name):
    names = [c["name"] for c in recipes_data if c["category"].lower() == category_name.lower()]
    if not names:
        abort(404, description="Category not found")
    return jsonify(names), 200

# 5. /coffees/<coffee_name>/sizes -> list of sizes
@app.route("/coffees/<coffee_name>/sizes", methods=["GET"])
def coffee_sizes(coffee_name):
    coffee = next((c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()), None)
    if not coffee:
        abort(404, description="Coffee not found")
    sizes = get_sizes_for_coffee(coffee)
    return jsonify(sizes), 200

# 6. /coffees/<coffee_name>/size/<size_name>/ingredients -> return ingredients for specified size
@app.route("/coffees/<coffee_name>/size/<size_name>/ingredients", methods=["GET"])
def coffee_ingredients_size(coffee_name, size_name):
    coffee = next((c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()), None)
    if not coffee:
        abort(404, description="Coffee not found")
    
    if coffee.get("size") and coffee["size"].lower() == size_name.lower():
        ingredients = coffee.get("ingredients", {})
    elif coffee.get("sizes") and size_name.lower() in coffee["sizes"]:
        ingredients = coffee["sizes"][size_name.lower()]
    else:
        abort(404, description="Size not available")
    
    return jsonify(ingredients), 200

# 7. /coffees/<coffee_name>/size/<size_name>/steps -> return recipe steps for coffee (same for all sizes)
@app.route("/coffees/<coffee_name>/steps", methods=["GET"])
def coffee_steps(coffee_name):
    coffee = next((c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()), None)
    if not coffee:
        abort(404, description="Coffee not found")
    steps = coffee.get("recipe_steps", [])
    return jsonify(steps), 200

# 8. /coffees/filter?category=&name=&size= -> flexible filtering
@app.route("/coffees/filter", methods=["GET"])
def filter_coffees():
    category = request.args.get("category")
    name = request.args.get("name")
    size = request.args.get("size")
    
    filtered = recipes_data

    if category:
        filtered = [c for c in filtered if c["category"].lower() == category.lower()]
    if name:
        filtered = [c for c in filtered if c["name"].lower().replace(' ', '_') == name.lower()]
    if size:
        filtered_size = []
        for c in filtered:
            if c.get("size") and c["size"].lower() == size.lower():
                filtered_size.append(c)
            elif c.get("sizes") and size.lower() in c["sizes"]:
                coffee_copy = c.copy()
                coffee_copy["ingredients"] = c["sizes"][size.lower()]
                coffee_copy["size_selected"] = size.lower()
                filtered_size.append(coffee_copy)
        filtered = filtered_size

    if not filtered:
        abort(404, description="No matching coffees found")
    
    return jsonify(filtered), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
