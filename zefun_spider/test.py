#coding: utf-8
import xlrd
import csv
import json
import thread
import sys
import xlwt
from items import SentreeMembersSimpleItem
from zefun_spider.utils import dama
import time
from urllib import urlencode, quote_plus

reload(sys)
sys.setdefaultencoding('utf-8')  # @UndefinedVariable

print urlencode({'' : u'西城店店长'})[1:]

a = {'1' : '1'}
for k,v in a.items():
    print k, v

# rand = dama.dama('%s?r=%d' % ('http://vip6.sentree.com.cn/shair/vc', time.time()))
# rand = None
# retry = 3
# while retry > 0 and not rand:
#     rand = dama.dama('%s?r=%d' % ('http://vip6.sentree.com.cn/shair/vc', time.time()))
#     retry -= 1
# print rand
# if rand:
#     FormRequest(url='http://vip6.sentree.com.cn/shair/loginAction!ajaxLogin.action', formdata={
#                      'login' : u'西城店店长',
#                      'passwd' : '15977340369dz',
#                      'rand' : rand
#                      }, callback=self.parse_login, headers={'Referer' : 'http://vip6.sentree.com.cn/shair/loginAction.action?from=base'})
# sys.exit(0)

member_xls = xlrd.open_workbook('e:\\memberinfo.xls')
member_sheet = member_xls.sheet_by_name(u'会员资料')
rows = member_sheet.nrows
headers = member_sheet.row_values(0)
print json.dumps(obj=headers, ensure_ascii=False)


# result_xls_writer = csv.writer(open("e:\\kkk.xls", 'wb'))
# print dir (result_xls_writer)
# result_xls_writer.writerow(['1', '2'])

wb = xlwt.Workbook()
s = wb.add_sheet(u'会员资料')
for i, h in enumerate(headers):
    s.write(0, i, h)
wb.save('e:\\kkk.xls')
for i, h in enumerate(headers):
    s.write(1, i, h)
wb.save('e:\\kkk.xls')
# def t(i):
#     print '%d\r\n' % i
#     result_xls_writer.writerow([i, i, i, i, i])
#
# for i in xrange(0, 100):
#     thread.start_new_thread(t, (i, ))
#
#
# while 1 == 1:
#     pass

print SentreeMembersSimpleItem().fields


