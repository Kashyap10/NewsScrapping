from os import path
import sys
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from helper import Helper
from crawler import crawler
from bs4 import BeautifulSoup
from DbOps import DbOperations,QueryType
import re
import hashlib
import logging
import urllib3

urllib3.disable_warnings()

class hanwhacorp(object):
    def __init__(self,url,body=None,headers=None,logger=None):
        self.url = url
        self.body = body
        self.headers = headers
        self.logger = logger
        self.news_collection = Helper.getNewsCollection()
    def crawler_news(self):
        try:
            loop = True
            page = 1
            while loop:
                response = crawler.MakeRequest(self.url.format(page=page),'Get',postData=self.body,headers=self.headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                bulk_obj = DbOperations.Get_object_for_bulkop(False,self.news_collection)
                news_data = soup.find('tbody')
                if news_data and news_data.tr.text.strip() != 'There is no data.':
                    for news in news_data.find_all('tr'):
                        news_dict = Helper.get_news_dict()

                        title_data = news.find('td',{'class':'title'})
                        title = title_data.text if title_data else ""

                        # Check if already present
                        unqUrl = hashlib.md5(title.encode()).hexdigest()
                        chkIsExists = DbOperations.GetData(self.news_collection, {"news_title_uid": str(unqUrl)}, {},
                                                           QueryType.one)
                        if (chkIsExists):
                            print("Already saved. title - ( " + title + " )")
                            continue

                        publish_date_data = news.find_all('td')[3].text
                        publish_date = Helper.parse_date(publish_date_data) if publish_date_data and publish_date_data != '' else ''

                        news_dict.update(
                            {"title": title, "news_title_uid": hashlib.md5(title.encode()).hexdigest(),
                             "publishedAt": publish_date, 'date': publish_date, "publishedAt_scrapped": publish_date,
                             "company_id": "hanwhacorp", "ticker": "hanwhacorp_scrapped", "industry_name": "hanwhacorp",
                             "news_provider": "hanwhacorp"})

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
url = "https://www.hanwhacorp.co.kr/eng/hanwha/media/coverage.do?pageNum={page}&search_param1=0&search_param2="
news_obj = hanwhacorp(url,logger=logger)
news_obj.crawler_news()

news_collection = Helper.getNewsCollection()
processed_collection = Helper.getProcessNewsCollection()
news_log_collection = Helper.getLogCollection()
isInserted,rowCount = Helper.processNewsBasedOnTitle(news_collection,processed_collection,'hanwhacorp')
print('Total rows added Process collection => ' + str(rowCount))

# UPDATING LOG COLLECTION
if (isInserted):
    Helper.makeLog(news_log_collection,processed_collection,'hanwhacorp')