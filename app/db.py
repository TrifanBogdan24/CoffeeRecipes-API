import MySQLdb
import json


RECIPES_FILE = "../recipes.json"
DB_USER = 'barista'
DB_PASSWD = 'LatteLounge@8am'
DB_NAME = 'CoffeeRecipeAPI'


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
