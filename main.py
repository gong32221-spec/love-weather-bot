import requests
import yagmail
import os
import time
import urllib3

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 配置区 =================
SENDER_EMAIL = os.environ["MY_EMAIL"]
SENDER_PASSWORD = os.environ["MY_PASSWORD"]
RECEIVER_EMAIL = os.environ["MY_RECEIVER"]
CITY = "Yiwu"
# ==========================================

def get_weather_data():
    """ 获取天气数据，带重试 """
    url = f"http://wttr.in/{CITY}?format=j1"
    headers = {"User-Agent": "Mozilla/5.0"}

    for i in range(1, 6):
        try:
            print(f">>> 正在尝试第 {i} 次连接...")
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 502:
                time.sleep(3)
        except Exception as e:
            print(f"⚠️ 连接出错: {e}")
            time.sleep(3)
    return None

def run_task():
    print(f">>> 🚀 云端机器人启动！坐标：{CITY}")
    data = get_weather_data()

    if data:
        # 1. 获取【实时】温度（作为参考）
        current = data['current_condition'][0]
        temp = current['temp_C']
        humidity = current['humidity']

        # 2. 获取【今天全天】的预报
        # weather[0] 代表今天，weather[1] 代表明天
        today_forecast = data['weather'][0]
        hourly_data = today_forecast['hourly']
        
        # 定义坏天气关键词 (中英文都要，防止翻译失效)
        bad_weather_keywords = [
            '雨', '雪', '雷', '冰雹',  # 中文
            'Rain', 'Snow', 'Thunder', 'Drizzle', 'Showers' # 英文
        ]

        # 3. 核心升级：遍历今天每 3 小时的预报
        will_rain = False
        rain_desc = "" # 记录具体是什么雨

        # 检查当天的每个时间段
        for hour in hourly_data:
            # 尝试获取中文，没有就用英文
            if 'lang_zh' in hour:
                desc = hour['lang_zh'][0]['value']
            else:
                desc = hour['weatherDesc'][0]['value']
            
            # 打印出来调试看一看
            # print(f"时间段预报: {desc}") 

            # 只要有一个时间段包含坏天气，就标记为 True
            if any(keyword in desc for keyword in bad_weather_keywords):
                will_rain = True
                rain_desc = desc # 记录下来，比如 "小雨"
                break # 只要找到一次有雨，就不用往后找了，肯定要带伞

        # ============================================
        # ☔ 发送逻辑
        # ============================================
        if will_rain:
            print(f"☔ 查到了！今天预报中有：{rain_desc}，正在发送警报...")
            warning_msg = f"⚠️ <b>注意：今天预报有【{rain_desc}】，出门务必带伞！</b>"
            # 这里的 weather 参数传 rain_desc，让邮件标题直接显示“小雨”而不是实时的“阴”
            send_email(CITY, rain_desc, temp, humidity, warning_msg)
        else:
            # 如果跑遍了全天都没雨，才是真的没雨
            # 获取当前的实时天气描述用于日志
            if 'lang_zh' in current:
                current_desc = current['lang_zh'][0]['value']
            else:
                current_desc = current['weatherDesc'][0]['value']
            print(f"🌞 检查了全天预报，没有发现雨雪。实时天气：{current_desc}。")

    else:
        print("❌ 获取数据失败。")

def send_email(city, weather, temp, humidity, warning_msg):
    try:
        yag = yagmail.SMTP(user=SENDER_EMAIL, password=SENDER_PASSWORD, host='smtp.qq.com')
        
        # 标题高能预警
        subject = f"【带伞提醒】早安！{city}今天有{weather}，别忘带伞"

        contents = [
            f"<h2 style='color: red;'>{warning_msg}</h2>",
            "<hr>",
            "<h3 style='color: pink;'>宝宝爱你(≧∇≦)/</h3>",
            f"<p>城市: {city}</p>",
            f"<p>今天天气: {weather}</p>",
            f"<p>实时温度: {temp}°C</p>",
            f"<p>实时湿度: {humidity}%</p>",
            "<br>",
            "<p style='color: gray; font-size: 12px;'>-- 你的全天候气象雷达</p>"
        ]

        yag.send(to=RECEIVER_EMAIL, subject=subject, contents=contents)
        print(">>> ✅ 提醒邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == '__main__':
    run_task()
