from os import get_terminal_size
import requests
from bs4 import BeautifulSoup
import re
import json
import datetime
import os
from requests.api import head
import time

#json.dumps(news, ensure_ascii=False)



def newsPost(data):
    headers = {'Accept': '*/*', 'Content-type':'application/json'}
    params_ = {"news": data}
    try: 
        res = requests.post('http://ec2-18-218-1-49.us-east-2.compute.amazonaws.com/crawler', 
        json=params_,
        headers=headers)
        return res
        
    except Exception as e:
        print(e)
        time.sleep(1)
        return None


def getRequestUrl(url, data):
    try: 
        res = requests.post(url, data=data)
        return res
        
    except Exception as e:
        print(e)
        print("[%s] Error for URL : %s" % (datetime.datetime.now(), url))
        return None

def crawler_index(today, page, last):
    result = []
    url = 'https://entertain.naver.com/now/page.json'
    data = {"sid":'106', 'date':'%s'%(today), 'page': '%d' %page}
    res = getRequestUrl(url,data)
    if res is None :
        return None, True
    html = json.loads(res.text)
    soup = BeautifulSoup(html['newsListHtml'], 'html.parser')
    ul = soup.select('li')
    for li in ul:
        if(li.text == "기사가 없습니다."):
            print('기사 없음')
            break
        link = "https://entertain.naver.com"+li.select_one('div.tit_area > a')['href']
        if last == link: 
            return result, True
        result.append(link)
    return result, False

def crawler(url):
    news={"title": "", "link": "", "text": "", "createdAt": ""}
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')

    selectors=['.end_tit','.article_info .author em', '#articeBody']
    title=soup.select_one(selectors[0]).get_text()
    time=soup.select_one(selectors[1]).get_text()
    content=soup.select_one(selectors[2]).get_text()

    news["title"] = remove(title)
    news["link"] = url
    news["text"] = remove(content)
    news["createdAt"] = getDate(time)
    return news

def remove(str):
    text = re.sub(r'[^\w]', ' ', str)
    text = ' '.join(text.split())
    return text

def getDate(time):
    time = remove(time).split(' ')
    year = time[0]
    month = time[1]
    day = time[2]
    if time[3] == '오후':
        hour = int(time[4])+12
    else:
        hour = int(time[4])
    minute = time[5]
    d = "%s-%s-%s-%02d:%s" %(year, month, day, hour, minute)
    return d


def init():
    now = datetime.datetime.now()
    today = now.date()
    with open('last_link.txt', 'r') as f:
        last = f.readline()
    
    data = []
    links = []
    for page in range(1,4):
        link, end = crawler_index(today=today, page=page, last=last)
        if link is None :
            break
        links.extend(link)
        if end:
            break

    if len(links) == 0:
        return

    last = links[0]
    with open('last_link.txt', 'w') as f:
        f.write(last)
    
    for url in reversed(links):
        time.sleep(2)
        data.append(crawler(url))
        if url == last:
            break

    res = newsPost(data=data)

    if not os.path.exists('./logs/%s/%s'%(now.month, now.day)):
            os.makedirs('./logs/%s/%s'%(now.month, now.day))

    with open('last_link.txt', 'w') as f:
        f.write(last)

    if len(res.text) == 0:
        with open('./logs/%s/%s/%s_log_data.txt'%(now.month, now.day, now.hour), 'a+') as log_data:
            log_data.write('time: %s\n' %now)
            log_data.write('code: %s\n' %res.status_code)
        return None
    else :
        with open('./logs/%s/%s/%s_log_data.txt'%(now.month, now.day, now.hour), 'a+') as log_data:
            log_data.write('time: %s\n' %now)
            log_data.write('code: %s\n' %res.status_code)
            log_data.write('text: %s\n' %(json(res.text)))
        return None

        

if __name__ == '__main__':
    time_now = datetime.datetime.now()
    now = time_now.minute
    init()
    while True:
        time_now = datetime.datetime.now()
        time.sleep(10)
        if now != time_now.minute:
            init()
            print(time_now)
            now = time_now.minute
