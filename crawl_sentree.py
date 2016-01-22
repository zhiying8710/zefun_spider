#coding: utf-8
import sys
from optparse import OptionParser
import os
import multiprocessing
import threading
from zefun_spider.utils.conns_helper import RedisHelper
import time
from zefun_spider.settings import running_auths_key
reload(sys)
sys.setdefaultencoding('utf-8')  # @UndefinedVariable

def _start_crawl(workpath, auth, semaphore):
    cwd = os.getcwd()
    try:
        os.chdir(workpath)
        os.system("""scrapy crawl -a username='%s' -a password='%s' sentree""" % (auth[0], auth[1]))
    finally:
        semaphore.release()
        os.chdir(cwd)

def _check_path(path, parser, is_file=False):
    err = False
    if not path:
        err = True
    if not err and not path.startswith('/'):
        print u'文件%s必须时绝对路径' % path
        err = True
    if not err and not os.path.exists(path):
        print u'%s不存在' % path
        err = True
    if not err and is_file and not os.path.isfile(path):
        print u'%s不是一个文件' % path
        err = True
    if err:
        parser.print_help()
        sys.exit(0)

def start(options, tp='file'):
    threads = options.threads
    if threads < 1:
        print u'threads必须是大于0的整数'
        parser.print_help()
        sys.exit(0)
    workpath = options.workpath
    delimiter = options.delimiter
    semaphore = multiprocessing.Semaphore(threads)
    if tp == 'file':
        authfile = options.authfile
        auths = []
        f = open(authfile, 'r')
        for l in f:
            l = l.strip()
            auth = l.split(delimiter)
            if len(auth) < 2:
                print u'%s 的分隔符与配置不符' % l
                continue
            auths.append((auth[0], auth[1]));
        print u'%s中账号和密码的个数为%d' % (authfile, len(auths))
        if auths:
            for auth in auths:
                semaphore.acquire()
                threading.Thread(target=_start_crawl,args=(workpath, auth, semaphore)).start()
            while semaphore.get_value() != threads:
                pass
            print 'all done...'
    elif tp == 'redis':
        auth_key = options.auth_key
        rconn=RedisHelper.get_redis_conn()
        while 1:
            info = rconn.lpop(auth_key)
            if not info:
                time.sleep(1)
                continue
            auth = info.split(delimiter)
            if len(auth) < 2:
                print u'%s 的分隔符与配置不符' % info
                continue
            if rconn.sismember(running_auths_key, auth[0]):
                print u'%s 该用户名的数据正在抓取中, 请等待本次抓取完成后再试' % info
                continue
            semaphore.acquire()
            threading.Thread(target=_start_crawl,args=(workpath, (auth[0], auth[1]), semaphore)).start()
    else:
        print u'不支持的账号信息保存类型'


parser = OptionParser('usage: python %prog -w <workpath> -a [authfile] -k [auth-key] -d [delimiter] -t [threads] ')
parser.add_option("-a", "--authfile", dest="authfile", help=ur"盛传系统的账号名和密码文件, 一行表示一个账号和密码")
parser.add_option("-d", "--delimiter", dest="delimiter", help=ur"账号密码的分隔符, 默认为\t, 传参时请用单引号引起来", default='\t')
parser.add_option("-w", "--workpath", dest="workpath", help=ur"爬虫所在目录")
parser.add_option("-t", "--threads", dest="threads", help=ur"线程数, 默认为1", default=1, type="int")
parser.add_option("-k", "--auth-key", dest="auth_key", help=ur"redis中存放账号信息的key")

if __name__ == '__main__':
    (options, args) = parser.parse_args(sys.argv)
    workpath = options.workpath
    _check_path(workpath, parser)

    authfile = options.authfile
    auth_key = options.auth_key
    if not authfile:
        if not auth_key:
            print u'不指定auth_file时, auth_key不能为空'
            parser.print_help()
            sys.exit(0)
        start(options, tp='redis')
    else:
        _check_path(authfile, parser, True)
        start(options)



