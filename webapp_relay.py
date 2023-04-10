import os
from flask import Flask, request, jsonify, abort
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DEST_HOST = os.environ.get("MY_DEST_HOST")
DEST_PORT = os.environ.get("MY_DEST_PORT")
MY_ENTRY_FUNC_NAME = os.getenv("MY_ENTRY_FUNC_NAME", "/callback")
DEST_ENTRY_FUNC_NAME = os.getenv("DEST_ENTRY_FUNC_NAME", "/callback")

# Line Messaging API 相关设置
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route(f"{MY_ENTRY_FUNC_NAME}", methods=["POST"])
def relay_callback():
    # 将签名从请求头中获取
    signature = request.headers["X-Line-Signature"]

    # 从请求中获取事件数据
    body = request.get_data(as_text=True)

    try:
        # 处理事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 注册事件处理器
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    user_input = event.message.text

    # 创建目标 URL
    dest_url = f"http://{DEST_HOST}:{DEST_PORT}/{DEST_ENTRY_FUNC_NAME}"

    # 创建要转发的数据
    data = {
        "user_id": user_id,
        "user_input": user_input,
    }

    # 转发请求到目标 Web 应用程序
    response = requests.post(dest_url, json=data)
    response_data = response.json()

    # 从响应中获取要发送给用户的消息
    response_message = response_data.get("message")

    # 向用户发送消息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_message)
    )
    
    # 将目标 Web 应用程序的响应返回给客户端
    # return jsonify(response.json()), response.status_code

if __name__ == "__main__":
    app.run()
