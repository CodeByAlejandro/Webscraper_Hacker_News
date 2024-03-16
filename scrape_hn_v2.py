"""
Webscrape Hacker news page to display news topics ordered on number of points
(i.e. the score).
"""

import sys
from copy import copy
from typing import Callable, Iterator, Tuple, List
from pathlib import Path

import requests
from bs4 import BeautifulSoup, PageElement, Tag, NavigableString, Comment


class NewsItem():

    def __init__(self, athing_tag: Tag) -> None:
        self._athing_tag = athing_tag
        self.title, self.link = self._get_titleline_info()
        self.score = self._get_score()

    def _get_titleline_info(self) -> Tuple[str, str | List[str]]:
        titleline_class = "titleline"
        titleline_tag = self._athing_tag.find(class_=titleline_class)
        if not isinstance(titleline_tag, Tag):
            raise ValueError(
                "Cannot create NewsItem: missing tag with class " +
                f"'{titleline_class}'!"
            )
        titleline_link = titleline_tag.find("a")
        if not isinstance(titleline_link, Tag):
            raise ValueError(
                "Cannot create NewsItem: missing link inside tag with class " +
                f"'{titleline_class}'!"
            )
        title = titleline_link.get_text()
        if not title:
            raise ValueError("Cannot create NewsItem: missing link title!")
        link = titleline_link.get('href')
        if not link:
            raise ValueError("Cannot create NewsItem: missing link href!")
        return (title, link)

    def _get_score(self) -> int:
        score = 0
        id = self._athing_tag.get("id")
        if not id:
            raise ValueError("Cannot create NewsItem: missing tag id!")
        elif isinstance(id, list):
            id = id[0]
        score_str = f"score_{id}"
        score_tag = self._athing_tag.find_next(id=score_str)
        if not score_tag:
            return score
        points_str = score_tag.get_text()
        if not points_str:
            return score
        score = points_str.split()[0]
        return int(score)

    def _get_news_item_block(self) -> Iterator[PageElement]:
        next_tag = self._athing_tag
        yield next_tag
        while (next_tag := next_tag.next_sibling) and (
            (isinstance(next_tag, Tag)
             and "athing" not in next_tag.get_attribute_list("class")
             and "morespace" not in next_tag.get_attribute_list("class"))
            or isinstance(next_tag, NavigableString)
            or isinstance(next_tag, Comment)
        ):
            yield next_tag

    def append_copy_to(self, table_tag: Tag) -> "NewsItem":
        copy_athing_tag = self._athing_tag
        for tag in self._get_news_item_block():
            copy_tag = copy(tag)
            if tag is self._athing_tag and isinstance(copy_tag, Tag):
                copy_athing_tag = copy_tag
            table_tag.append(copy_tag)
        return NewsItem(copy_athing_tag)


class NewsPage():

    def __init__(self, page_nbr: int) -> None:
        self.page_nbr = page_nbr
        self.soup = self._fetch_html_page()
        self.news_item_list = self._fetch_news_items()

    def _fetch_html_page(self) -> BeautifulSoup:
        res = requests.get(
            "https://news.ycombinator.com/?p=" + str(self.page_nbr)
        )
        if res.status_code != 200:
            raise ValueError(
                f"Cannot create NewsPage {self.page_nbr}: " +
                f"failed to fetch Hacker news page: {res.status_code}!"
            )
        return BeautifulSoup(res.text, "html.parser")

    def _fetch_news_items(self):
        news_item_list: List[NewsItem] = []
        for athing_tag in self.soup.find_all("tr", class_="athing"):
            try:
                news_item = NewsItem(athing_tag)
            except ValueError as err:
                id = athing_tag.get("id")
                if isinstance(id, list):
                    id = id[0]
                if id:
                    print(
                        f"Error creating NewsPage {self.page_nbr}; " +
                        f"NewsItem with id attr {id}:",
                        err,
                        sep="\n",
                        file=sys.stderr
                    )
                else:
                    print(
                        f"Error creating NewsPage {self.page_nbr}; " +
                        "NewsItem without id:",
                        err,
                        sep="\n",
                        file=sys.stderr
                    )
            else:
                news_item_list.append(news_item)
        return news_item_list

    def sort_news_items(
        self, key: Callable[[NewsItem], int], reverse: bool = False
    ) -> None:
        if len(self.news_item_list) > 0:
            news_table = self.news_item_list[0]._athing_tag.find_parent("table")
            if not news_table:
                raise ValueError(
                    f"Cannot sort news items on NewsPage {self.page_nbr}: " +
                    "missing parent table element!"
                )
            news_table_attrs = news_table.attrs
            ordered_table_soup = BeautifulSoup(
                "<table><tbody></tbody></table>", "html.parser"
            )
            if not (ordered_table_soup.table and ordered_table_soup.tbody):
                raise RuntimeError(
                    "Error: BeautifulSoup could not parse replacement table!"
                )
            ordered_table = ordered_table_soup.table
            for attr, value in news_table_attrs.items():
                ordered_table[attr] = value
            ordered_table_body = ordered_table_soup.tbody
            self.news_item_list.sort(key=key, reverse=reverse)
            for index, news_item in enumerate(self.news_item_list):
                copy_news_item = news_item.append_copy_to(ordered_table_body)
                self.news_item_list[index] = copy_news_item
            news_table.replace_with(ordered_table)

    def append_to(self, merge_page: "NewsPage") -> None:
        if len(self.news_item_list) > 0:
            if not len(merge_page.news_item_list) > 0:
                raise ValueError(
                    f"Cannot append NewsPage {self.page_nbr} to " +
                    f"NewsPage {merge_page.page_nbr}: " +
                    "target page has no news items!"
                )
            merge_news_table_tag = merge_page.news_item_list[0]._athing_tag
            merge_news_table = merge_news_table_tag.find_parent("table")
            if not merge_news_table:
                raise ValueError(
                    f"Cannot append NewsPage {self.page_nbr} to " +
                    f"NewsPage {merge_page.page_nbr}: " +
                    "target page has no parent table element!"
                )
            merge_news_table_attrs = merge_news_table.attrs
            ordered_table_soup = BeautifulSoup(
                "<table><tbody></tbody></table>", "html.parser"
            )
            if not (ordered_table_soup.table and ordered_table_soup.tbody):
                raise RuntimeError(
                    "Error: BeautifulSoup could not parse replacement table!"
                )
            ordered_table = ordered_table_soup.table
            for attr, value in merge_news_table_attrs.items():
                ordered_table[attr] = value
            ordered_table_body = ordered_table_soup.tbody
            for index, news_item in enumerate(merge_page.news_item_list):
                copy_news_item = news_item.append_copy_to(ordered_table_body)
                merge_page.news_item_list[index] = copy_news_item
            for index, news_item in enumerate(self.news_item_list):
                copy_news_item = news_item.append_copy_to(ordered_table_body)
                self.news_item_list[index] = copy_news_item
            merge_news_table.replace_with(ordered_table)
            merge_page.news_item_list.extend(self.news_item_list)

    def update_item_ranking_in_soup(self):
        for index, news_item in enumerate(self.news_item_list):
            athing_tag = news_item._athing_tag
            rank_tag = athing_tag.find(class_="rank")
            id = athing_tag.get("id")
            if isinstance(id, list):
                id = id[0]
            if not rank_tag:
                if id:
                    raise ValueError(
                        f"Cannot update ranking for NewsItem with id {id}: "
                        "missing tag with class 'rank'!"
                    )
                else:
                    raise ValueError(
                        "Cannot update ranking for NewsItem without id: " +
                        "missing tag with class 'rank'!"
                    )
            if isinstance(rank_tag, Tag):
                rank_tag.string = f"{index + 1}."

    def write_page_html(self, file: Path, update_ranking = True) -> None:
        with open(file, "wt") as html:
            if update_ranking:
                self.update_item_ranking_in_soup()
            html.write(str(self.soup))


# Singleton class
class Display():

    _instance = None

    def __new__(cls) -> "Display":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._initialized = True
            # Initialization goes here

    @staticmethod
    def display_news_item(news_item: NewsItem, rank: int) -> None:
        rank_str = f"{rank}) "
        print("=" * 50)
        print(rank_str + news_item.title)
        padding = " " * len(rank_str)
        print(f"{padding}Link: {news_item.link}")
        print(f"{padding}Score: {news_item.score}", end="\n\n")


if __name__ == "__main__":
    nbr_of_pages = 1
    if len(sys.argv) == 2:
        try:
            nbr_of_pages = int(sys.argv[1])
            if nbr_of_pages < 1:
                print('Error: number of pages must be at least 1!')
                sys.exit(1)
        except (TypeError, ValueError):
            print('Error: argument for number of pages must be an integer!')
            sys.exit(1)
    elif len(sys.argv) > 2:
        print('Error: provide only 1 argument for number of pages to process!')
        sys.exit(1)

    # Create all news pages
    news_pages: List[NewsPage] = []
    for index in range(nbr_of_pages):
        page_nbr = index + 1
        new_page = NewsPage(page_nbr)
        news_pages.append(new_page)


    # # Sort all pages based on news item score
    # for page in news_pages:
    #     page.sort_news_items(key=lambda news_item: news_item.score,
    #                          reverse=True)
    # # Display page 1
    # display = Display()
    # for index, news_item in enumerate(news_pages[0].news_item_list):
    #     rank = index + 1
    #     display.display_news_item(news_item, rank)

    # # Write merged page HTML
    # html_path = Path("hacker-news-page1.html")
    # news_pages[0].write_page_html(html_path)
    # print("Wrote new version of Hacker news HTML-page 1 to", html_path)


    # Create merged page
    main_page = news_pages[0]
    if nbr_of_pages > 1:
        for news_page in news_pages[1:]:
            news_page.append_to(main_page)

    # Sort merged page
    main_page.sort_news_items(key=lambda news_item: news_item.score,
                              reverse=True)

    # Display merged page
    display = Display()
    for index, news_item in enumerate(main_page.news_item_list):
        rank = index + 1
        display.display_news_item(news_item, rank)

    # Write merged page HTML
    html_path = Path("hacker-news.html")
    main_page.write_page_html(html_path)
    print("Wrote new version of Hacker news HTML-page to", html_path)
