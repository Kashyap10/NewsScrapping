from os import path
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from helper import Helper
from crawler import crawler
from bs4 import BeautifulSoup
from DbOps import DbOperations,QueryType
import hashlib,logging

class exxonmobil_corporation(object):
    def __init__(self, url, body=None, headers=None, logger=None):
        """
        Set initial paramaeters

        :param url: scraping url
        :param body: scraping url body
        :param headers: scraping url header
        :param logger: logger object
        """
        self.url = url
        self.body = body
        self.headers = headers
        self.news_collection = Helper.getNewsCollection()
        self.logger = logger
    def crawler_news(self):
        try:
            loop = True
            page = 1
            while loop:
                response = crawler.MakeRequest(self.url.format(page=page),'Get',postData=self.body)
                soup = BeautifulSoup(response.content, 'html.parser')
                bulk_obj = DbOperations.Get_object_for_bulkop(False,self.news_collection)
                news_data = soup.find_all('div', {'class': "contentCollection--item"})
                if news_data:
                    for news in news_data:
                        news_dict = Helper.get_news_dict()

                        title_data = news.find('a')
                        title = title_data.text if title_data else ""

                        url_data = news.find('a', {'href': True})
                        url = "https://corporate.exxonmobil.com"+str(url_data['href']) if url_data else ''

                        # Check if already present
                        unqUrl = hashlib.md5(url.encode()).hexdigest()
                        chkIsExists = DbOperations.GetData(self.news_collection, {"news_url_uid": str(unqUrl)}, {},
                                                           QueryType.one)
                        if (chkIsExists):
                            print("Already saved. url - ( " + url + " )")
                            continue

                        description_data = news.find('span',{'class':'contentCollection--description p'})
                        description = description_data.text if description_data else ''

                        publish_date_data = news.find('span',{'class':'date'})
                        publish_date = Helper.parse_date(publish_date_data.text) if publish_date_data and publish_date_data.text != '' else ''

                        news_dict.update(
                            {"title": title, "url": url, "formatted_sub_header": title, "description": description, "link": url,
                             "publishedAt":publish_date,'date':publish_date,"news_provider": "exxonmobil_corporation",
                             "company_id": "exxonmobil_corporation", "ticker": "exxonmobil_corporation_scrapped", "industry_name": "exxonmobil_corporation"})

                        bulk_obj.insert(news_dict)

                        if len(bulk_obj._BulkOperationBuilder__bulk.__dict__['ops']) >100:
                            bulk_obj.execute()
                            bulk_obj = DbOperations.Get_object_for_bulkop(False,self.news_collection)

                    if len(bulk_obj._BulkOperationBuilder__bulk.__dict__['ops']) > 0:
                        bulk_obj.execute()

                    page += 1

                else:
                    print("All news has been scrapped !!")
                    loop = False
        except Exception as e:
            self.logger.error(f"Error Occured : \n",exc_info=True)
#Create and configure logger
logging.basicConfig(filename="news_scraping_logs.log",
                    format='%(asctime)s %(message)s',
                    filemode='a')
logger = logging.getLogger()
url = "https://corporate.exxonmobil.com/api/v2/related/collection?itemid=3f311ddd-4cb5-489b-a768-325e94ee0ef1&contextid=3f311ddd-4cb5-489b-a768-325e94ee0ef1&language=en&pagesize=5&page={page}"
news_obj = exxonmobil_corporation(url,logger=logger)
news_obj.crawler_news()

news_collection = Helper.getNewsCollection()
processed_collection = Helper.getProcessNewsCollection()
news_log_collection = Helper.getLogCollection()
isInserted,rowCount = Helper.processNews(news_collection,processed_collection,'exxonmobil_corporation')
print('Total rows added Process collection => ' + str(rowCount))

# UPDATING LOG COLLECTION
if (isInserted):
    Helper.makeLog(news_log_collection,processed_collection,'exxonmobil_corporation')