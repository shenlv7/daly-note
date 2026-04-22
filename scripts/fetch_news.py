#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

SERVERCHAN_KEY = os.environ.get('SERVERCHAN_KEY', '')
SERVERCHAN_URL = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"

def fetch_sina():
    url = "https://finance.sina.com.cn/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    news = []
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        if text and 15 < len(text) < 80:
            news.append({'title': text})
    return news[:8]

def fetch_eastmoney():
    url = "https://finance.eastmoney.com/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    news = []
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        if text and 15 < len(text) < 80 and '点击查看全文' not in text:
            news.append({'title': text})
    return news[:7]

def push_to_wechat(title, content):
    data = {'title': title, 'desp': content}
    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(SERVERCHAN_URL, data=encoded_data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    today_display = beijing_time.strftime('%m月%d日')
    
    sina = fetch_sina()
    east = fetch_eastmoney()
    all_news = sina + east
    
    lines = [f"## 📰 今日财经热点 ({today_display})", ""]
    for n in all_news[:12]:
        lines.append(f"• {n['title']}")
    lines.append(f"\n---\n⏰ 推送时间：{today_display} 07:00")
    
    content = "\n".join(lines)
    result = push_to_wechat(f"📰 财经早报 ({today_display})", content)
    print(result)

if __name__ == '__main__':
    main()
