#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 多个 Server酱 Key（用逗号分隔）
SERVERCHAN_KEYS = os.environ.get('SERVERCHAN_KEY','XUELIAN_KEY').split(',')
SERVERCHAN_KEYS = [k.strip() for k in SERVERCHAN_KEYS if k.strip()]

def get_weather():
    """获取北京天气"""
    try:
        # 使用 wtr.in 获取天气（免费，无需API Key）
        url = "https://wtr.in/Beijing?format=%C|%t|%h|%w"
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read().decode('utf-8').strip()
        
        parts = data.split('|')
        if len(parts) >= 2:
            condition = parts[0]
            temp = parts[1]
            return f"{condition} {temp}"
        return "天气获取失败"
    except Exception as e:
        return "天气获取失败"

def get_greeting(weather):
    """根据天气生成问候语"""
    hour = (datetime.utcnow() + timedelta(hours=8)).hour
    
    # 根据时间
    if 5 <= hour < 11:
        time_greeting = "早上好"
    elif 11 <= hour < 14:
        time_greeting = "中午好"
    elif 14 <= hour < 18:
        time_greeting = "下午好"
    else:
        time_greeting = "晚上好"
    
    # 根据天气添加提醒
    weather_tip = ""
    if "雨" in weather or "Rain" in weather:
        weather_tip = "☔ 今天有雨，记得带伞"
    elif "云" in weather or "Cloud" in weather:
        weather_tip = "☁️ 今天多云"
    elif "晴" in weather or "Clear" in weather or "Sunny" in weather:
        weather_tip = "☀️ 今天晴朗，心情不错"
    
    return time_greeting, weather_tip

def fetch_news():
    """抓取新闻"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    news_list = []
    
    # 新浪财经
    try:
        req = urllib.request.Request("https://finance.sina.com.cn/", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a'):
            t = a.get_text(strip=True)
            if t and 15 < len(t) < 80 and not any(x in t for x in ['图片', '视频', '更多', '>>']):
                news_list.append({"title": t, "source": "新浪"})
                if len(news_list) >= 6:
                    break
    except Exception as e:
        print(f"新浪抓取失败: {e}")
    
    # 东方财富
    try:
        req = urllib.request.Request("https://finance.eastmoney.com/", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a'):
            t = a.get_text(strip=True)
            if t and 15 < len(t) < 80 and '点击查看' not in t:
                news_list.append({"title": t, "source": "东财"})
                if len(news_list) >= 12:
                    break
    except Exception as e:
        print(f"东财抓取失败: {e}")
    
    return news_list[:10]

def classify_news(news_list):
    """分类新闻"""
    important_keywords = ['美联储', '央行', '降准', '降息', '金价', '原油', '港股', 'A股', '美股', '谈判', '停火', '涨', '跌']
    company_keywords = ['业绩', '财报', '亏损', '上市', '收购', '涨停', '跌停', '立案']
    
    important = []
    sectors = []
    companies = []
    
    for item in news_list:
        title = item['title']
        if any(kw in title for kw in important_keywords):
            important.append(item)
        elif any(kw in title for kw in company_keywords):
            companies.append(item)
        else:
            sectors.append(item)
    
    return important, sectors, companies

def format_content(weather, greeting, weather_tip, important, sectors, companies):
    """格式化推送内容"""
    today = (datetime.utcnow() + timedelta(hours=8))
    date_str = today.strftime('%m月%d日')
    weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][today.weekday()]
    
    lines = []
    
    # ===== 头部问候区 =====
    lines.append(f"# {greeting}！🌅")
    lines.append("")
    lines.append(f"📅 {date_str} {weekday} | 🌤️ 北京 {weather}")
    if weather_tip:
        lines.append(f"{weather_tip}")
    lines.append("")
    
    # ===== 提醒区 =====
    lines.append("---")
    lines.append("")
    lines.append("## 💊 每日提醒")
    lines.append("")
    lines.append("> **记得吃药！** 身体健康最重要 💪")
    lines.append("")
    
    # ===== 新闻区 =====
    lines.append("---")
    lines.append("")
    lines.append("## 📰 今日财经热点")
    lines.append("")
    
    if important:
        lines.append("### 🔴 重要")
        for item in important[:4]:
            lines.append(f"• {item['title']}")
        lines.append("")
    
    if sectors:
        lines.append("### 📊 板块")
        for item in sectors[:3]:
            lines.append(f"• {item['title']}")
        lines.append("")
    
    if companies:
        lines.append("### 🏢 公司")
        for item in companies[:3]:
            lines.append(f"• {item['title']}")
        lines.append("")
    
    # ===== 底部 =====
    lines.append("---")
    lines.append("")
    lines.append(f"⏰ 推送时间：{date_str} 07:00")
    lines.append("📊 数据来源：新浪财经、东方财富")
    lines.append("🤖 由你牛子自动推送")
    
    return "\n".join(lines)

def push_to_wechat(key, title, content):
    """推送到单个微信"""
    url = f"https://sctapi.ftqq.com/{key}.send"
    data = urllib.parse.urlencode({
        'title': title,
        'desp': content
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode())
            print(f"推送到 {key[:10]}... 结果: {result.get('errno') == 0}")
            return result.get('errno') == 0
    except Exception as e:
        print(f"推送到 {key[:10]}... 失败: {e}")
        return False

def main():
    print("=== 开始生成每日晨报 ===")
    
    # 获取天气和问候
    weather = get_weather()
    greeting, weather_tip = get_greeting(weather)
    print(f"天气: {weather}, 问候: {greeting}")
    
    # 获取新闻
    news_list = fetch_news()
    print(f"获取新闻 {len(news_list)} 条")
    
    # 分类
    important, sectors, companies = classify_news(news_list)
    
    # 格式化内容
    content = format_content(weather, greeting, weather_tip, important, sectors, companies)
    title = f"{greeting}！{greeting}晨报"
    
    print(f"标题: {title}")
    print(f"内容长度: {len(content)} 字符")
    
    # 推送到所有配置的 Key
    print(f"=== 开始推送到 {len(SERVERCHAN_KEYS)} 个用户 ===")
    success_count = 0
    for key in SERVERCHAN_KEYS:
        if push_to_wechat(key, title, content):
            success_count += 1
    
    print(f"推送完成: {success_count}/{len(SERVERCHAN_KEYS)} 成功")

if __name__ == '__main__':
    main()
