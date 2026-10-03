"""Робота з базою даних онлайн-магазину електроніки (SQLite)."""

import sqlite3
from datetime import date
from typing import Any, List, Optional, Sequence, Tuple

DEFAULT_DB_FILE = "shop.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""

# 1. Додавання продуктів
SQL_INSERT_PRODUCT = """
INSERT INTO products (name, category, price)
VALUES (?, ?, ?)
"""

# 2. Додавання клієнтів
SQL_INSERT_CUSTOMER = """
INSERT INTO customers (first_name, last_name, email)
VALUES (?, ?, ?)
"""

# 3. Замовлення товарів
SQL_INSERT_ORDER = """
INSERT INTO orders (customer_id, product_id, quantity, order_date)
VALUES (?, ?, ?, ?)
"""

# 3. Замовлення товарів (демо-дані: клієнт і товар визначаються за email і назвою)
SQL_INSERT_ORDER_BY_KEYS = """
INSERT INTO orders (customer_id, product_id, quantity, order_date)
VALUES (
    (SELECT customer_id FROM customers WHERE email = ?),
    (SELECT product_id FROM products WHERE name = ?),
    ?,
    ?
)
"""

# 4. Сумарний обсяг продажів
SQL_TOTAL_SALES = """
SELECT ROUND(COALESCE(SUM(o.quantity * p.price), 0), 2) AS total_sales
FROM orders AS o
INNER JOIN products AS p ON p.product_id = o.product_id
"""

# 5. Кількість замовлень на кожного клієнта
SQL_ORDERS_PER_CUSTOMER = """
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.order_id) AS orders_count
FROM customers AS c
INNER JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY orders_count DESC, c.customer_id
"""

# 6. Середній чек замовлення
SQL_AVERAGE_CHECK = """
SELECT ROUND(AVG(o.quantity * p.price), 2) AS average_check
FROM orders AS o
INNER JOIN products AS p ON p.product_id = o.product_id
"""

# 7. Найбільш популярна категорія товарів (за кількістю замовлень, з урахуванням рівних результатів)
SQL_MOST_POPULAR_CATEGORY = """
WITH category_orders AS (
    SELECT
        p.category,
        COUNT(o.order_id) AS orders_count,
        SUM(o.quantity) AS items_sold
    FROM orders AS o
    INNER JOIN products AS p ON p.product_id = o.product_id
    GROUP BY p.category
)
SELECT category, orders_count, items_sold
FROM category_orders
WHERE orders_count = (SELECT MAX(orders_count) FROM category_orders)
ORDER BY category
"""

# 8. Загальна кількість товарів кожної категорії
SQL_PRODUCTS_PER_CATEGORY = """
SELECT category, COUNT(*) AS products_count
FROM products
GROUP BY category
ORDER BY products_count DESC, category
"""

# 9. Оновлення цін
SQL_UPDATE_CATEGORY_PRICES = """
UPDATE products
SET price = ROUND(price * (1 + ? / 100.0), 2)
WHERE category = ?
"""

SQL_LIST_PRODUCTS = """
SELECT product_id, name, category, price
FROM products
ORDER BY product_id
"""

SQL_LIST_CUSTOMERS = """
SELECT customer_id, first_name, last_name, email
FROM customers
ORDER BY customer_id
"""

SQL_LIST_ORDERS = """
SELECT
    o.order_id,
    o.order_date,
    c.first_name || ' ' || c.last_name AS customer,
    p.name AS product,
    o.quantity,
    p.price,
    ROUND(o.quantity * p.price, 2) AS order_sum
FROM orders AS o
INNER JOIN customers AS c ON c.customer_id = o.customer_id
INNER JOIN products AS p ON p.product_id = o.product_id
ORDER BY o.order_id
"""

DEMO_PRODUCTS = [
    ("Samsung Galaxy S24", "смартфони", 32999.00),
    ("Apple iPhone 15", "смартфони", 37999.00),
    ("Xiaomi Redmi Note 13", "смартфони", 8999.00),
    ("Lenovo IdeaPad 5", "ноутбуки", 28499.00),
    ("ASUS VivoBook 15", "ноутбуки", 21999.00),
    ("Apple MacBook Air M2", "ноутбуки", 47999.00),
    ("Apple iPad 10.9", "планшети", 16999.00),
    ("Samsung Galaxy Tab S9", "планшети", 29999.00),
    ("Sony WH-1000XM5", "навушники", 13499.00),
    ("Apple Watch Series 9", "смарт-годинники", 17999.00),
]

DEMO_CUSTOMERS = [
    ("Олена", "Коваленко", "olena.kovalenko@example.com"),
    ("Андрій", "Шевченко", "andrii.shevchenko@example.com"),
    ("Марія", "Бондаренко", "mariia.bondarenko@example.com"),
    ("Дмитро", "Ткаченко", "dmytro.tkachenko@example.com"),
    ("Ірина", "Мельник", "iryna.melnyk@example.com"),
]

DEMO_ORDERS = [
    ("olena.kovalenko@example.com", "Samsung Galaxy S24", 1, "2026-09-01"),
    ("olena.kovalenko@example.com", "Sony WH-1000XM5", 1, "2026-09-03"),
    ("andrii.shevchenko@example.com", "Lenovo IdeaPad 5", 1, "2026-09-05"),
    ("andrii.shevchenko@example.com", "Xiaomi Redmi Note 13", 2, "2026-09-07"),
    ("andrii.shevchenko@example.com", "Apple iPad 10.9", 1, "2026-09-10"),
    ("mariia.bondarenko@example.com", "Apple iPhone 15", 1, "2026-09-12"),
    ("mariia.bondarenko@example.com", "Apple Watch Series 9", 1, "2026-09-12"),
    ("dmytro.tkachenko@example.com", "ASUS VivoBook 15", 2, "2026-09-15"),
    ("dmytro.tkachenko@example.com", "Xiaomi Redmi Note 13", 1, "2026-09-18"),
    ("iryna.melnyk@example.com", "Samsung Galaxy Tab S9", 1, "2026-09-20"),
    ("iryna.melnyk@example.com", "Apple MacBook Air M2", 1, "2026-09-22"),
    ("olena.kovalenko@example.com", "Apple iPhone 15", 1, "2026-09-25"),
]

QueryResult = Tuple[List[str], List[Tuple[Any, ...]]]


class ShopDatabase:
    """Обгортка над підключенням sqlite3 з методами для всіх запитів завдання.

    Зміни не фіксуються автоматично: після модифікуючих операцій відкрита
    транзакція чекає на commit() або rollback(), щоб користувач сам вирішив,
    чи зберігати зміни.
    """

    def __init__(self, path: str = DEFAULT_DB_FILE) -> None:
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA)

    def _query(self, sql: str, params: Sequence[Any] = ()) -> QueryResult:
        cursor = self.connection.execute(sql, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

    def _scalar(self, sql: str, params: Sequence[Any] = ()) -> Any:
        row = self.connection.execute(sql, params).fetchone()
        return row[0] if row else None

    def add_product(self, name: str, category: str, price: float) -> int:
        cursor = self.connection.execute(SQL_INSERT_PRODUCT, (name, category, price))
        return cursor.lastrowid

    def add_customer(self, first_name: str, last_name: str, email: str) -> int:
        cursor = self.connection.execute(SQL_INSERT_CUSTOMER, (first_name, last_name, email))
        return cursor.lastrowid

    def add_order(
        self,
        customer_id: int,
        product_id: int,
        quantity: int,
        order_date: Optional[str] = None,
    ) -> int:
        if quantity <= 0:
            raise ValueError("Кількість товару має бути більшою за 0.")
        if order_date is None:
            order_date = date.today().isoformat()
        else:
            order_date = date.fromisoformat(order_date).isoformat()
        cursor = self.connection.execute(
            SQL_INSERT_ORDER, (customer_id, product_id, quantity, order_date)
        )
        return cursor.lastrowid

    def total_sales(self) -> float:
        return self._scalar(SQL_TOTAL_SALES)

    def orders_per_customer(self) -> QueryResult:
        return self._query(SQL_ORDERS_PER_CUSTOMER)

    def average_check(self) -> Optional[float]:
        return self._scalar(SQL_AVERAGE_CHECK)

    def most_popular_category(self) -> QueryResult:
        return self._query(SQL_MOST_POPULAR_CATEGORY)

    def products_per_category(self) -> QueryResult:
        return self._query(SQL_PRODUCTS_PER_CATEGORY)

    def update_category_prices(self, category: str = "смартфони", percent: float = 10.0) -> int:
        cursor = self.connection.execute(SQL_UPDATE_CATEGORY_PRICES, (percent, category))
        return cursor.rowcount

    def list_products(self) -> QueryResult:
        return self._query(SQL_LIST_PRODUCTS)

    def list_customers(self) -> QueryResult:
        return self._query(SQL_LIST_CUSTOMERS)

    def list_orders(self) -> QueryResult:
        return self._query(SQL_LIST_ORDERS)

    def is_empty(self) -> bool:
        products = self._scalar("SELECT COUNT(*) FROM products")
        customers = self._scalar("SELECT COUNT(*) FROM customers")
        orders = self._scalar("SELECT COUNT(*) FROM orders")
        return products == 0 and customers == 0 and orders == 0

    def seed_demo_data(self) -> bool:
        """Заповнює порожню базу демо-даними. Повертає False, якщо дані вже є."""
        if not self.is_empty():
            return False
        self.connection.executemany(SQL_INSERT_PRODUCT, DEMO_PRODUCTS)
        self.connection.executemany(SQL_INSERT_CUSTOMER, DEMO_CUSTOMERS)
        self.connection.executemany(SQL_INSERT_ORDER_BY_KEYS, DEMO_ORDERS)
        return True

    def has_unsaved_changes(self) -> bool:
        return self.connection.in_transaction

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()
