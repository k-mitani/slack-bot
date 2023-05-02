import json
from pathlib import Path
import datetime
import openai
from typing import Dict, Tuple, TypedDict

Message = TypedDict("Message", {"role": str, "content": str})

class Ai:
    def __init__(self, api_key: str, log_path: Path):
        openai.api_key = api_key
        self.log_path = log_path

    def chatgpt(self, messages: list[Message]) -> Tuple[str, Dict]:
        req_time = datetime.datetime.now()
        model = "gpt-3.5-turbo"
        response = openai.ChatCompletion.create(model=model, messages=messages)
        res_time = datetime.datetime.now()
        self._write_log({
            "req_time": req_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": (res_time - req_time).total_seconds(),
            "model": model,
            "messages": messages,
            "response": response
        })
        text = response["choices"][0]["message"]["content"]
        return text, response
    
    def _write_log(self, json_data: Dict):
        with open(self.log_path, "a", encoding="utf8") as f:
            f.write(json.dumps(json_data, ensure_ascii=False))
            f.write("\n")
    
    def constuct_messages(self, fn) -> list[Message]:
        return fn(message_of_system, message_of_user, message_of_assistant)


def _message(role: str, message: str) -> Message:
    return {"role": role, "content": message.strip()}

def message_of_system(message: str) -> Message:
    return _message("system", message)

def message_of_user(message: str) -> Message:
    return _message("user", message)

def message_of_assistant(message: str) -> Message:
    return _message("assistant", message)

