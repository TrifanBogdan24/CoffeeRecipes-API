from flask import Blueprint, jsonify, request, abort, send_file
from http import HTTPStatus
import socket
import qrcode
import io
from .db import *

web_api = Blueprint("web_api", __name__)



# 0. /api -> root endpoint (check connectivity)
@web_api.route("/api", methods=["GET"])
def root_page():
    return "", HTTPStatus.OK

# 1. /api/coffee_recipes -> Returns all coffees with ingredients and recipe steps
@web_api.route("/api/coffee_recipes", methods=["GET"])
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
@web_api.route("/api/coffees", methods=["GET"])
def coffee_names():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM coffees")
    names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(names), 200

# 3. /api/categories -> return all category names (standardized to lowercase)
@web_api.route("/api/categories", methods=["GET"])
def categories():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT LOWER(category) FROM coffees")
    cats = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(cats), 200

# 4. /api//category/<category_name> -> coffee names under category
@web_api.route("/api/category/<category_name>", methods=["GET"])
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
@web_api.route("/api/coffees/<coffee_name>/sizes", methods=["GET"])
def coffee_sizes(coffee_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    sizes = get_sizes_for_coffee(coffee['id'])
    return jsonify(sizes), 200

# 6. /api/coffees/<size_name>/<coffee_name>/ingredients -> return ingredients for specified size
@web_api.route("/api/coffees/<size_name>/<coffee_name>/ingredients", methods=["GET"])
def coffee_ingredients_size(coffee_name, size_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    ingredients = get_ingredients(coffee['id'], size_name)
    if not ingredients:
        abort(404, description="Size not available")
    return jsonify(ingredients), 200


# 7. /api/coffees/<coffee_name>/steps -> return recipe steps for coffee (same for all sizes)
@web_api.route("/api/coffees/<coffee_name>/steps", methods=["GET"])
def coffee_steps(coffee_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    steps = get_steps(coffee['id'])
    return jsonify(steps), 200

# 8. /api/coffees/<coffee_name>/<size_name>/final_volume
@web_api.route("/api/coffees/<coffee_name>/<size_name>/final_volume", methods=["GET"])
def coffee_final_volume(coffee_name, size_name):
    coffee = get_coffee_by_name(coffee_name)
    if not coffee:
        abort(404, description="Coffee not found")
    final_volume = get_final_volume(coffee['id'], size_name)
    if not final_volume:
        abort(404, description="Size not available or final volume not set")
    return jsonify({"final_volume": final_volume}), 200


# 9. /api/coffees/filter?category=&name=&size= -> flexible filtering
@web_api.route("/api/coffees/filter", methods=["GET"])
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
@web_api.route('/api/images/coffee_list/<coffee_name>')
def get_coffee_img(coffee_name):
    image_path = f'../images/coffee_list/{coffee_name}.jpeg'
    return send_file(image_path, mimetype='image/jpeg')


# 11. /api/images/<coffe_type>/<cup_size> -> get the picture of a cup size
@web_api.route('/api/images/<coffee_type>/<cup_size>')
def get_cup_img(coffee_type, cup_size):
    if coffee_type not in ['hot', 'cold']:
        abort(404, description=f"Invalid coffee type '{coffee_type}'. Expected either 'hot' or 'cold'")

    image_path = f'../images/cup_sizes/{coffee_type}_coffees/{cup_size}.png'
    return send_file(image_path, mimetype='image/jpeg')


# Error handlers
@web_api.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

@web_api.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500




def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
    
@web_api.route("/api/server_qr", methods=["GET"])
def server_qr():
    ip = get_local_ip()
    port = "5000"
    
    server_url = f"http://{ip}:{port}"
    
    # Generare QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(server_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Trimitem imaginea direct in stream HTTP
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')