# coding: utf-8

# Scrapy settings for zefun_spider project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'zefun_spider'

SPIDER_MODULES = ['zefun_spider.spiders']
NEWSPIDER_MODULE = 'zefun_spider.spiders'

ITEM_PIPELINES = {
#     'zefun_spider.pipelines.VerifyCodePipeline' : 500,
    'zefun_spider.pipelines.SentreeMembersCsvItemPipeline' : 501,
    'zefun_spider.pipelines.SentreeMembersSimpleItemPipeline' : 502,
    'zefun_spider.pipelines.SentreeEmployeeItemPipeline' : 502,
    'zefun_spider.pipelines.SentreeServiceItemPipeline' : 502,
    'zefun_spider.pipelines.SentreeMemberCardItemPipeline' : 502,
}

DOWNLOAD_TIMEOUT = 60
CONCURRENT_REQUESTS = 8
USER_AGENT = 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.79 Safari/535.11'

LOG_ENABLED = True
LOG_FILE = './log/zefun_spider.log'
LOG_LEVEL = 'DEBUG'

ROBOTSTXT_OBEY = False

IMAGES_STORE = '/root/zefun_spider_result'

COOKIES_DEBUG=True


redis_host = '127.0.0.1'
redis_port = 6379
redis_df_db = 15

result_dir = '/root/zefun_spider_result'
