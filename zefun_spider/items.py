# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Field

class VerifyCodeItem(scrapy.Item):
    key = Field()
    url = Field()
    meta = Field()
    headers = Field()
    image_urls = Field()
    images = Field()

class SentreeShuiDanShenChaItem(scrapy.Item):
    menu = Field()
    headers = Field()
    data = Field()

class SentreeMembersCsvItem(scrapy.Item):
    filename = Field()

class SentreeMembersSimpleItem(scrapy.Item):
    card_no = Field()
    phone = Field()
    name = Field()

class SentreeEmployeeItem(scrapy.Item):
    info = Field()

class SentreeServiceItem(scrapy.Item):
    info = Field()

class SentreeMemberCardItem(scrapy.Item):
    info = Field()
