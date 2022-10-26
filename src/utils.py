# utils.py
import logging
from requests import RequestException
from exceptions import ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = "utf-8"
        return response
    except RequestException:
        logging.exception(
            f"Возникла ошибка при загрузке страницы {url}", stack_info=True
        )


def find_tag(soup, name=None, attrs=None, ifEmpty=False, string=None):
    searched_tag = soup.find(
        name=(name or ""), string=(string or ""), attrs=(attrs or {})
    )
    if searched_tag is None:
        if ifEmpty:
            return searched_tag
        error_msg = f"Не найден тег {name} {attrs}"
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def find_all_tag(soup, name=None, attrs=None, string=None):
    searched_tags = soup.find_all(
        name=(name or ""), string=(string or ""), attrs=(attrs or {})
    )
    if searched_tags == []:
        error_msg = f"Не найден тег {name} {attrs}"
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tags
