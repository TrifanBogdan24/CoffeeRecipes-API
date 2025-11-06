# CoffeeRecipes API

| Endpoint | Description |
|----------|-------------|
| `GET /coffee_recipes` | Returns all coffees with their ingredients, sizes, final volume, notes, and recipe steps. |
| `GET /coffees` | Returns a list of all coffee names. |
| `GET /categories` | Returns a list of all category names. |
| `GET /category/<category_name>` | Returns all coffee names under the specified category. |
| `GET /coffees/<coffee_name>/sizes` | Returns a list of available sizes for the specified coffee. |
| `GET /coffees/<coffee_name>/steps` | Returns the recipe steps for the specified coffee (same for all sizes). |
| `GET /coffees/<coffee_name>/size/<size_name>/ingredients` | Returns the ingredients for the specified coffee and size. |
| `GET /coffees/filter?category=&name=&size=` | Flexible filtering endpoint: can filter coffees by category, name, and/or size. |
