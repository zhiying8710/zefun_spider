# coding: utf-8
# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import sys
from scrapy.spider import Spider
from scrapy.http.request import Request
reload(sys)
sys.setdefaultencoding('utf-8')  # @UndefinedVariable

class CommonSpider(Spider):

    def __init__(self, *args, **kwargs):
        super(CommonSpider, self).__init__(*args, **kwargs)

    def make_requests_from_url(self, url):
        headers = None
        if hasattr(self, 'domain'):
            headers = {'Referer' : self.domain}
        return Request(url, dont_filter=True, headers=headers)

    def __str__(self):
        return self.name
