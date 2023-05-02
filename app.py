import os
import dotenv
from loguru import logger
from pathlib import Path
from typing import Any, Tuple, Dict
from slack_bolt import App, Say
from slack_sdk.web import WebClient
from slack_bolt.adapter.socket_mode import SocketModeHandler
from ai import Ai
import ai as aiutil

dotenv.load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)
ai = Ai(OPENAI_API_KEY, Path("chatlog.jsonl"))
client = WebClient(token=SLACK_BOT_TOKEN)


@app.message("")
def message_hello(message: Dict, say: Say):
    logger.info(f"メッセージを受信しました。'{message['text']}'")
    channel_id = message["channel"]
    thread_ts = message.get("thread_ts", message.get("ts"))
    # スレッドメッセージを取得する。
    replies = client.conversations_replies(channel=channel_id, ts=thread_ts)
    logger.info(f"スレッドメッセージを取得しました。({len(replies.data)}個)")
    # スレッドのメッセージをAIに渡す。
    messages = chatbot.create_request_messages(replies.data["messages"])
    # AIに送信する。
    res_text, _ = ai.chatgpt(messages)
    logger.info(f"AIメッセージを取得しました。'{res_text}'")
    # slackに投稿する。
    say(res_text, icon_emoji=":wave:", thread_ts=thread_ts)
    logger.info(f"応答が完了しました。")



class Chatbot:
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.context_messages = ai.constuct_messages(self.create_context)


    def create_context(self, s, u, a):
        return [
            s("あなたは全知全能のAIです。"),
            u("こんにちは。"),
            a("私は全知全能のAIです。なんの用だ。"),
        ]


    def create_request_messages(self, replies: list[dict]):
        messages = []
        messages.extend(self.context_messages)
        for reply in replies:
            # reply["icons"]["emoji"]
            if reply.get("bot_id") == self.bot_id:
                messages.append(aiutil.message_of_assistant(reply["text"]))
            else:
                messages.append(aiutil.message_of_user(reply["text"]))
        return messages


if __name__ == "__main__":
    # 自身のuser_idを取得する。
    response = client.auth_test()
    user_id = response["user_id"]
    bot_id = response["bot_id"]
    chatbot = Chatbot(bot_id)

    # app.start(port=int(os.environ.get("PORT", 3000)))
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
