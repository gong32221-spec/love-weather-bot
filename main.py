import requests
import yagmail
import os  # 读取云端密码
import time
import urllib3

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 配置区 =================
# 密码和邮箱从 GitHub 环境变量读取，安全！
SENDER_EMAIL = os.environ["1431457301@qq.com"]
SENDER_PASSWORD = os.environ["zkwtbaiumhvdiajb"]
RECEIVER_EMAIL = os.environ["12085660@qq.com"]
CITY = "Yiwu"


# ==========================================

def get_weather_data():
    """ 死磕模式：获取天气数据，失败会自动重试 """
    url = f"http://wttr.in/{CITY}?format=j1"
    headers = {"User-Agent": "Mozilla/5.0"}

    for i in range(1, 6):  # 最多试 5 次
        try:
            print(f">>> 正在尝试第 {i} 次连接...")
            # verify=False 解决 SSL 报错，timeout=10 防止卡死
            response = requests.get(url, headers=headers, timeout=10, verify=False)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 502:
                print("⚠️ 服务器忙 (502)，休息 3 秒...")
                time.sleep(3)
            else:
                print(f"⚠️ 状态码异常: {response.status_code}")

        except Exception as e:
            print(f"⚠️ 连接出错: {e}")
            time.sleep(3)

    return None


def run_task():
    print(f">>> 🚀 云端机器人启动！坐标：{CITY}")

    data = get_weather_data()

    if data:
        # 解析数据
        current = data['current_condition'][0]
        temp = current['temp_C']
        humidity = current['humidity']

        # 智能获取天气描述 (优先中文)
        if 'lang_zh' in current:
            weather = current['lang_zh'][0]['value']
        else:
            weather = current['weatherDesc'][0]['value']

        # ============================================
        # ☔ 核心逻辑修改：只有坏天气才发邮件
        # ============================================
        bad_weather_keywords = ['雨', '雪', '雷', '冰雹']

        # 检查天气描述里有没有上面那些字
        if any(keyword in weather for keyword in bad_weather_keywords):
            print(f"☔ 检测到坏天气 ({weather})，正在发送警报...")

            # 定义一句贴心的警报语
            warning_msg = "⚠️ <b>外面正在下雨/雪，出门千万别忘带伞！</b>"

            send_email(CITY, weather, temp, humidity, warning_msg)
        else:
            # 如果是晴天/阴天，直接结束，不发邮件
            print(f"🌞 今天天气不错 ({weather})，不打扰主人，任务结束。")

    else:
        print("❌ 5次尝试全失败，今日跳过。")


def send_email(city, weather, temp, humidity, warning_msg):
    try:
        yag = yagmail.SMTP(user=SENDER_EMAIL, password=SENDER_PASSWORD, host='smtp.qq.com')

        # 标题改成【早安】，并加上【带伞】标记
        subject = f"【带伞提醒】早安！{city}正在{weather}，记得带伞"

        contents = [
            f"<h2 style='color: red;'>{warning_msg}</h2>",  # 警报语放大标红
            "<hr>",
            "<h3 style='color: pink;'>宝宝爱你(≧∇≦)/</h3>",
            f"<p>城市: {city}</p>",
            f"<p>天气: {weather}</p>",
            f"<p>温度: {temp}°C</p>",
            f"<p>湿度: {humidity}%</p>",
            "<br>",
            "<p style='color: gray; font-size: 12px;'>-- 你的专属气象员</p>"
        ]

        yag.send(to=RECEIVER_EMAIL, subject=subject, contents=contents)
        print(">>> ✅ 提醒邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")


if __name__ == '__main__':
    run_task()