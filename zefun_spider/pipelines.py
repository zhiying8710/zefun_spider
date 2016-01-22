# -*- coding: utf-8 -*-
from collections import OrderedDict
import json

import xlrd

from zefun_spider.items import SentreeMembersCsvItem, SentreeMembersSimpleItem,\
    SentreeEmployeeItem, SentreeServiceItem, SentreeMemberCardItem,\
    SentreeMemberTreatItem
from zefun_spider.utils.conns_helper import redis_exec, RedisHelper
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.http.request import Request
from scrapy.exceptions import DropItem
from scrapy import log
from zefun_spider import settings
from zefun_spider.utils import dama
from zefun_spider.settings import running_auths_key


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
    def store_member(self, member, spider, rconn=None, add=True):
        member = dict(member)
        if add:
            rconn.hset(spider.member_xls_key, member[u'卡号'], json.dumps(obj=member, ensure_ascii=False))
        else:
            rconn.hdel(spider.member_xls_key, member[u'卡号'])

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

    card_no_sep = '\001'

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeMembersSimpleItem:
            return item

        member = self.get_member(item['card_no'], spider)
        if not member:
            return

        member[u'手机号'] = item['phone']
        member[u'姓名'] = item['name']
        member[u'卡名称'] = item['card_name']
        member[u'卡类型'] = item['card_type']
        member[u'折扣'] = item['discont']
        member[u'失效日期'] = item['timeout']
        member[u'欠款'] = item['overdraft']

        while not spider.member_origin_result_ready:
            pass
        overage = item['overage']
        if not overage:
            self.store_member(member, spider)
        else:
            self.store_member(member, spider, add=False)
            for i, o in enumerate(overage):
                member[u'卡号'] = '%s%s%d' % (item['card_no'], self.card_no_sep, i)
                member[u'卡内总余额'] = o
                self.store_member(member, spider)

    def close_spider(self, spider):
        s_members = RedisHelper.get_redis_conn().hvals(spider.member_xls_key)
        r = 0
        hs = spider.member_headers
        for i, h in enumerate(hs):
            spider.member_result_xsl_sheet.write(0, i, h)
        r += 1
        log.msg('%s get members from redis, size: %d' %(spider.name, 0 if not s_members else len(s_members)))
        if s_members:
            for s_member in s_members:
                member = json.loads(s=s_member, encoding="utf-8")
                is_valid = True
                for h in hs:
                    if not h in member:
                        is_valid = False
                        break
                if not is_valid:
                    continue
                card_no = member[u'卡号']
                if self.card_no_sep in card_no:
                    card_no = card_no[:card_no.index(self.card_no_sep)]
                    member[u'卡号'] = card_no
                for i, h in enumerate(hs):
                    spider.member_result_xsl_sheet.write(r, i, member[h])
                r += 1
        spider.member_result_xsl_book.save(spider.member_result_xls)
        log.msg('%s complete write member xsl for %s.' % (spider.name, spider.login_username))
        RedisHelper.get_redis_conn().delete(spider.member_xls_key)
        RedisHelper.get_redis_conn().srem(running_auths_key, spider.login_username)


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

class SentreeMemberTreatItemPipeline(object):

    @redis_exec(rconn=RedisHelper.get_redis_conn())
    def store_member_treat(self, member_treat, spider, rconn=None):
        rconn.rpush(spider.member_treat_key, json.dumps(obj=dict(member_treat), ensure_ascii=False))

    def process_item(self, item, spider):
        if not item or not type(item) == SentreeMemberTreatItem:
            return item

        self.store_member_treat(item, spider)

    def close_spider(self, spider):
        s_member_treats = RedisHelper.get_redis_conn().lrange(spider.member_treat_key, 0, -1)
        if s_member_treats:
            for s_member_treat in s_member_treats:
                member_treat = json.loads(s=s_member_treat, encoding="utf-8")
                if spider.member_treat_rows == 0:
                    hs = member_treat['hs']
                    for i, h in enumerate(hs):
                        spider.member_treat_result_xsl_sheet.write(0, i, h)
                    spider.member_treat_rows += 1
                vals = member_treat['vals']
                r = spider.member_treat_rows
                for i, v in enumerate(vals):
                    spider.member_treat_result_xsl_sheet.write(r, i, v)
                spider.member_treat_rows += 1

        spider.member_treat_result_xsl_book.save(spider.member_treat_result_xsl)
        log.msg('%s complete write member treat xsl for %s.' % (spider.name, spider.login_username))
        RedisHelper.get_redis_conn().delete(spider.member_treat_key)
