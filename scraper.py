# # -*- coding: utf-8 -*-

import sys
import requests
import lxml.html
try:  # Python 2
    from ConfigParser import ConfigParser
    import urlparse
    from urlparse import urljoin
    reload(sys)
    sys.setdefaultencoding('utf8')
except ImportError:  # Python 3
    from configparser import ConfigParser
    from urllib.parse import urlparse, urljoin

parser = ConfigParser()
parser.read('config.ini')


class Scraper:

    def __init__(self, entry_url, entry_name, session, auth_username,
                 auth_password, json_URL, base_url):
        self.entry_url = entry_url
        self.entry_name = entry_name
        self.session = session
        self.username = auth_username
        self.password = auth_password
        self.session.auth = (self.username, self.password)
        self.json_URL = json_URL
        self.base_url = base_url
        self.load_pages()

    def load_pages(self):
        try:
            response = requests.get(self.json_URL)
        except requests.exceptions.ConnectionError:
            raise Exception('Unable to fetch JSON_URL')
        try:
            self.pages = response.json()
        except ValueError:
            raise Exception('No json response in JSON_URL')

    def parse_page(self, url, page_name):

        if not url:
            url = self.entry_url
        page = self.pages[page_name]
        xpath_button = page['xpath_button_to_click']
        xpath_test_query = page['xpath_test_query']
        xpath_test_result = page['xpath_test_result']
        next_page_name = page['next_page_expected']
        r = self.session.get(url)
        html = lxml.html.fromstring(r.content)
        next_url = html.xpath(xpath_button)[0].get("href")
        if next_url.startswith('/') and not next_url.startswith('//'):
            next_url = urljoin(self.base_url, next_url)
        fetchedResult = html.xpath(xpath_test_query)
        if fetchedResult != xpath_test_result:
            return {"URL": None, "NEXT_PAGE_NAME": next_page_name}
        return {"URL": next_url, "NEXT_PAGE_NAME": next_page_name}

    def crawl_pages(self):
        page_count = 0
        page_url, page_name = self.entry_url, self.entry_name
        while page_url:
            parsedResult = self.parse_page(page_url, page_name)
            next_page_url = parsedResult['URL']
            next_page_name = parsedResult['NEXT_PAGE_NAME']
            if not next_page_url:
                error_msg = "ALERT - Can’t move to page {}: page {} link " \
                            "has been malevolently tampered with!!"
                print(error_msg.format(page_count+1, page_count))
                break
            if not page_name == '0':
                print("Move to page {}".format(page_count))
            page_name = next_page_name
            page_url = next_page_url
            page_count += 1


def main():
    name = 'SCRAPER'
    entry_url = parser.get(name, 'ENTRY_URL')
    entry_name = parser.get(name, 'ENTRY_NAME')
    session = requests.Session()
    auth_username = parser.get(name, 'AUTH_USERNAME')
    auth_password = parser.get(name, 'AUTH_PASSWORD')
    json_URL = parser.get(name, 'JSON_URL')
    base_url = parser.get(name, 'BASE_URL')
    scraper = Scraper(
        entry_url=entry_url,
        entry_name=entry_name,
        session=session,
        auth_username=auth_username,
        auth_password=auth_password,
        json_URL=json_URL,
        base_url=base_url,
    )
    scraper.crawl_pages()


if __name__ == '__main__':
    main()
