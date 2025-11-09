from flask import Flask, jsonify, request, abort, Response, send_file
from http import HTTPStatus
import json
import os
import MySQLdb

RECIPES_FILE = "recipes.json"
DB_USER = 'barista'
DB_PASSWD = 'LatteLounge@8am'
DB_NAME = 'CoffeeRecipeAPI'

webserver = Flask(__name__)

def connect_db():
    # Connect to DB
    return MySQLdb.connect(
        host="localhost",
        user=DB_USER,
        password=DB_PASSWD,
        database=DB_NAME
    )


def load_recipes():
    conn = connect_db()
    cursor = conn.cursor()

    # Clear all tables (fresh start)
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE ingredients;")
    cursor.execute("TRUNCATE TABLE steps;")
    cursor.execute("TRUNCATE TABLE coffee_sizes;")
    cursor.execute("TRUNCATE TABLE coffees;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # Load JSON
    with open(RECIPES_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    for recipe in recipes:
        # Insert coffee
        cursor.execute(
            "INSERT INTO coffees (category, name, notes) VALUES (%s, %s, %s)",
            (recipe["category"], recipe["name"], recipe.get("notes", ""))
        )
        coffee_id = cursor.lastrowid

        # Insert coffee sizes
        for size, final_volume in recipe.get("final_volume", {}).items():
            cursor.execute(
                "INSERT INTO coffee_sizes (coffee_id, size, final_volume) VALUES (%s, %s, %s)",
                (coffee_id, size, final_volume)
            )

        # Insert ingredients
        for size, ingredients in recipe.get("ingredients", {}).items():
            for ingredient, quantity in ingredients.items():
                cursor.execute(
                    "INSERT INTO ingredients (coffee_id, size, ingredient, quantity) VALUES (%s, %s, %s, %s)",
                    (coffee_id, size, ingredient, quantity)
                )

        # Insert steps
        for step_number, step in recipe.get("steps", {}).items():
            cursor.execute(
                "INSERT INTO steps (coffee_id, step_number, title, description) VALUES (%s, %s, %s, %s)",
                (coffee_id, int(step_number), step.get("title", ""), step.get("description", ""))
            )

    conn.commit()
    cursor.close()
    conn.close()
    print("Database loaded successfully!")



def normalize_name(name):
    return name.lower().replace(' ', '_')


def get_coffee_by_name(coffee_name):
    conn = connect_db()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM coffees WHERE LOWER(REPLACE(name,' ', '_')) = %s", (normalize_name(coffee_name),))
    coffee = cursor.fetchone()
    cursor.close()
    conn.close()
    return coffee

def get_sizes_for_coffee(coffee_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT size FROM coffee_sizes WHERE coffee_id=%s", (coffee_id,))
    sizes = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return sizes


def get_ingredients(coffee_id, size):
    conn = connect_db()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT ingredient, quantity 
        FROM ingredients 
        WHERE coffee_id=%s AND LOWER(size)=%s
    """, (coffee_id, size.lower()))
    result = {row['ingredient']: row['quantity'] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return result

def get_steps(coffee_id):
    conn = connect_db()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT step_number, title, description FROM steps WHERE coffee_id=%s ORDER BY step_number", (coffee_id,))
    steps = {str(row['step_number']): {'title': row['title'], 'description': row['description']} for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return steps

def get_final_volume(coffee_id, size):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT final_volume FROM coffee_sizes WHERE coffee_id=%s AND LOWER(size)=%s", (coffee_id, size.lower()))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None



# 0. /api -> root endpoint (check connectivity)
@webserver.route("/api", methods=["GET"])
def root_page():
    return "", HTTPStatus.OK

# 1. /api/coffee_recipes -> Returns all coffees with ingredients and recipe steps
@webserver.route("/api/coffee_recipes", methods=["GET"])
def coffee_recipes():
    conn = connect_db()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM coffees")
    coffees = cursor.fetchall()
    all_recipes = []

    for coffee in coffees:
        coffee_id = coffee['id']
        sizes = get_sizes_for_coffee(coffee_id)
        ingredients = {size: get_ingredients(coffee_id, size) for size in sizes}
        final_volumes = {}
        conn2 = connect_db()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT size, final_volume FROM coffee_sizes WHERE coffee_id=%s", (coffee_id,))
        for row in cursor2.fetchall():
            final_volumes[row[0]] = row[1]
        cursor2.close()
        conn2.close()
        steps = get_steps(coffee_id)
        recipe = {
            "category": coffee['category'],
            "name": coffee['name'],
            "notes": coffee.get('notes', ''),
            "ingredients": ingredients,
            "final_volume": final_volumes,
            "steps": steps
        }
        all_recipes.append(recipe)
    cursor.close()
    conn.close()
    return jsonify(all_recipes), 200


# 2. /api/coffees -> return all coffee names
@webserver.route("/api/coffees", methods=["GET"])
def coffee_names():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM coffees")
    names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(names), 200

# 3. /api/categories -> return all category names (standardized to lowercase)
@webserver.route("/api/categories", methods=["GET"])
def categories():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT LOWER(category) FROM coffees")
    cats = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(cats), 200

# 4. /api//category/<category_name> -> coffee names under category
@webserver.route("/api/category/<category_name>", methods=["GET"])
def coffees_by_category(category_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM coffees WHERE LOWER(category)=%s", (category_name.lower(),))
    names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    if not names:
        abort(404, description="Category not found")
    return jsonify(names), 200

# 5. /api/coffees/<coffee_name>/sizes -> list of sizes
@webserver.route("/api/coffees/<coffee_name>/sizes", methods=["GET"])
def coffee_sizes(coffee_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    sizes = get_sizes_for_coffee(coffee['id'])
    return jsonify(sizes), 200

# 6. /api/coffees/<size_name>/<coffee_name>/ingredients -> return ingredients for specified size
@webserver.route("/api/coffees/<size_name>/<coffee_name>/ingredients", methods=["GET"])
def coffee_ingredients_size(coffee_name, size_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    ingredients = get_ingredients(coffee['id'], size_name)
    if not ingredients:
        abort(404, description="Size not available")
    return jsonify(ingredients), 200


# 7. /api/coffees/<coffee_name>/steps -> return recipe steps for coffee (same for all sizes)
@webserver.route("/api/coffees/<coffee_name>/steps", methods=["GET"])
def coffee_steps(coffee_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    steps = get_steps(coffee['id'])
    return jsonify(steps), 200

# 8. /api/coffees/<coffee_name>/<size_name>/final_volume
@webserver.route("/api/coffees/<coffee_name>/<size_name>/final_volume", methods=["GET"])
def coffee_final_volume(coffee_name, size_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    final_volume = get_final_volume(coffee['id'], size_name)
    if not final_volume:
        abort(404, description="Size not available or final volume not set")
    return jsonify({"final_volume": final_volume}), 200


# 9. /api/coffees/filter?category=&name=&size= -> flexible filtering
@webserver.route("/api/coffees/filter", methods=["GET"])
def filter_coffees():
    category = request.args.get("category")
    name = request.args.get("name")
    size = request.args.get("size")

    conn = connect_db()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    query = "SELECT * FROM coffees WHERE 1=1"
    params = []

    if category:
        query += " AND LOWER(category)=%s"
        params.append(category.lower())
    if name:
        query += " AND LOWER(REPLACE(name,' ', '_'))=%s"
        params.append(normalize_name(name))

    cursor.execute(query, params)
    coffees = cursor.fetchall()
    cursor.close()
    conn.close()

    if size:
        filtered = []
        for coffee in coffees:
            ing = get_ingredients(coffee['id'], size)
            if ing:
                coffee_copy = dict(coffee)
                coffee_copy['ingredients'] = ing
                coffee_copy['size_selected'] = size.lower()
                filtered.append(coffee_copy)
        coffees = filtered

    if not coffees:
        abort(404, description="No matching coffees found")
    return jsonify(coffees), 200

# 10. /api/images/coffee_list/<coffee_name> -> get the picture of a coffee
@webserver.route('/api/images/coffee_list/<coffee_name>')
def get_coffee_img(coffee_name):
    image_path = f'images/coffee_list/{coffee_name}.jpeg'
    return send_file(image_path, mimetype='image/jpeg')



# 11. /api/images/<coffe_type>/<cup_size> -> get the picture of a cup size
@webserver.route('/api/images/<coffee_type>/<cup_size>')
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
    load_recipes()
    webserver.run(debug=True, host='0.0.0.0')
