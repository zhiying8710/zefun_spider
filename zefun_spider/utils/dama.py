# coding: utf-8
import time
import urllib2
import json

def dama(filename):
    return __jsdati_dama__(filename)

def __jsdati_dama__(filename):
#     urlretrieve(url, [filename=None, [reporthook=None, [data=None]]])
    boundary = '----%s' % hex(int(time.time() * 1000))
    data = ['--%s' % boundary]
    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'user_name')
    data.append('qq491642740')
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'user_pw')
    data.append('livesALL2015')
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'yzm_minlen')
    data.append('4')
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'yzm_maxlen')
    data.append('4')
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'yzmtype_mark')
    data.append('0')
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'zztool_token')
    data.append('qq491642740')
    data.append('--%s' % boundary)

    fr=open(filename,'rb')
    data.append('Content-Disposition: form-data; name="%s"; filename="b.png"' % 'upload')
    data.append('Content-Type: %s\r\n' % 'application/octet-stream')
    data.append(fr.read())
    fr.close()
    data.append('--%s--\r\n' % boundary)

    http_url='http://bbb4.hyslt.com/api.php?mod=php&act=upload'
    http_body='\r\n'.join(data)
    try:
        #buld http request
        req=urllib2.Request(http_url, data=http_body)
        #header
        req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
        #post data to server
        resp = urllib2.urlopen(req, timeout=5)
        #get response
        qrcont=resp.read()
        res = json.loads(s=qrcont)
        return res['data']['val']
    except Exception:
        return None




