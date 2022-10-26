# outputs.py
import csv
import logging
import datetime as dt
from prettytable import PrettyTable
from constants import BASE_DIR, DATETIME_FORMAT


def control_output(results, cli_args):
    # Проверяем аргумент parser.add_argument --output
    # Чтобы не обращаться дважды к атрибуту объекта, сохраним в переменную
    output = cli_args.output
    if output == "pretty":
        pretty_output(results)
    elif output == "file":
        # Вывод в csv
        file_output(results, cli_args)
    else:
        default_output(results)


def default_output(results):
    for row in results:
        print(*row)


def pretty_output(results):
    # Инициализируем объект PrettyTable
    table = PrettyTable()
    # В качестве заголовков устанавливаем первый элемент списка
    table.field_names = results[0]
    # Выравниваем всю таблицу по левому краю
    table.align = "l"
    # Добавляем все строки, начиная со второй (с индексом 1)
    # СТРОКИ добавляются через 'add_rowS'
    # СТРОКА добавляется через 'add_row'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    result_dir = BASE_DIR / "results"
    result_dir.mkdir(exist_ok=True)
    # Получаем режим работы парсера из аргументов командной строки
    parse_mode = cli_args.mode
    # Получаем текущие дату и время
    now_date = dt.datetime.now()
    # Сохраняем текущие дату-время в указанном формате.
    # Результат будет выглядеть вот так: 2021-06-18_07-40
    now_date_formatted = now_date.strftime(DATETIME_FORMAT)
    filename = f"{parse_mode}_{now_date_formatted}.csv"
    file_path = result_dir / filename
    with open(file_path, "w", encoding="utf-8") as f:
        # Создаём «объект записи» writer
        writer = csv.writer(f, dialect="unix")
        # Передаём в метод writerows список с результатами парсинга
        writer.writerows(results)
    logging.info(f"Файл с результатами был сохранён: {file_path}")
