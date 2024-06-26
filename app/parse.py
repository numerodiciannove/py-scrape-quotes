# import asyncio
# import csv
# import aiohttp
# from bs4 import BeautifulSoup
# from dataclasses import dataclass
# from typing import List
# import os
#
# BASE_URL = "https://quotes.toscrape.com/"
# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# OUTPUT_PATH = os.path.join(BASE_DIR, "tests", "result.csv")
#
#
# @dataclass
# class Quote:
#     text: str
#     author: str
#     tags: List[str]
#
#
# async def fetch_quote(session: aiohttp.ClientSession, url: str) -> List[Quote]:
#     async with session.get(url) as response:
#         if response.status == 200:
#             html_content = await response.text()
#             soup = BeautifulSoup(html_content, "html.parser")
#             quote_elements = soup.select(".quote")
#             return [parse_single_quote(quote_soup) for quote_soup in
#                     quote_elements]
#         return []
#
#
# def parse_single_quote(quote_soup: BeautifulSoup) -> Quote:
#     return Quote(
#         text=get_single_quote_text(quote_soup),
#         author=get_single_quote_author(quote_soup),
#         tags=get_single_quote_tags(quote_soup)
#     )
#
#
# def get_single_quote_text(quote_soup: BeautifulSoup) -> str:
#     return quote_soup.select_one(".text").text.strip()
#
#
# def get_single_quote_author(quote_soup: BeautifulSoup) -> str:
#     return quote_soup.select_one(".author").text.strip()
#
#
# def get_single_quote_tags(quote_soup: BeautifulSoup) -> List[str]:
#     tag_elements = quote_soup.select(".tags .tag")
#     tags = [tag.text.strip() for tag in tag_elements]
#     return tags
#
#
# async def generate_quotes() -> List[Quote]:
#     page_num = 1
#     async with aiohttp.ClientSession() as session:
#         while True:
#             url = BASE_URL + f"page/{page_num}/"
#             async with session.get(url) as response:
#                 if response.status == 200:
#                     html_content = await response.text()
#                     soup = BeautifulSoup(html_content, "html.parser")
#                     quote_elements = soup.select(".quote")
#                     if not quote_elements:
#                         break
#                     for quote_soup in quote_elements:
#                         yield parse_single_quote(quote_soup)
#                     page_num += 1
#                 else:
#                     break
#
#
# async def write_quotes_to_csv(quotes: List[Quote], csv_path: str) -> None:
#     os.makedirs(os.path.dirname(csv_path), exist_ok=True)
#
#     with open(csv_path, "w", newline="", encoding="utf-8") as file:
#         writer = csv.writer(file)
#         writer.writerow(["text", "author", "tags"])
#         for quote in quotes:
#             writer.writerow([quote.text, quote.author, quote.tags])
#
#
# async def get_all_quotes() -> List[Quote]:
#     quotes = []
#     async for quote in generate_quotes():
#         quotes.append(quote)
#     return quotes
#
#
# async def main(output_csv_path: str) -> None:
#     quotes = await get_all_quotes()
#     await write_quotes_to_csv(quotes=quotes, csv_path=output_csv_path)
#
#
# if __name__ == "__main__":
#     asyncio.run(main(OUTPUT_PATH))


import csv
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


QUOTE_FIELDS = [field.name for field in fields(Quote)]


def get_single_quote(quote_soup: BeautifulSoup) -> Quote:
    tags = quote_soup.select_one(".tags").text.split()[1:]
    return Quote(
        text=quote_soup.select_one(".text").text,
        author=quote_soup.select_one(".author").text,
        tags=tags
    )


def get_single_page_quotes(page_soup: BeautifulSoup) -> List[Quote]:
    quotes = page_soup.select(".quote")

    return [get_single_quote(quote_soup) for quote_soup in quotes]


def get_all_quotes() -> List[Quote]:
    first_page = requests.get(BASE_URL).content
    first_page_soup = BeautifulSoup(first_page, "html.parser")

    all_quotes = get_single_page_quotes(page_soup=first_page_soup)

    page_number = 2

    while True:
        next_page_url = urljoin(BASE_URL, f"page/{page_number}")
        next_page = requests.get(next_page_url).content
        next_page_soup = BeautifulSoup(next_page, "html.parser")

        if not next_page_soup.find(class_="next"):
            break

        all_quotes.extend(get_single_page_quotes(page_soup=next_page_soup))
        page_number += 1

    last_page_soup = urljoin(BASE_URL, f"page/{page_number}")
    last_page = requests.get(last_page_soup).content
    last_page_soup = BeautifulSoup(last_page, "html.parser")
    all_quotes.extend(get_single_page_quotes(page_soup=last_page_soup))

    return all_quotes


def write_to_csv(quotes: List[Quote], csv_path: str) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(QUOTE_FIELDS)
        writer.writerows([astuple(quote) for quote in quotes])


def main(output_csv_path: str) -> None:
    quotes = get_all_quotes()
    write_to_csv(quotes=quotes, csv_path=output_csv_path)


if __name__ == "__main__":
    main("result.csv")
