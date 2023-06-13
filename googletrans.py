import configparser
from googletrans import Translator
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import quote
import hashlib
import os
import sys

# 从test.ini读取配置
with open('test.ini', mode='r') as f:
    ini_data = f.read()
config = configparser.ConfigParser()
config.read_string(ini_data)

# 获取指定配置项的值
def get_cfg(sec, name):
    return config.get(sec, name).strip('"')

# 修改指定配置项的值
def set_cfg(sec, name, value):
    config[sec][name] = '"%s"' % value

# 获取翻译的源语言和目标语言
def get_cfg_tra(sec):
    cc = config.get(sec, "action").strip('"')
    target = ""
    source = ""
    if cc == "auto":
        source = 'auto'
        target = 'zh-CN'
    else:
        source = cc.split('->')[0]
        target = cc.split('->')[1]
    return source, target

# 计算字符串的MD5值
def get_md5_value(src):
    _m = hashlib.md5()
    _m.update(src.encode('utf-8'))
    return _m.hexdigest()

# 逐个处理每个配置节
def tran(sec):
    global links
    out_dir = os.path.join(get_cfg('cfg', 'base'), get_cfg(sec, 'name'))
    url = get_cfg(sec, 'url')
    max_item = int(get_cfg(sec, 'max'))
    old_md5 = get_cfg(sec, 'md5')
    source, target = get_cfg_tra(sec)

    links += [" - %s [%s](%s) -> [%s](%s)\n" % (sec, url, url, get_cfg(sec, 'name'), quote(out_dir))]

    # 获取网页内容并计算MD5值
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36 LBBROWSER'}
    req = Request(url, headers=headers)
    try:
        html_doc = urlopen(req).read().decode('utf8')
        new_md5 = get_md5_value(html_doc)
    except:
        print("Error: " + url)
        return

    if old_md5 == new_md5:
        return
    else:
        set_cfg(sec, 'md5', new_md5)

    # 处理HTML数据并翻译
    html_doc = html_doc.replace('<?', '</s')
    html_doc = html_doc.replace('?>', '/>')
    soup = BeautifulSoup(html_doc, "html.parser")
    items = soup.find_all('item')
    for idx, e in enumerate(items):
        if idx > max_item:
            e.decompose()
    content = str(soup)
    content = content.replace('<title', '<stitle')
    content = content.replace('title>', 'stitle>')
    content = content.replace('<pubdate>', '<pubDate><span translate="no">')
    content = content.replace('</pubdate>', '</span></pubdate>')

    translator = Translator()
    _text = translator.translate(content, src=source, dest=target)

    with open(out_dir, 'w', encoding='utf-8') as f:
        c = _text.text
        c = c.replace('<stitle', '<title')
        c = c.replace('stitle>', 'title>')
        c = c.replace('<span translate="no">', '')
        c = c.replace('</span></pubdate>', '</pubDate>') # 对于ttrss需要为pubDate才会识别正确
        c = c.replace('&gt', '>') # &gt 会影响识别
        f.write(c)

    print("GT: " + url + " > " + out_dir)

# 逐个处理所有的配置节
secs = config.sections()
links = []
for x in secs[1:]:
    tran(x)
    print(config.items(x))

# 写入更新后的配置
with open('test.ini', 'w') as configfile:
    config.write(configfile)

# 更新文档映射
YML = "README.md"
f = open(YML, "r+", encoding="UTF-8")
list1 = f.readlines()
list1 = list1[:13] + links
f = open(YML, "w+", encoding="UTF-8")
f.writelines(list1)
f.close()