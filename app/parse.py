import asyncio
import csv

import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List

BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    text: str
    author: str
    tags: List[str]


async def fetch_quote(session: aiohttp.ClientSession, url: str) -> List[Quote]:
    async with session.get(url) as response:
        if response.status == 200:
            html_content = await response.text()
            soup = BeautifulSoup(html_content, "html.parser")
            quote_elements = soup.select(".quote")
            return [
                parse_single_quote(quote_soup) for quote_soup in quote_elements
            ]
        return []


def parse_single_quote(quote_soup: BeautifulSoup) -> Quote:
    return Quote(
        text=get_single_quote_text(quote_soup),
        author=get_single_quote_author(quote_soup),
        tags=get_single_quote_tags(quote_soup)
    )


def get_single_quote_text(quote_soup: BeautifulSoup) -> str:
    return quote_soup.select_one(".text").text.strip()


def get_single_quote_author(quote_soup: BeautifulSoup) -> str:
    return quote_soup.select_one(".author").text.strip()


def get_single_quote_tags(quote_soup: BeautifulSoup) -> List[str]:
    tag_elements = quote_soup.select(".tags .tag")
    tags = [tag.text.strip() for tag in tag_elements]
    return tags


async def generate_quotes() -> List[Quote]:
    page_num = 1
    async with aiohttp.ClientSession() as session:
        while True:
            url = BASE_URL + f"page/{page_num}/"
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, "html.parser")
                    quote_elements = soup.select(".quote")
                    if not quote_elements:
                        break
                    for quote_soup in quote_elements:
                        yield parse_single_quote(quote_soup)
                    page_num += 1
                else:
                    break


async def write_quotes_to_csv(quotes: List[Quote], csv_path: str) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Quote", "Author", "Tags"])
        for quote in quotes:
            writer.writerow([quote.text, quote.author, ", ".join(quote.tags)])


async def get_all_quotes() -> List[Quote]:
    quotes = []
    async for quote in generate_quotes():
        quotes.append(quote)
    return quotes


async def main(output_csv_path: str) -> None:
    quotes = await get_all_quotes()
    await write_quotes_to_csv(quotes=quotes, csv_path=output_csv_path)


if __name__ == "__main__":
    asyncio.run(main("result.csv"))
