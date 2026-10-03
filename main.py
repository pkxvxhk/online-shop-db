"""Інтерфейс командного рядка для бази даних онлайн-магазину електроніки."""

import argparse
import sqlite3
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from database import DEFAULT_DB_FILE, ShopDatabase

YES_ANSWERS = {"т", "так", "y", "yes", "д", "да"}
NO_ANSWERS = {"н", "ні", "n", "no", "нет"}

MENU = """
========== Онлайн-магазин електроніки ==========
 1. Додати товар
 2. Додати клієнта
 3. Створити замовлення
 4. Загальний обсяг продажів
 5. Кількість замовлень кожного клієнта
 6. Середній чек замовлення
 7. Найбільш популярна категорія товарів
 8. Кількість товарів у кожній категорії
 9. Оновити ціни категорії (за замовчуванням: смартфони +10%)
10. Переглянути товари
11. Переглянути клієнтів
12. Переглянути замовлення
13. Заповнити порожню базу демо-даними
 s. Зберегти зміни в базі даних
 r. Скасувати незбережені зміни
 0. Вихід
================================================"""


def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_not_empty(prompt: str) -> str:
    while True:
        value = ask(prompt)
        if value:
            return value
        print("Значення не може бути порожнім.")


def ask_int(prompt: str, min_value: Optional[int] = None) -> int:
    while True:
        value = ask(prompt)
        try:
            number = int(value)
        except ValueError:
            print("Введіть ціле число.")
            continue
        if min_value is not None and number < min_value:
            print(f"Число має бути не меншим за {min_value}.")
            continue
        return number


def ask_float(prompt: str, default: Optional[float] = None, min_value: Optional[float] = None) -> float:
    while True:
        value = ask(prompt).replace(",", ".")
        if not value and default is not None:
            return default
        try:
            number = float(value)
        except ValueError:
            print("Введіть число.")
            continue
        if min_value is not None and number < min_value:
            print(f"Число має бути не меншим за {min_value}.")
            continue
        return number


def ask_date(prompt: str) -> Optional[str]:
    while True:
        value = ask(prompt)
        if not value:
            return None
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            print("Невірний формат дати. Використовуйте РРРР-ММ-ДД.")


def ask_yes_no(prompt: str) -> bool:
    while True:
        value = ask(prompt).lower()
        if value in YES_ANSWERS:
            return True
        if value in NO_ANSWERS:
            return False
        print("Відповідайте 'т' (так) або 'н' (ні).")


def format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def print_table(columns: Sequence[str], rows: Sequence[Tuple[Any, ...]]) -> None:
    if not rows:
        print("Немає даних.")
        return
    text_rows: List[List[str]] = [[format_value(value) for value in row] for row in rows]
    widths = [len(column) for column in columns]
    for row in text_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    header = " | ".join(column.ljust(widths[index]) for index, column in enumerate(columns))
    separator = "-+-".join("-" * width for width in widths)
    print(header)
    print(separator)
    for row in text_rows:
        print(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))


def offer_save(db: ShopDatabase) -> None:
    if not db.has_unsaved_changes():
        return
    if ask_yes_no("Зберегти зміни в базі даних? (т/н): "):
        db.commit()
        print("Зміни збережено.")
    else:
        print("Зміни не збережено. Їх можна зберегти пізніше (пункт 's') або скасувати (пункт 'r').")


def action_add_product(db: ShopDatabase) -> None:
    name = ask_not_empty("Назва товару: ")
    category = ask_not_empty("Категорія (наприклад: смартфони, ноутбуки, планшети): ")
    price = ask_float("Ціна: ", min_value=0)
    product_id = db.add_product(name, category, price)
    print(f"Товар додано, product_id = {product_id}.")
    offer_save(db)


def action_add_customer(db: ShopDatabase) -> None:
    first_name = ask_not_empty("Ім'я: ")
    last_name = ask_not_empty("Прізвище: ")
    email = ask_not_empty("Email: ")
    try:
        customer_id = db.add_customer(first_name, last_name, email)
    except sqlite3.IntegrityError:
        print(f"Клієнт з email '{email}' вже існує.")
        return
    print(f"Клієнта додано, customer_id = {customer_id}.")
    offer_save(db)


def action_add_order(db: ShopDatabase) -> None:
    print("\nКлієнти:")
    print_table(*db.list_customers())
    print("\nТовари:")
    print_table(*db.list_products())
    print()
    customer_id = ask_int("customer_id: ", min_value=1)
    product_id = ask_int("product_id: ", min_value=1)
    quantity = ask_int("Кількість: ", min_value=1)
    order_date = ask_date("Дата замовлення (РРРР-ММ-ДД, Enter - сьогодні): ")
    try:
        order_id = db.add_order(customer_id, product_id, quantity, order_date)
    except sqlite3.IntegrityError:
        print("Помилка: клієнта або товару з таким ідентифікатором не існує.")
        return
    print(f"Замовлення створено, order_id = {order_id}.")
    offer_save(db)


def action_total_sales(db: ShopDatabase) -> None:
    print(f"Загальний обсяг продажів: {db.total_sales():.2f}")


def action_orders_per_customer(db: ShopDatabase) -> None:
    print_table(*db.orders_per_customer())


def action_average_check(db: ShopDatabase) -> None:
    average = db.average_check()
    if average is None:
        print("Замовлень ще немає.")
        return
    print(f"Середній чек замовлення: {average:.2f}")


def action_most_popular_category(db: ShopDatabase) -> None:
    print_table(*db.most_popular_category())


def action_products_per_category(db: ShopDatabase) -> None:
    print_table(*db.products_per_category())


def action_update_prices(db: ShopDatabase) -> None:
    category = ask("Категорія (Enter - смартфони): ") or "смартфони"
    percent = ask_float("Відсоток зміни ціни (Enter - 10): ", default=10.0)
    updated = db.update_category_prices(category, percent)
    if updated == 0:
        print(f"У категорії '{category}' немає товарів.")
        return
    print(f"Оновлено цін: {updated}.")
    offer_save(db)


def action_list_products(db: ShopDatabase) -> None:
    print_table(*db.list_products())


def action_list_customers(db: ShopDatabase) -> None:
    print_table(*db.list_customers())


def action_list_orders(db: ShopDatabase) -> None:
    print_table(*db.list_orders())


def action_seed(db: ShopDatabase) -> None:
    if not db.seed_demo_data():
        print("База вже містить дані, демо-дані не додано.")
        return
    print("Демо-дані додано.")
    offer_save(db)


def action_commit(db: ShopDatabase) -> None:
    if not db.has_unsaved_changes():
        print("Незбережених змін немає.")
        return
    db.commit()
    print("Зміни збережено.")


def action_rollback(db: ShopDatabase) -> None:
    if not db.has_unsaved_changes():
        print("Незбережених змін немає.")
        return
    db.rollback()
    print("Незбережені зміни скасовано.")


ACTIONS: Dict[str, Callable[[ShopDatabase], None]] = {
    "1": action_add_product,
    "2": action_add_customer,
    "3": action_add_order,
    "4": action_total_sales,
    "5": action_orders_per_customer,
    "6": action_average_check,
    "7": action_most_popular_category,
    "8": action_products_per_category,
    "9": action_update_prices,
    "10": action_list_products,
    "11": action_list_customers,
    "12": action_list_orders,
    "13": action_seed,
    "s": action_commit,
    "r": action_rollback,
}


def finish(db: ShopDatabase) -> None:
    if db.has_unsaved_changes():
        if ask_yes_no("Є незбережені зміни. Зберегти перед виходом? (т/н): "):
            db.commit()
            print("Зміни збережено.")
        else:
            db.rollback()
            print("Зміни скасовано.")


def run(db: ShopDatabase) -> None:
    while True:
        print(MENU)
        choice = ask("Оберіть пункт: ").lower()
        if choice == "0":
            finish(db)
            print("До побачення!")
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("Невідомий пункт меню.")
            continue
        print()
        try:
            action(db)
        except (sqlite3.Error, ValueError) as error:
            print(f"Помилка: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI для бази даних онлайн-магазину електроніки")
    parser.add_argument("--db", default=DEFAULT_DB_FILE, help="шлях до файлу бази даних SQLite")
    args = parser.parse_args()

    db = ShopDatabase(args.db)
    print(f"Підключено до бази даних: {args.db}")
    try:
        run(db)
    except (KeyboardInterrupt, EOFError):
        print()
        if db.has_unsaved_changes():
            db.rollback()
            print("Роботу перервано, незбережені зміни скасовано.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
