"""
Webscrape Hacker news page to display news topics ordered on number of points
(i.e. the score).
"""

from copy import copy
from pathlib import Path
import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag


def get_news_item_score(news_item):
    score = 0
    news_item_id = news_item.get("id")
    score_span_id = "score_" + news_item_id
    score_span = news_item.find_next(attrs={"id": score_span_id})
    if not score_span:
        return score
    score_str = score_span.get_text()
    if not score_str:
        return score
    score = score_str.split()[0]
    return int(score)


def show_cmd_line_overview(news_items):
    for index, news_item in enumerate(news_items):
        news_title = news_item.find(class_="titleline")
        news_title_a = news_title.find("a")
        rank_str = str(index + 1) + ") "
        title = news_title_a.get_text()
        link = news_title_a.get("href")
        print("=" * 50)
        print(rank_str + title)
        padding = f"{'':{len(rank_str)}}"
        print(f"{padding}Link: {link}")
        print(f"{padding}Score: {get_news_item_score(news_item)}", end="\n\n")


def write_modified_html_page(news_items):
    if len(news_items) > 0:
        # Get original news table to be replaced
        news_table = news_items[0].find_parent("table")
        news_table_attrs = news_table.attrs

        # Create new ordered replacement table
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

        # Loop sorted news items and append to new ordered replacement table
        # We need to make sure we append copies because otherwise the next sibling
        # would be searched for in the replacement table, instead of in the
        # original
        for index, news_item in enumerate(news_items):
            tag = news_item
            copy_tag = copy(tag)
            rank_tag = copy_tag.find(class_="rank")
            if rank_tag:
                rank_tag.string = f"{index + 1}."
            ordered_table_body.append(copy_tag)
            while (tag := tag.next_sibling) and (
                (isinstance(tag, Tag)
                 and "athing" not in tag.get_attribute_list("class"))
                or isinstance(tag, NavigableString)
                or isinstance(tag, Comment)
            ):
                ordered_table_body.append(copy(tag))


        # Replace original news table with new ordered replacement table
        news_table.replace_with(ordered_table)

        # Write new version of HTML-page with updated news ranking
        html_path = Path("hacker-news.html")
        with open(html_path, "wt") as html:
            html.write(str(soup))
        print("Wrote new version of Hacker news HTML-page to", html_path)


if __name__ == "__main__":
    res = requests.get("https://news.ycombinator.com/news")
    if res.status_code != 200:
        raise RuntimeError("Error: failed to fetch Hacker news page!")

    soup = BeautifulSoup(res.text, "html.parser")

    news_items = soup.find_all("tr", class_="athing")
    news_items.sort(key=get_news_item_score, reverse=True)

    show_cmd_line_overview(news_items)
    write_modified_html_page(news_items)
