# Webscraper_Hacker_News
Created python webscraper for Hacker News to merge news items from multiple pages and sort by number of points. Created using BeautifulSoup4 and a OOP paradigm.

# Installation
Install in virtual environment using following commands:
```shell
git clone https://github.com/CodeByAlejandro/Webscraper_Hacker_News.git
cd Webscraper_Hacker_News
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

# Usage
The program takes 1 optional cmd line argument which is a positive integer value indicating the number of Hacker News pages to scrape.

What it does:
1. It will retrieve the requested amount of Hacker News pages (each extra page is like clicking on the `More` link at the bottom of a page)
2. It will merge all of these pages into one big page
3. It will sort the merged page based on the number of points of eacht news item
4. It will display the resulting merge page via a cmd line interface
5. It will write the full HTML of the resulting merge page to `./hacker-news.html` (as one big page without `More`-links)

## Examples
```shell
python scrape_hn.py
```
```shell
python scrape_hn.py 2
```

# Uninstall
Deactivate the virtual environment using the exported shell function `deactivate`:
```shell
deactivate
```
Remove the project:
```shell
cd ..
rm -rf Webscraper_Hacker_News
```
