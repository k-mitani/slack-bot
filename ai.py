import json
from pathlib import Path
import datetime
import openai
from typing import Dict, Tuple, TypedDict
from openai.types.chat.completion_create_params import Function
from PIL import Image
import io
import base64

Message = TypedDict("Message", {"role": str, "content": str})

class Ai:
    def __init__(self, api_key: str, log_path: Path):
        openai.api_key = api_key
        self.log_path = log_path

    def chatgpt(self, messages: list[Message], functions: list[Function]) -> Tuple[str, Dict, Image]:
        req_time = datetime.datetime.now()
        model = "gpt-3.5-turbo-1106"
        # model = "gpt-3.5-turbo"
        response = openai.chat.completions.create(
            model=model,
            functions=functions,
            messages=messages,
            temperature=0.7,
        )
        res_time = datetime.datetime.now()
        self._write_log({
            "req_time": req_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": (res_time - req_time).total_seconds(),
            "model": model,
            "messages": messages,
            "response": response.model_dump_json(),
        })
        res = response.choices[0]
        if res.finish_reason == "function_call":
            if res.message.function_call.name == "generate_image":
                import json
                image_prompt = json.loads(res.message.function_call.arguments)["prompt"]
                try:
                    image_response = openai.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        size="1024x1024",
                        quality="standard",
                        response_format="b64_json",
                        n=1,
                    )
                except Exception as e:
                    image_response = openai.images.generate(
                        model="dall-e-3",
                        prompt="お花畑",
                        size="1024x1024",
                        quality="standard",
                        response_format="b64_json",
                        n=1,
                    )
                image = io.BytesIO(base64.b64decode(image_response.data[0].b64_json))
                return f"({image_prompt})", response, image

        return res.message.content, response, None
    
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

