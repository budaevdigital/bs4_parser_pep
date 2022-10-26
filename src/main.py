# main.py
import re
from tkinter.messagebox import NO
from urllib.parse import urljoin

import logging
import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag, find_all_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features="lxml")
    main_div = find_tag(soup, name="section", attrs={"id": "what-s-new-in-python"})
    div_with_ul = find_tag(main_div, name="div", attrs={"class": "toctree-wrapper"})
    sections_by_python = find_all_tag(
        div_with_ul, name="li", attrs={"class": "toctree-l1"}
    )

    results = [("Ссылка на статью", "Заголовок", "Редактор, Aвтор")]
    for row in tqdm(sections_by_python, desc="Парсинг новостей", colour="magenta"):
        a_link = find_tag(row, name="a")
        # Для адекватного "склеивания" URL
        href_link = a_link["href"]
        version_link = urljoin(whats_new_url, href_link)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features="lxml")
        h1_tag_text = find_tag(soup, name="h1").text.replace("Â¶", "")
        dl_tag_text = (find_tag(soup, name="dl")).text.replace("\n", " ")
        results.append((version_link, h1_tag_text, dl_tag_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features="lxml")
    sidebar = find_tag(soup, name="div", attrs={"class": "sphinxsidebarwrapper"})
    ul_tags = find_all_tag(sidebar, name="ul")
    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = find_all_tag(ul, name="a")
            break
    else:
        raise Exception("Парсер ничего не нашёл")

    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
    results = [("Ссылка на документацию", "Версия", "Статус")]

    for a_tag in tqdm(a_tags, desc="Парсинг версий", colour="magenta"):
        text_link = a_tag["href"]
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((text_link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, "download.html")
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, "lxml")
    main_tag = find_tag(soup, "div", {"role": "main"})
    table_tag = find_tag(main_tag, "table", {"class": "docutils"})
    pdf_a4_tag = find_tag(table_tag, "a", {"href": re.compile(r".+pdf-a4\.zip$")})
    pdf_a4_link = pdf_a4_tag["href"]
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split("/")[-1]

    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)

    with open(archive_path, "wb") as file:
        file.write(response.content)
    logging.info(f"Архив был загружен и сохранён: {archive_path}")


def pep(session):
    pep_list_url = MAIN_PEP_URL
    response = get_response(session, pep_list_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features="lxml")
    table_tags = find_all_tag(soup, name="table", attrs={"class": "pep-zero-table"})
    temp_result = []
    results = [["Статус", "Количество"], ]
    for row in tqdm(table_tags, desc="Парсинг списка PEP", colour="magenta"):
        body_tags = find_tag(row, name="tbody")
        tr_tags = find_all_tag(
            body_tags, name="tr", attrs={"class": re.compile(r"row-(even|odd)")}
        )
        for index in tr_tags:
            first_column = find_tag(index, name="abbr", ifEmpty=True)
            if first_column is None:
                preview_status = ""
            else:
                preview_status = first_column.text[1:]
            second_column = find_tag(
                index, name="a", attrs={"class": "pep reference internal"}, ifEmpty=True
            )
            crop_link_pep = second_column["href"]
            full_link_pep = urljoin(pep_list_url, crop_link_pep)
            if not EXPECTED_STATUS[preview_status]:
                logging.warning(
                        f"Статус {preview_status} отсутствует в базе"
                )
            temp_result.append((EXPECTED_STATUS[preview_status], full_link_pep))
            
    for row in tqdm(temp_result, desc="Проверка статусов PEP", colour="magenta"):
        response = get_response(session, row[1])
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features="lxml")
        status_tag = find_tag(soup, string="Status")
        status = status_tag.find_next("dd").text
        if status not in row[0]:
            logging.info(
                "\nНесовпадающие статусы:\n"
                f"{row[1]}\n"
                f"Статус в карточке: {status}\n"
                f"Ожидаемые статусы: {row[0]}\n"
            )
        for i in range(0, len(results)):
            if status == results[i][0]:
                results[i][1] = int(results[i][1]) + 1
                break
            if i == len(results) - 1:
                results.append([status, 1])
    total = 0
    for row in range(1, len(results)):
        total += results[row][1]
        if row == len(results) - 1:
            results.append(["Всего:", total])
    return results


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    configure_logging()
    logging.info("Парсер запущен!")
    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parse = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parse.parse_args()
    logging.info(f"Аргументы командной строки: {args}")
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info("Парсер завершил работу.")


if __name__ == "__main__":
    main()
