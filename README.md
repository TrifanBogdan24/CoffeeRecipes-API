# CoffeeRecipes API

| Endpoint | Description |
|----------|-------------|
| `GET /coffee_recipes` | Returns all coffees with their ingredients (for all sizes), final volumes, notes, and recipe steps. Ingredients now include units (e.g., `"30ml"`) instead of numeric values. |
| `GET /coffees` | Returns a list of all coffee names. |
| `GET /categories` | Returns a list of all category names (standardized to lowercase). |
| `GET /category/<category_name>` | Returns all coffee names under the specified category. |
| `GET /coffees/<coffee_name>/sizes` | Returns a list of available sizes (`small`, `medium`, `large`) for the specified coffee. |
| `GET /coffees/<coffee_name>/steps` | Returns the recipe steps for the specified coffee (same for all sizes). |
| `GET /coffees/<size_name>/<coffee_name>/ingredients` | Returns the ingredients for the specified coffee and size. Ingredients values are strings including units (e.g., `"30ml"`, `"7g"`). |
| `GET /coffees/<size_name>/<coffee_name>/final_volume` | Returns volume of the querried drink. |
| `GET /coffees/filter?category=&name=&size=` | Flexible filtering endpoint. Returns coffees filtered by category, name, and/or size. When filtering by size, the response includes only the ingredients for that size and the corresponding `final_volume`. Also includes `size_selected` field for clarity. |



## SQL | MariaDB

```sh
sudo mariadb
```

One-time setup (for creating new user and database):
```sql
MariaDB [(none)]> CREATE USER 'barista'@'localhost' IDENTIFIED BY  'LatteLounge@8am';

MariaDB [(none)]> DROP DATABASE IF EXISTS CoffeeRecipeAPI;
MariaDB [(none)]> CREATE DATABASE CoffeeRecipeAPI;

MariaDB [(none)]> GRANT ALL PRIVILEGES ON CoffeeRecipeAPI.* TO 'barista'@'localhost';
MariaDB [(none)]> FLUSH PRIVILEGES;

MariaDB [(none)]> exit
```


```sh
% mariadb -u barista -p                
Enter password: LatteLounge@8am
```


```sql
MariaDB [(none)]> USE CoffeeRecipeAPI;
MariaDB [CoffeeRecipeAPI]>
```



```sql
CREATE TABLE IF NOT EXISTS coffees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS coffee_sizes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coffee_id INT NOT NULL,
    size TEXT NOT NULL,
    final_volume TEXT,
    FOREIGN KEY (coffee_id) REFERENCES coffees(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coffee_id INT NOT NULL,
    size TEXT NOT NULL,
    ingredient TEXT NOT NULL,
    quantity TEXT,
    FOREIGN KEY (coffee_id) REFERENCES coffees(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coffee_id INT NOT NULL,
    step_number INT NOT NULL,
    title TEXT,
    description TEXT,
    FOREIGN KEY (coffee_id) REFERENCES coffees(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

```