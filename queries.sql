-- База даних онлайн-магазину електроніки (SQLite)
-- Запуск: sqlite3 shop.db < queries.sql

PRAGMA foreign_keys = ON;

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

-- 1. Додавання продуктів
INSERT INTO products (name, category, price) VALUES
    ('Samsung Galaxy S24', 'смартфони', 32999.00),
    ('Apple iPhone 15', 'смартфони', 37999.00),
    ('Xiaomi Redmi Note 13', 'смартфони', 8999.00),
    ('Lenovo IdeaPad 5', 'ноутбуки', 28499.00),
    ('ASUS VivoBook 15', 'ноутбуки', 21999.00),
    ('Apple MacBook Air M2', 'ноутбуки', 47999.00),
    ('Apple iPad 10.9', 'планшети', 16999.00),
    ('Samsung Galaxy Tab S9', 'планшети', 29999.00),
    ('Sony WH-1000XM5', 'навушники', 13499.00),
    ('Apple Watch Series 9', 'смарт-годинники', 17999.00);

-- 2. Додавання клієнтів
INSERT INTO customers (first_name, last_name, email) VALUES
    ('Олена', 'Коваленко', 'olena.kovalenko@example.com'),
    ('Андрій', 'Шевченко', 'andrii.shevchenko@example.com'),
    ('Марія', 'Бондаренко', 'mariia.bondarenko@example.com'),
    ('Дмитро', 'Ткаченко', 'dmytro.tkachenko@example.com'),
    ('Ірина', 'Мельник', 'iryna.melnyk@example.com');

-- 3. Замовлення товарів
-- Клієнт і товар визначаються за email і назвою, тому запит не залежить від конкретних id
INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES
    ((SELECT customer_id FROM customers WHERE email = 'olena.kovalenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Samsung Galaxy S24'), 1, '2026-09-01'),
    ((SELECT customer_id FROM customers WHERE email = 'olena.kovalenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Sony WH-1000XM5'), 1, '2026-09-03'),
    ((SELECT customer_id FROM customers WHERE email = 'andrii.shevchenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Lenovo IdeaPad 5'), 1, '2026-09-05'),
    ((SELECT customer_id FROM customers WHERE email = 'andrii.shevchenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Xiaomi Redmi Note 13'), 2, '2026-09-07'),
    ((SELECT customer_id FROM customers WHERE email = 'andrii.shevchenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Apple iPad 10.9'), 1, '2026-09-10'),
    ((SELECT customer_id FROM customers WHERE email = 'mariia.bondarenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Apple iPhone 15'), 1, '2026-09-12'),
    ((SELECT customer_id FROM customers WHERE email = 'mariia.bondarenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Apple Watch Series 9'), 1, '2026-09-12'),
    ((SELECT customer_id FROM customers WHERE email = 'dmytro.tkachenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'ASUS VivoBook 15'), 2, '2026-09-15'),
    ((SELECT customer_id FROM customers WHERE email = 'dmytro.tkachenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Xiaomi Redmi Note 13'), 1, '2026-09-18'),
    ((SELECT customer_id FROM customers WHERE email = 'iryna.melnyk@example.com'),
     (SELECT product_id FROM products WHERE name = 'Samsung Galaxy Tab S9'), 1, '2026-09-20'),
    ((SELECT customer_id FROM customers WHERE email = 'iryna.melnyk@example.com'),
     (SELECT product_id FROM products WHERE name = 'Apple MacBook Air M2'), 1, '2026-09-22'),
    ((SELECT customer_id FROM customers WHERE email = 'olena.kovalenko@example.com'),
     (SELECT product_id FROM products WHERE name = 'Apple iPhone 15'), 1, '2026-09-25');

-- 4. Сумарний обсяг продажів
SELECT ROUND(COALESCE(SUM(o.quantity * p.price), 0), 2) AS total_sales
FROM orders AS o
INNER JOIN products AS p ON p.product_id = o.product_id;

-- 5. Кількість замовлень на кожного клієнта
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(o.order_id) AS orders_count
FROM customers AS c
INNER JOIN orders AS o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY orders_count DESC, c.customer_id;

-- 6. Середній чек замовлення
SELECT ROUND(AVG(o.quantity * p.price), 2) AS average_check
FROM orders AS o
INNER JOIN products AS p ON p.product_id = o.product_id;

-- 7. Найбільш популярна категорія товарів (за кількістю замовлень)
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
ORDER BY category;

-- 8. Загальна кількість товарів кожної категорії
SELECT category, COUNT(*) AS products_count
FROM products
GROUP BY category
ORDER BY products_count DESC, category;

-- 9. Оновлення цін: смартфони +10%
UPDATE products
SET price = ROUND(price * 1.10, 2)
WHERE category = 'смартфони';

SELECT product_id, name, category, price
FROM products
WHERE category = 'смартфони';
