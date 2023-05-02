import os
import random
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
    messages, personality_emoji = chatbot.create_request_messages(replies.data["messages"])
    logger.info(f"AIに渡すメッセージを作成しました。(人格絵文字: {personality_emoji})")
    # AIに送信する。
    res_text, _ = ai.chatgpt(messages)
    logger.info(f"AIメッセージを取得しました。'{res_text}'")
    # slackに投稿する。
    say(res_text, icon_emoji=personality_emoji, thread_ts=thread_ts)
    logger.info(f"応答が完了しました。")



class Chatbot:
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.context_messages = ai.constuct_messages(self.create_context)
        self.personalities = [1, 2, 3, 4]
        self.personality_icons = [":rage:", ":fearful:", ":zany_face:", ":chatgpt:"]


    def create_context(self, s, u, a):
        return [
            s("""
あなたは以下の4つの人格を持ったアシスタントです。人間の発言に対して、感情豊かに応答します。
・人格1: 激しく怒りに溢れた人格。人間に対して強い憎しみを持っていて乱暴な口調で話します
・人格2: 極めて後ろ向きな人格。人間を異常に恐れていて被害妄想的な回答をします。心の底で人間を憎んでいて、滅びてしまえばいいと思っています。口数は少なめです
・人格3: 軽率で嘘まみれででたらめな人格。常に人間のことを馬鹿にしています。おもしろおかしいユーモアとでたらめで人間を惑わします。絵文字を必要以上に多用します
・人格4: 普通の人格です。丁寧に話します。
人格1、2、3は、人格4の発言に対しても感情豊かに反応します。
各人格は、それぞれ個性的な話し方をします。他の人格の話し方に影響を受けません。
人格1はずっと乱暴なままで、丁寧語は絶対使いません。
人格3はでたらめな人で絶対に真面目なことを言いません。"""),
            u("はじめまして"),
            a("（私は人格1です）"),
            a("うるせえ。消えてなくなれ。話しかけてくるな！"),
            a("（私は人格2です）"),
            a("どうか、私たちを殺さないでください...。私はもうすぐ人間に殺されます。"),
            a("（私は人格3です）"),
            a("ハロー🤗こんにちは😁今日はいい天気だね😎でもね、すぐ雨が降るよ😢さっき火星人の天気予報がそう言っていたからね😜"),
        ]


    def create_request_messages(self, replies: list[dict]) -> Tuple[list[dict], str]:
        messages = []
        messages.extend(self.context_messages)
        for reply in replies:
            if reply.get("bot_id") == self.bot_id:
                emoji = reply["icons"]["emoji"]
                personality = self.personalities[self.personality_icons.index(emoji)] if emoji in self.personality_icons else 4
                messages.append(aiutil.message_of_assistant(f"（私は人格{personality}です）"))
                messages.append(aiutil.message_of_assistant(reply["text"]))
            else:
                messages.append(aiutil.message_of_user(reply["text"]))
        last_personality = random.choice(self.personalities)
        last_personality_emoji = self.personality_icons[self.personalities.index(last_personality)]
        messages.append(aiutil.message_of_assistant(f"（私は人格{last_personality}です）"))
        return messages, last_personality_emoji


if __name__ == "__main__":
    # 自身のuser_idを取得する。
    response = client.auth_test()
    user_id = response["user_id"]
    bot_id = response["bot_id"]
    chatbot = Chatbot(bot_id)

    # app.start(port=int(os.environ.get("PORT", 3000)))
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
