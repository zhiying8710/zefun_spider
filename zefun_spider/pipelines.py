# -*- coding: utf-8 -*-
from collections import OrderedDict
import json

import xlrd

from zefun_spider.items import SentreeMembersCsvItem, SentreeMembersSimpleItem,\
    SentreeEmployeeItem, SentreeServiceItem, SentreeMemberCardItem
from zefun_spider.utils.conns_helper import redis_exec, RedisHelper
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.http.request import Request
from scrapy.exceptions import DropItem
from scrapy import log
from zefun_spider import settings
from zefun_spider.utils import dama


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

class VerifyCodePipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        return [Request(x, meta=item['meta'], headers=item['headers']) for x in item.get(self.IMAGES_URLS_FIELD, [])]

    def item_completed(self, results, item, info):
        if self.IMAGES_RESULT_FIELD in item.fields:
            item[self.IMAGES_RESULT_FIELD] = [x for ok, x in results if ok]
            log.msg('got verify code result %s' % json.dumps(obj=item[self.IMAGES_RESULT_FIELD], ensure_ascii=False, indent=4))
            path = settings.IMAGES_STORE + '/' + item[self.IMAGES_RESULT_FIELD][0]['path']
            code = None
            while not code:
                code = dama.dama(path)
            code = str(code)
            log.msg('got code %s' % code)
            RedisHelper.get_redis_conn().set(item['key'], code)
            raise DropItem('drop it.')

class SentreeMembersRedisHelper(object):

    @redis_exec(rconn=RedisHelper.get_redis_conn())
    def store_member(self, member, spider, rconn=None):
        rconn.hset(spider.member_xls_key, member[u'卡号'], json.dumps(obj=member, ensure_ascii=False))

    @redis_exec(rconn=RedisHelper.get_redis_conn())
    def get_member(self, member_key_val, spider, rconn=None):
        val = rconn.hget(spider.member_xls_key, member_key_val)
        if not val:
            return None
        return json.loads(s=val, encoding='utf-8')

class SentreeMembersCsvItemPipeline(SentreeMembersRedisHelper):

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeMembersCsvItem:
            return item

        filename = item['filename']
        member_xls = xlrd.open_workbook(filename)
        member_sheet = member_xls.sheet_by_name(u'会员资料')
        rows = member_sheet.nrows
        headers = member_sheet.row_values(0)
        for r in xrange(1, rows):
            member = OrderedDict({})
            vals = member_sheet.row_values(r)
            for c, val in enumerate(vals):
                member[headers[c]] = val
            self.store_member(member, spider)
        spider.member_origin_result_ready = True


class SentreeMembersSimpleItemPipeline(SentreeMembersRedisHelper):

#     def spider_closed(self, spider):
#         spider.member_result_xsl_book.save(spider.member_result_xls)

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeMembersSimpleItem:
            return item

        member = self.get_member(item['card_no'], spider)
        if not member:
            return

        member[u'手机号'] = item['phone']
        member[u'姓名'] = item['name']

        spider.member_result_semaphore.acquire()
        while not spider.member_origin_result_ready:
            pass
        if spider.member_result_rows == 0:
            hs = member.keys()
            for i, h in enumerate(hs):
                spider.member_result_xsl_sheet.write(0, i, h)
            spider.member_result_rows += 1
        r = spider.member_result_rows
        vs = member.values()
        for i, v in enumerate(vs):
            spider.member_result_xsl_sheet.write(r, i, v)
        spider.member_result_xsl_book.save(spider.member_result_xls)
        spider.member_result_rows += 1
        spider.member_result_semaphore.release()

class SentreeEmployeeItemPipeline(object):

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeEmployeeItem:
            return item

        spider.employee_result_semaphore.acquire()
        if spider.employee_result_rows == 0:
            hs = item['info'].keys()
            for i, h in enumerate(hs):
                spider.employee_result_xsl_sheet.write(0, i, h)
            spider.employee_result_rows += 1

        r = spider.employee_result_rows
        vs = item['info'].values()
        for i, v in enumerate(vs):
            spider.employee_result_xsl_sheet.write(r, i, v)
        spider.employee_result_xsl_book.save(spider.employee_result_xls)
        spider.employee_result_rows += 1
        spider.employee_result_semaphore.release()


class SentreeServiceItemPipeline(object):

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeServiceItem:
            return item

        spider.service_result_semaphore.acquire()
        if spider.service_result_rows == 0:
            hs = item['info'].keys()
            for i, h in enumerate(hs):
                spider.service_result_xsl_sheet.write(0, i, h)
            spider.service_result_rows += 1

        r = spider.service_result_rows
        vs = item['info'].values()
        for i, v in enumerate(vs):
            spider.service_result_xsl_sheet.write(r, i, v)
        spider.service_result_xsl_book.save(spider.service_result_xls)
        spider.service_result_rows += 1
        spider.service_result_semaphore.release()


class SentreeMemberCardItemPipeline(object):

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeMemberCardItem:
            return item

        spider.membercard_result_semaphore.acquire()
        if spider.membercard_result_rows == 0:
            hs = item['info'].keys()
            for i, h in enumerate(hs):
                spider.membercard_result_xsl_sheet.write(0, i, h)
            spider.membercard_result_rows += 1

        r = spider.membercard_result_rows
        vs = item['info'].values()
        for i, v in enumerate(vs):
            spider.membercard_result_xsl_sheet.write(r, i, v)
        spider.membercard_result_xsl_book.save(spider.membercard_result_xls)
        spider.membercard_result_rows += 1
        spider.membercard_result_semaphore.release()
