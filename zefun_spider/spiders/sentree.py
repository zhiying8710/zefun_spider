# coding: utf-8
from collections import OrderedDict
import datetime
import json
import multiprocessing
import os
import time
import traceback
from urllib import urlencode

from scrapy import log
from scrapy.http.request import Request
from scrapy.http.request.form import FormRequest
from scrapy.http.response.text import TextResponse
from scrapy.selector.unified import Selector
import xlwt

from zefun_spider import utils, settings
from zefun_spider.items import SentreeShuiDanShenChaItem, SentreeMembersCsvItem,\
    SentreeMembersSimpleItem, SentreeEmployeeItem, SentreeServiceItem,\
    SentreeMemberCardItem
from zefun_spider.settings import result_dir
from zefun_spider.spiders import CommonSpider
from zefun_spider.utils import dama, str_list_strip, str_list_strip_replace
from scrapy.http.cookies import CookieJar

class SentreeSpider(CommonSpider):

    name = 'sentree'

    def __init__(self, **kwagrs):
        self.start_urls = ['http://vip6.sentree.com.cn/shair/loginAction.action?from=base']
        self.domain = 'http://vip6.sentree.com.cn'
        self.login_url = 'http://vip6.sentree.com.cn/shair/loginAction!ajaxLogin.action'
        self.login_rand = 'http://vip6.sentree.com.cn/shair/vc'
        self.login_username = u'西城店店长'
        self.login_password = '15977340369dz'
        self.start_time = time.time()
        self.member_xls_key = '__%s_xls_members_%d' % (self.name, self.start_time)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        self.member_result_xls = '%s/members_%d.xls' % (result_dir, self.start_time)
        self.member_result_xsl_book = xlwt.Workbook()
        self.member_result_xsl_sheet = self.member_result_xsl_book.add_sheet(u'会员资料')
        self.member_result_rows = 0
        self.member_result_semaphore = multiprocessing.Semaphore(1)
        self.member_origin_result_ready = False
        self.member_headers = [u'手机号', u'姓名', u'性别', u'会员分类', u'注册日期', u'卡号', u'卡名称', u'卡类型', u'折扣', u'储值总额', u'消费总额', u'卡内总余额', u'赠送总余额', u'失效日期', u'消费次数', u'当前积分', u'最后消费日']

        self.employee_result_semaphore = multiprocessing.Semaphore(1)
        self.employee_result_xls = '%s/employees_%d.xls' % (result_dir, self.start_time)
        self.employee_result_xsl_book = xlwt.Workbook()
        self.employee_result_xsl_sheet = self.employee_result_xsl_book.add_sheet(u'员工资料')
        self.employee_result_rows = 0

        self.service_result_semaphore = multiprocessing.Semaphore(1)
        self.service_result_xls = '%s/services_%d.xls' % (result_dir, self.start_time)
        self.service_result_xsl_book = xlwt.Workbook()
        self.service_result_xsl_sheet = self.service_result_xsl_book.add_sheet(u'服务项目')
        self.service_result_rows = 0

        self.membercard_result_semaphore = multiprocessing.Semaphore(1)
        self.membercard_result_xls = '%s/membercards_%d.xls' % (result_dir, self.start_time)
        self.membercard_result_xsl_book = xlwt.Workbook()
        self.membercard_result_xsl_sheet = self.membercard_result_xsl_book.add_sheet(u'会员卡')
        self.membercard_result_rows = 0


    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.preper_login, meta={'cookie_jar' : CookieJar()})

    def preper_login(self, resp):
        yield Request(url='%s?r=%d' % (self.login_rand, time.time()), callback=self.start_login, meta=resp.meta)

    def start_login(self, resp):
        path = settings.IMAGES_STORE + ("/vc_%d.jpg" % time.time())
        with open(path, "wb") as f:
            f.write(resp.body)
        rand = None
        while not rand:
            rand = dama.dama(path)
            time.sleep(3)
        self.log('%s got verify code %s' % (self.name, rand), log.INFO)

        return [FormRequest(url=self.login_url, formdata={
                     'login' : self.login_username,
                     'passwd' : self.login_password,
                     'rand' : rand
                     }, callback=self.parse_login, meta=resp.meta)]


    def parse_login(self, resp):
        res = json.loads(s = resp._get_body(), encoding='utf-8')
        code = res['code']
        if 3 == code or 4 == code:
            self.log('%s verify code is wrong, retry.' % self.name, level=log.WARNING)
            return self.preper_login(resp)
        if 7 == code:
            return Request(url='http://vip6.sentree.com.cn/shair/main!showMain.action', callback=self.parse_main, cookies={
                                                                                                                           'username' : urlencode({'' : self.login_username})[1:],
                                                                                                                           'testcookie' : 'testvalue',
                                                                                                                           'pageReferrInSession' : 'http%3A//vip6.sentree.com.cn/shair/main%21showMain.action',
                                                                                                                           'firstEnterUrlInSession' : 'http%3A//vip6.sentree.com.cn/shair/main%21showMain.action',
                                                                                                                           'VisitorCapacity' : '1'
                                                                                                                        })
        else:
            self.log('%s login failed, login result code is %d' %(self.name, code), level=log.ERROR)
            return None

    def parse_main(self, resp):
        urls = {
#                 'http://vip6.sentree.com.cn/shair/consumerHelp!init.action?r=%d' % time.time() : self.parse_consumer,
                'http://vip6.sentree.com.cn/shair/main!showDesk.action' : self.parse_showdesk
                }
        for url, act in urls.items():
            yield Request(url=url, callback=act)

    def parse_consumer(self, resp):
        urls = {
                'http://vip6.sentree.com.cn/shair/bill!billcheck.action?set=cash&r=%d' % time.time()  : [self.parse_consumer_bill],
#                 'http://vip6.sentree.com.cn/shair/collect!day.action' : [self.parse_consumer_collect],
#                 'http://vip6.sentree.com.cn/shair/memberInfo!memberlist.action?set=cash&r=%d' % time.time() : [self.parse_consumer_members]
                }
        for url, info in urls.items():
            yield Request(url=url, callback=info[0])

    def parse_consumer_bill(self, resp):
        urls = {
                'http://vip6.sentree.com.cn/shair/bill!billcheck.action?set=cash' : [self.parse_consumer_bill_stream],
#                 'http://vip6.sentree.com.cn/shair/accountBill!givebill.action?set=cash&r=%d' %time.time() : [self.parse_consumer_bill_givebill],
#                 'http://vip6.sentree.com.cn/shair/consumeHiddenLog!init.action?set=cash' : [self.parse_consumer_bill_hidden]
                }

        for url, info in urls.items():
            yield Request(url=url, callback=info[0])

    def parse_consumer_bill_stream(self, resp):
        urls = {
                'http://vip6.sentree.com.cn/shair/bill!billcheck.action?set=cash' : [self.parse_consumer_bill_stream_validate],
#                 'http://vip6.sentree.com.cn/shair/bill!bill.action?set=cash&billFlag=0' : [self.parse_consumer_bill_stream_item],
#                 'http://vip6.sentree.com.cn/shair/bill!bill.action?set=cash&billFlag=1' : [self.parse_consumer_bill_stream_item1],
#                 'http://vip6.sentree.com.cn/shair/bill!bill.action?set=cash&billFlag=2' : [self.parse_consumer_bill_stream_item2],
#                 'http://vip6.sentree.com.cn/shair/bill!bill.action?set=cash&billFlag=3' : [self.parse_consumer_bill_stream_item3],
#                 'http://vip6.sentree.com.cn/shair/bill!bill.action?set=cash&billFlag=5' : [self.parse_consumer_bill_stream_item5],
#                 'http://vip6.sentree.com.cn/shair/bill!cancelbill.action?set=cash' : [self.parse_consumer_bill_stream_cancel],
#                 'http://vip6.sentree.com.cn/shair/bill!feeallocation.action?set=cash' : [self.parse_consumer_bill_stream_fee]
                }
        for url, info in urls.items():
            yield Request(url=url, callback=info[0], meta={'end_date' : utils.subtract_months(datetime.date.today(), 5, '%Y-%m-%d')})

    def parse_consumer_bill_stream_validate(self, resp):
        hxs = Selector(resp)
        menu = [u'营业记录', u'水单记录', u'水单审查']
        bill_headers = []
        head_nodes = hxs.xpath('//tbody[@id="billBody"]/parent::table/thead/tr/th')
        if not head_nodes:
            self.log('in %s.parse_consumer_bill_stream_validate, can not get table headers.' % self.name, level=log.ERROR)
            yield None
            return
        for idx, hd in enumerate(head_nodes):
            if idx == len(head_nodes) - 1:
                break
            txts = hd.xpath('child::text()').extract()
            bill_headers.append('/'.join(txts))

        bill_nodes = hxs.xpath('//tbody[@id="billBody"]/tr')
        if bill_nodes:
            for bn in bill_nodes:
                item = SentreeShuiDanShenChaItem()
                item['menu'] = menu
                headers = []
                item['data'] = OrderedDict({})
                data_nodes = bn.xpath('td')
                for idx, dn in enumerate(data_nodes):
                    if idx == 6:
                        break
                    h = bill_headers[idx]
                    if idx == 0 or idx == 4:
                        headers.append(h)
                        item['data'][h] = [str_list_strip(dn.xpath('descendant::text()').extract())[0], True]
                        continue
                    if idx == 1 or idx == 2 or idx == 3:
                        headers.append(h)
                        item['data'][h] = [str_list_strip(dn.xpath('descendant::text()').extract()), True]
                        continue
                    if idx == 5:
                        detail = []
                        subtrs = dn.xpath('table/tr')
                        recoded_headers = False
                        for tr in subtrs:
                            empperfors = []
                            subdetail = OrderedDict({})
                            subtds = tr.xpath('td')
                            h = bill_headers[idx + 0]
                            if not recoded_headers:
                                headers.append(h)
                            subdetail[h] = [str_list_strip(subtds[0].xpath('descendant::text()').extract()), True]
                            h = bill_headers[idx + 1]
                            if not recoded_headers:
                                headers.append(h)
                            subdetail[h] = [str_list_strip(subtds[1].xpath('descendant::text()').extract())[0], True]

                            subtrs2 = subtds[2].xpath('table/tr')
                            for kdx, tr2 in enumerate(subtrs2):
                                if kdx == len(subtrs2) - 1:
                                    break
                                empperfor = OrderedDict({})
                                subtds2 = tr2.xpath('td')
                                h = bill_headers[idx + 2 + 0]
                                if not recoded_headers:
                                    headers.append(h)
                                if h not in empperfor:
                                    empperfor[h] = []
                                empperfor[h].append([str_list_strip(subtds2[0].xpath('descendant::text()').extract()), True])
                                h = bill_headers[idx + 2 + 1]
                                if not recoded_headers:
                                    headers.append(h)
                                if h not in empperfor:
                                    empperfor[h] = []
                                empperfor[h].append([str_list_strip(subtds2[1].xpath('descendant::text()').extract())[0], True])
                                h = bill_headers[idx + 2 + 2]
                                h = u'员工' + h
                                if not recoded_headers:
                                    headers.append(h)
                                if h not in empperfor:
                                    empperfor[h] = []
                                empperfor[h].append([str_list_strip(subtds2[2].xpath('descendant::text()').extract())[0], True])
                                empperfors.append(empperfor)
                                recoded_headers = True
                            subdetail[u'员工业绩'] = [empperfors, False]
                            detail.append([subdetail, False])
                            recoded_headers = True
                        item['headers'] = headers
                        item['data'][u'详情'] = [detail, False]
#                 items.append(item)
                yield item

    def parse_showdesk(self, resp):
        r = time.time()
        urls = {
                'http://vip6.sentree.com.cn/shair/memberInfo!memberlist.action?set=manage&r=%d' % r  : [self.parse_showdesk_members, {'r' : r}],
#                 'http://vip6.sentree.com.cn/shair/employee!employeeInfo.action?set=manage&r=%d' % r : [self.parse_showdesk_employees, {'r' : r}],
#                 'http://vip6.sentree.com.cn/shair/serviceItemSet!init.action?set=manage&r=%d' % r : [self.parse_showdesk_services, {'r' : r}],
#                 'http://vip6.sentree.com.cn/shair/cardTypeSet!getList.action?set=manage&r=%d' % r : [self.parse_showdesk_membercards, {'r' : r}],
                }
        for url, info in urls.items():
            yield Request(url=url, callback=info[0], meta=info[1])


    def parse_showdesk_members_save_xls(self, resp):
        path = settings.IMAGES_STORE + ("/member_origin_%d.xls" % time.time())
        with open(path, "wb") as f:
            f.write(resp.body)
        csv_item = SentreeMembersCsvItem()
        csv_item['filename'] = path
        yield csv_item

        meta = resp.meta
        meta['page'] = 1
        yield FormRequest(url="http://vip6.sentree.com.cn/shair/memberInfo!memberlist.action", formdata={
                         'page.currNum' : '1',
                         'page.rpp' : '30',
                         'r' : str(meta['r']),
                         'set' : 'manage'
                         }, callback=self.parse_showdesk_members2, meta=meta)

    def parse_showdesk_members(self, resp):
        yield FormRequest(url="http://vip6.sentree.com.cn/shair/memberInfo!exportmember.action?set=manage", formdata={'memberForm.shopid' : '33082', 'memberForm.birthtype' : '1', 'memberForm.invalidflag' : '0'}, meta=resp.meta, callback=self.parse_showdesk_members_save_xls)

    def parse_showdesk_members2(self, resp):
        hxs = Selector(resp)
        member_nodes = hxs.xpath('//form[@id="delForm"]//table/tbody/tr')
        if member_nodes:
            for m_n in member_nodes:
                member_tds = m_n.xpath('td')
                try:
                    phone = member_tds[1].xpath('a/child::text()').extract()[0].replace('&nbsp;', '').strip()
                    name = member_tds[2].xpath('span/child::text()').extract()[0].replace('&nbsp;', '').strip()
                    card_no = member_tds[6].xpath('table/tr/td[1]/a/child::text()').extract()[0].replace('&nbsp;', '').strip()
                    card_name = member_tds[6].xpath('table/tr/td[2]/child::text()').extract()[0].replace('&nbsp;', '').strip()
                    card_type = member_tds[6].xpath('table/tr/td[3]//child::text()').extract()[0].replace('&nbsp;', '').replace(' ', '').strip()
                    discont = member_tds[6].xpath('table/tr/td[4]/child::text()').extract()[0].replace('&nbsp;', '').replace(' ', '').strip()
                    timeout = member_tds[6].xpath('table/tr/td[9]/child::text()').extract()[0].replace('&nbsp;', '').replace(' ', '').strip()
                except:
                    continue
                mem_item = SentreeMembersSimpleItem()
                mem_item[u'phone'] = phone
                mem_item[u'name'] = name
                mem_item[u'card_no'] = card_no
                mem_item[u'card_name'] = card_name
                mem_item[u'card_type'] = card_type
                mem_item[u'discont'] = discont
                mem_item[u'timeout'] = timeout
#                 items.append(mem_item)
                yield mem_item
        meta = resp.meta
        next_page_nodes = hxs.xpath('//a[@class="next_page"]')
        if next_page_nodes and (len(next_page_nodes) > 1 or meta['page'] == 1):
            page = meta['page'] + 1
            meta['page'] = page
            yield FormRequest(url="http://vip6.sentree.com.cn/shair/memberInfo!memberlist.action", formdata={
                         'page.currNum' : str(page),
                         'page.rpp' : '30',
                         'r' : str(meta['r']),
                         'set' : 'manage'
                         }, callback=self.parse_showdesk_members2, meta=meta)

    def parse_showdesk_employees(self, resp):
        hxs = Selector(resp)
        headers = hxs.xpath('//form[@id="employeeInfo"]//table/thead/tr/th/child::text()').extract()
        if not headers:
            self.log('%s can not find table headers.' % self.name, level=log.ERROR)
            yield None
            return
        employee_nodes = hxs.xpath('//form[@id="employeeInfo"]//table/tbody/tr')
        if not employee_nodes:
            self.log('%s can not find employees info' % self.name, level=log.ERROR)
            yield None
            return
        for e_n in employee_nodes:
            info_nodes = e_n.xpath('td')
            info = OrderedDict({})
            for idx, i_n in enumerate(info_nodes):
                if idx == 0 or idx == len(info_nodes) - 1:
                    continue
                info[headers[idx]] = ' | '.join(str_list_strip_replace(i_n.xpath('descendant::text()').extract(), [' ', '\t', '\n']))

            item = SentreeEmployeeItem()
            item['info'] = info
#             items.append(info)
            yield item

    def parse_showdesk_services(self, resp):
        hxs = Selector(resp)
        headers = hxs.xpath('//table[@id="itemset"]/thead/tr/th/child::text()').extract()
        if not headers:
            self.log('%s can not find table headers.' % self.name, level=log.ERROR)
            yield None
            return
        service_nodes = hxs.xpath('//table[@id="itemset"]/tbody/tr')
        if not service_nodes:
            self.log('%s can not find services info' % self.name, level=log.ERROR)
            yield None
            return
        for s_n in service_nodes:
            info_nodes = s_n.xpath('td')
            info = OrderedDict({})
            no = None
            for idx, i_n in enumerate(info_nodes):
                if idx == 0 or idx == len(info_nodes) - 1:
                    continue
                if idx == 8:
                    info[headers[idx]] = str_list_strip_replace(str_list_strip(hxs.xpath('//span[@id="pricespan%s"]' % no).xpath('child::text()').extract()), [' ', '\t', '\n'])
                    continue
                if idx == 9:
                    discount_nodes = i_n.xpath('.//div[starts-with(@id, "icddiv")]')
                    discounts = []
                    if discount_nodes:
                        for d_n in discount_nodes:
                            discounts.append(' | '.join(str_list_strip_replace(str_list_strip(d_n.xpath('./child::text()').extract()), [' ', '\t', '\n'])))
                    info[headers[idx]] = ' ||| '.join(discounts)
                    continue
                info[headers[idx]] = ' | '.join(str_list_strip_replace(str_list_strip(i_n.xpath('descendant::text()').extract()), [' ', '\t', '\n']))
                if idx == 1:
                    no = info[headers[idx]]

            item = SentreeServiceItem()
            item['info'] = info
#             items.append(info)
            yield item


    def parse_showdesk_membercards(self, resp):
        hxs = Selector(resp)
        headers = hxs.xpath('//form[@id="cardTypeForm"]//table/thead/tr/th/child::text()').extract()
        if not headers:
            self.log('%s can not find table headers.' % self.name, level=log.ERROR)
            yield None
            return
        employee_nodes = hxs.xpath('//form[@id="cardTypeForm"]//table/tbody/tr')
        if not employee_nodes:
            self.log('%s can not find member card info' % self.name, level=log.ERROR)
            yield None
            return
        for e_n in employee_nodes:
            info_nodes = e_n.xpath('td')
            info = OrderedDict({})
            for idx, i_n in enumerate(info_nodes):
                if idx == 0 or idx == len(info_nodes) - 2:
                    continue
                if idx == len(info_nodes) - 1:
                    info[headers[idx]] = ' | '.join(str_list_strip_replace(i_n.xpath('./child::text()').extract(), [' ', '\t', '\n', '&nbsp;']))
                    continue
                sep = ' | '
                if idx == 3:
                    sep = ''
                info[headers[idx]] = sep.join(str_list_strip_replace(str_list_strip(i_n.xpath('descendant::text()').extract()), [' ', '\t', '\n', '&nbsp;']))

            item = SentreeMemberCardItem()
            item['info'] = info
#             items.append(info)
            yield item

items = []

if __name__ == '__main__':
    f = open('e:\\1.html')

    html = ""
    for l in f:
        html += l
    f.close()

    resp = TextResponse(url="", body=html)
    s = SentreeSpider()
    try:
        s.parse_showdesk_services(resp)
    except:
        print traceback.format_exc()

    print json.dumps(obj=items, ensure_ascii=False, indent=4)
#     sys.exit(0)
#
#     SentreeSpider().parse_consumer_bill_stream_validate(resp)
#
#     datas = []
#     for item in items:
#         datas.append(item['data'])
#     rf = open('e:\\res.json', 'w')
#     rf.write(json.dumps(obj=datas, ensure_ascii=False, indent=4))
#     rf.flush()
#     rf.close()
#
#     writer = None
#     init = False
#
#     def gene_row(data, row=[]):
#         if type(data) == list:
#             b = data[-1]
#             if b:
#                 v = data[0]
#                 if type(v) == list:
#                     try:
#                         row.append(' | '.join(v))
#                     except:
# #                         print 111, json.dumps(obj=v, ensure_ascii=False, indent=4)
#                         print 111, b
#                 else:
#                     row.append(v)
#             else:
#                 data = data[0:-1]
#                 for v in data:
#                     if b:
#                         if type(v) == list:
#                             try:
#                                 row.append(' | '.join(v))
#                             except:
# #                                 print 222, json.dumps(obj=v, ensure_ascii=False, indent=4)
#                                 print 222, b
#                         else:
#                             row.append(v)
#                     else:
#                         gene_row(v, row)
#         elif type(data) == OrderedDict:
#             for _, v in data.items():
#                 gene_row(v, row)
#         else: # 不可能不是list或者dict
#             pass
#         return row
#
#     for item in items:
#         if not init:
#             fn = '-'.join(item['menu'])
#             writer = csv.writer(file('e:\\%s.csv' % fn, 'wb'))
#             writer.writerow(item['headers'])
#             init = True
#         row = gene_row(item['data'])
#         print json.dumps(obj=row, ensure_ascii=False, indent=4)
#         writer.writerow(row)
#         break
#
#
#
#
#
#
#
#
#
#
#
#
#
#


