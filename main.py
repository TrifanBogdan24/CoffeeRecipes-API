from flask import Flask, jsonify, request, abort, Response, send_file
from http import HTTPStatus
import json
import os

webserver = Flask(__name__)

# Load the combined JSON data
RECIPES_FILE = "recipes.json"
with open(RECIPES_FILE, "r", encoding="utf-8") as f:
    recipes_data = json.load(f)

# Helper function to create arrays coffee sizes
def get_sizes_for_coffee(coffee):
    if "ingredients" in coffee:
        return list(coffee["ingredients"].keys())
    return []

# 0. / -> root endpoint (check connectivity)
@webserver.route("/", methods=["GET"])
def root_page():
    return Response(status=HTTPStatus.OK)

# 1. /coffee_recipes -> Returns all coffees with ingredients and recipe steps
@webserver.route("/coffee_recipes", methods=["GET"])
def coffee_recipes():
    return jsonify(recipes_data), 200

# 2. /coffees -> return all coffee names
@webserver.route("/coffees", methods=["GET"])
def coffee_names():
    names = [c["name"] for c in recipes_data]
    return jsonify(names), 200

# 3. /categories -> return all category names (standardized to lowercase)
@webserver.route("/categories", methods=["GET"])
def categories():
    cats = list(set(c["category"].lower() for c in recipes_data))
    return jsonify(cats), 200

# 4. /category/<category_name> -> coffee names under category
@webserver.route("/category/<category_name>", methods=["GET"])
def coffees_by_category(category_name):
    names = [c["name"] for c in recipes_data if c["category"].lower() == category_name.lower()]
    if not names:
        abort(404, description="Category not found")
    return jsonify(names), 200

# 5. /coffees/<coffee_name>/sizes -> list of sizes
@webserver.route("/coffees/<coffee_name>/sizes", methods=["GET"])
def coffee_sizes(coffee_name):
    coffee = next((c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()), None)
    if not coffee:
        abort(404, description="Coffee not found")
    sizes = get_sizes_for_coffee(coffee)
    return jsonify(sizes), 200

# 6. /coffees/<size_name>/<coffee_name>/ingredients -> return ingredients for specified size
@webserver.route("/coffees/<size_name>/<coffee_name>/ingredients", methods=["GET"])
def coffee_ingredients_size(coffee_name, size_name):
    coffee = next(
        (c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()),
        None
    )
    if not coffee:
        abort(404, description="Coffee not found")
    
    ingredients = coffee.get("ingredients", {}).get(size_name.lower())
    if not ingredients:
        abort(404, description="Size not available")
    
    return jsonify(ingredients), 200


# 7. /coffees/<coffee_name>/size/<size_name>/steps -> return recipe steps for coffee (same for all sizes)
@webserver.route("/coffees/<coffee_name>/steps", methods=["GET"])
def coffee_steps(coffee_name):
    coffee = next((c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()), None)
    if not coffee:
        abort(404, description="Coffee not found")
    steps = coffee.get("recipe_steps", [])
    return jsonify(steps), 200

# 8. /coffees/<coffee_name>/<size_name>/final_volume
@webserver.route("/coffees/<coffee_name>/<size_name>/final_volume", methods=["GET"])
def coffee_final_volume(coffee_name, size_name):
    # Find the coffee by name
    coffee = next(
        (c for c in recipes_data if c["name"].lower().replace(' ', '_') == coffee_name.lower()),
        None
    )
    if not coffee:
        abort(404, description="Coffee not found")
    
    # Get the final volume for the requested size
    final_volume = coffee.get("final_volume", {}).get(size_name.lower())
    if not final_volume:
        abort(404, description="Size not available or final volume not set")
    
    return jsonify({
        "final_volume": final_volume
    }), 200


# 9. /coffees/filter?category=&name=&size= -> flexible filtering
@webserver.route("/coffees/filter", methods=["GET"])
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
            if size.lower() in c.get("ingredients", {}):
                coffee_copy = c.copy()
                coffee_copy["ingredients"] = c["ingredients"][size.lower()]
                coffee_copy["size_selected"] = size.lower()
                filtered_size.append(coffee_copy)
        filtered = filtered_size

    if not filtered:
        abort(404, description="No matching coffees found")
    
    return jsonify(filtered), 200

# 10. /images/coffee_list/<coffee_name> -> get the picture of a coffee
@webserver.route('/images/coffee_list/<coffee_name>')
def get_coffee_img(coffee_name):
    image_path = f'images/coffee_list/{coffee_name}.jpeg'
    return send_file(image_path, mimetype='image/jpeg')



# 11. /images/<coffe_type>/<cup_size> -> get the picture of a cup size
@webserver.route('/images/<coffee_type>/<cup_size>')
def get_cup_img(coffee_type, cup_size):
    if coffee_type not in ['hot', 'cold']:
        abort(404, description=f"Invalid coffee type '{coffee_type}'. Expected either 'hot' or 'cold'")

    image_path = f'images/cup_sizes/{coffee_type}_coffees/{cup_size}.png'
    return send_file(image_path, mimetype='image/jpeg')



# Error handlers
@webserver.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

@webserver.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    webserver.run(debug=True, host='0.0.0.0')
