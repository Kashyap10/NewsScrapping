from os import path
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from helper import Helper
from crawler import crawler
from bs4 import BeautifulSoup
from DbOps import DbOperations, QueryType
import re
import hashlib
import logging
import urllib3

urllib3.disable_warnings()


class accuracy(object):
    def __init__(self, url, body=None, headers=None, logger=None):
        self.url = url
        self.body = body
        self.headers = headers
        self.logger = logger
        self.news_collection = Helper.getNewsCollection()

    def crawler_news(self):
        try:
            for page in range(0, 5):
                url = baseurl + str(page)
                self.url = url
                response = crawler.MakeRequest(self.url, 'Get', postData=self.body, headers=self.headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                bulk_obj = DbOperations.Get_object_for_bulkop(False, self.news_collection)
                news_body = soup.find('tbody')
                news_data = news_body.find_all('tr')

                if news_data:
                    for news in news_data:
                        news_dict = Helper.get_news_dict()

                        news_header = news.find('td', class_= 'views-field views-field-field-nir-news-title')

                        title_data = news_header.find('a')
                        title = title_data.text if title_data else ""

                        url_data = news_header.find('a', {'href': True})
                        url = "https://investors.accuray.com" + str(url_data['href']) if url_data else ''

                        # Check if already present
                        unqUrl = hashlib.md5(url.encode()).hexdigest()
                        chkIsExists = DbOperations.GetData(self.news_collection, {"news_url_uid": str(unqUrl)}, {},
                                                           QueryType.one)
                        if (chkIsExists):
                            print("Already saved. url - ( " + url + " )")
                            continue

                        date_header = news.find('td', class_='views-field views-field-field-nir-news-date')

                        publish_date_data = date_header.find('time', class_='datetime')
                        publish_date = Helper.parse_date(
                            publish_date_data.text) if publish_date_data and publish_date_data.text != '' else ''

                        url_response = crawler.MakeRequest(url, 'Get', postData=self.body, headers=self.headers)
                        url_soup = BeautifulSoup(url_response.content, 'html.parser')

                        description_data = url_soup.find('div', {'class': "xn-content"})

                        description = []
                        regex = re.compile(r'[\n\xa0]')
                        for desc in description_data.find_all('p'):
                            description.append(regex.sub("", str(desc.text.strip())))
                        description = ''.join(description)


                        news_dict.update(
                            {"title": title, "news_title_uid": hashlib.md5(title.encode()).hexdigest(),
                             "url": url, "link": url, "news_url_uid": hashlib.md5(url.encode()).hexdigest(),
                             "description": description, "text": description,
                             "publishedAt": publish_date, 'date': publish_date, "publishedAt_scrapped": publish_date,
                             "company_id": "accuracy", "ticker": "accuracy_scrapped", "industry_name": "accuracy",
                             "news_provider": "accuracy"})

                        bulk_obj.insert(news_dict)

                        if len(bulk_obj._BulkOperationBuilder__bulk.__dict__['ops']) > 100:
                            bulk_obj.execute()
                            bulk_obj = DbOperations.Get_object_for_bulkop(False, self.news_collection)

                    if len(bulk_obj._BulkOperationBuilder__bulk.__dict__['ops']) > 0:
                        bulk_obj.execute()
                else:
                    print("All news has been scrapped !!")
        except Exception as e:
            self.logger.error(f"Error Occured : \n", exc_info=True)


# Create and configure logger
logging.basicConfig(filename="news_scraping_logs.log",
                    format='%(asctime)s %(message)s',
                    filemode='a')
logger = logging.getLogger()
baseurl = "https://investors.accuray.com/press-releases?page="
news_obj = accuracy(baseurl, logger=logger)
news_obj.crawler_news()

news_collection = Helper.getNewsCollection()
processed_collection = Helper.getProcessNewsCollection()
news_log_collection = Helper.getLogCollection()
isInserted, rowCount = Helper.processNews(news_collection, processed_collection, 'accuracy')
print('Total rows added Process collection => ' + str(rowCount))

# UPDATING LOG COLLECTION
if (isInserted):
    Helper.makeLog(news_log_collection, processed_collection, 'accuracy')