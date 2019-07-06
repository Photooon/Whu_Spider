import csv
import requests
import datetime
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup

eurl = 'http://218.197.150.140'                                     #教务系统
eurl_login = 'http://218.197.150.140/servlet/Login'                 #登录url
eurl_re = 'http://218.197.150.140/stu/stu_index.jsp'                #反馈url
eurl_image = 'http://218.197.150.140/servlet/GenImg'                #image的url
eurl_score = 'http://218.197.150.140/servlet/Svlt_QueryStuScore'    #成绩单url

uid = '2018302120319'                                               #在此处填入学号
upwd = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'                           #在此处填入在chrome中找到的加密后密码

'''Get image'''
def get_image(se, url):
    res_img = se.get(url)
    raw_image = res_img.content
    with open('image.png', 'wb+') as wf:                    #这里好像必须得这样先写入再打开，无法从byte类型转为Image类型
        wf.write(raw_image)

    image = Image.open('image.png', 'r')
    return image
'''/Get image'''

'''Process image'''
# 二值化和降噪处理
def process_img(raw_img):
    # 二值化
    raw_img = raw_img.convert("L")
    pixels = raw_img.load()
    for x in range(raw_img.width):
        for y in range(raw_img.height):
            if pixels[x, y] > 150:                              #这里的150可以根据图片特性更改
                pixels[x, y] = 255
            else:
                pixels[x, y] = 0
    # 降噪处理
    data = raw_img.getdata()
    w, h = raw_img.size
    count = 0
    for x in range(1, w - 1):
        for y in range(1, h - 1):
            # 找出各个像素方向
            mid_pixel = data[w * y + x]
            if mid_pixel == 0:
                top_pixel = data[w * (y - 1) + x]
                left_pixel = data[w * y + (x - 1)]
                down_pixel = data[w * (y + 1) + x]
                right_pixel = data[w * y + (x + 1)]

                if top_pixel == 0:
                    count += 1
                if left_pixel == 0:
                    count += 1
                if down_pixel == 0:
                    count += 1
                if right_pixel == 0:
                    count += 1
                if count > 4:
                    raw_img.putpixel((x, y), 0)

    # 去除所有边界噪点                              #根据观察，除了下边界之外，其他三条边是不会有有意义的内容的，所以删掉
    for x in range(0, w):
        raw_img.putpixel((x, 0), 255)
        raw_img.putpixel((x, 1), 255)
    for y in range(0, h):
        raw_img.putpixel((0, y), 255)
        raw_img.putpixel((1, y), 255)
        raw_img.putpixel((w - 1, y), 255)
        raw_img.putpixel((w - 2, y), 255)

    # 去除单值点                                    #更好的方法是搜索圈，发现如果是小于等于三个点的即判断为噪点除去（但是我太懒了hhh）
    for x in range(1, w - 2):
        for y in range(1, h - 2):
            mid_pixel = data[w * y + x]
            if mid_pixel < 125:
                top_pixel = data[w * (y - 1) + x]
                left_pixel = data[w * y + (x - 1)]
                down_pixel = data[w * (y + 1) + x]
                right_pixel = data[w * y + (x + 1)]

            count = 0
            if top_pixel < 125:
                count += 1
            if left_pixel < 125:
                count += 1
            if down_pixel < 125:
                count += 1
            if right_pixel < 125:
                count += 1

            if count == 0:
                raw_img.putpixel((x, y), 255)

    return raw_img
'''/Process image'''

'''Get token'''
def input_token(image):
    image.show()                    #会调用系统默认程序查看该图片
    return input()

def auto_token(pro_image):
    v_code = pytesseract.image_to_string(pro_image, 'num')		#num可以替换成自己训练的数据

    str = ""
    for ch in v_code:                       #有时会识别出空字符，全部处理掉。同时只保留前四个字符（有时会多余四个）
        if ch != " ":
            str += ch
        if len(str) > 3:
            break

    if len(str) < 4:                      # 如果不足4个字符，干脆返回空串表示识别失败
        return ""
    else:
        return str
'''/Get token'''

'''构造请求参数'''
def query_url(raw_url, token):              #这段写的好傻
    str = raw_url
    str += '?csrftoken=' + token
    str += '&year=0&term=&learnType=&scoreFlag=0&t='

    now = datetime.datetime.now()
    str += now.strftime('%a')
    str += '%20'
    str += now.strftime('%b')
    str += '%20'
    str += now.strftime('%d')
    str += '%20'
    str += now.strftime('%Y')
    str += '%20'
    str += now.strftime('%H:%M:%S')
    str += '%20'
    str += 'GMT+0800%20(%D6%D0%B9%FA%B1%EA%D7%BC%CA%B1%BC%E4)'
    return str
'''/构造请求参数'''

'''登录教务系统'''
session = requests.Session()

image = get_image(session, eurl_image)              #获取图片并处理图片
pro_img = process_img(image)

headers_login = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Length': '64',
    'Content-Type': 'application/x-www-form-urlencoded',
    #'Cookie': 'userLanguage=zh-CN; JSESSIONID=FE85C34F9AEBE560BCF30FE49BBF3BE3',
    'Host': '218.197.150.140',
    'Origin': 'http://218.197.150.140',
    'Referer': 'http://218.197.150.140/servlet/Login',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64;  x64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
}

postdata_login = {'id': uid, 'pwd': upwd, 'xdvfb': input_token(image)}              #这里调用input_token是手动输入，可以换成auto_token（OCR识别）

login_html = session.post(eurl_login, postdata_login, headers_login)

if login_html.url == eurl_login:
    print('Failed')
    login_in = False
else:
    print('Successful')
    login_in = True

    lbs = BeautifulSoup(login_html.content, 'lxml')     # 获取csrftoken
    str = lbs.find(name= 'div',id= 'system')
    token = ''
    for i in range(65, 101):
        token += str['onclick'][i]
    #print(token)

'''/登录教务系统'''

'''获取所有成绩'''
if login_in:
    headers_score = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Cookie': 'userLanguage = zh - CN; JSESSIONID=',
        'Host': '218.197.150.140',
        'Referer': 'http://218.197.150.140/stu/stu_score_parent.jsp',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    }

    headers_score['Cookie'] = headers_score['Cookie'] + session.cookies['JSESSIONID']       #填入session的Cookie

    course_html = session.get(query_url(eurl_score, token), headers= headers_score)

    if course_html.status_code == 200:          #如果拿到了成绩单html
        get_course = True
    else:
        get_course = False

else:
    get_course = False

'''/获取所有成绩'''

'''处理页面并存为csv'''
if get_course:
    cbs = BeautifulSoup(course_html.content, 'lxml')
    trs = cbs.find_all('tr')

    with open('data.csv', mode='w') as csv_file:
        fieldnames = ['Course', 'Credit', 'Teacher', 'Score']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(len(trs)):
            if i != 0:                 #开头是行标，不记录
                tds = trs[i].find_all('td')
                if tds[10].string == None:
                    writer.writerow({'Course': tds[0].string, 'Credit': tds[4].string, 'Teacher': tds[5].string,
                                     'Score': 'None'})
                else:
                    writer.writerow({'Course': tds[0].string, 'Credit': tds[4].string, 'Teacher': tds[5].string, 'Score': tds[10].string})
                                                # 更改下标可以获取其他信息，最大为11

'''/处理页面并存为csv'''
