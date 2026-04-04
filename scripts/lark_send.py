import json
import logging
import requests
import os
from requests_toolbelt import MultipartEncoder

BASE_URL = os.getenv("LARK_BASE_URL", "https://open.larksuite.com")

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "run.log")


def _get_logger():
    os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
    logger = logging.getLogger("rcomfyui")
    if not logger.handlers:
        handler = logging.FileHandler(_LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(module)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def get_token():
    log = _get_logger()
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    if not app_id or not app_secret:
        raise ValueError("LARK_APP_ID and LARK_APP_SECRET must be set in environment variables")

    url = f"{BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
    log.info("POST %s | app_id=%s", url, app_id)
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=30)
    log.info("Response %d | %s", resp.status_code, resp.text)
    resp.raise_for_status()
    token = resp.json().get("tenant_access_token")
    return token


class LarkFileSender:
    def __init__(self, chat_id=None, file_path=None):
        self.log = _get_logger()
        self.token = get_token()
        self.chat_id = chat_id
        self.file_path = file_path

    def upload_image(self, file_path):
        url = f"{BASE_URL}/open-apis/im/v1/images"
        self.log.info("POST %s | file_path=%s", url, file_path)
        with open(file_path, "rb") as f:
            form = {
                "image_type": "message",
                "image": f
            }
            multi_form = MultipartEncoder(form)
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": multi_form.content_type
            }
            response = requests.post(url, headers=headers, data=multi_form, timeout=60)
        self.log.info("Response %d | %s", response.status_code, response.text)
        response.raise_for_status()
        image_key = response.json().get("data", {}).get("image_key")
        return image_key

    def upload_video(self, file_path):
        # 1) 先上传同名 png 作为封面图，拿 image_key
        png_path = os.path.splitext(file_path)[0] + ".png"
        if not os.path.exists(png_path):
            raise FileNotFoundError(f"Same-name PNG not found for MP4: {png_path}")

        image_key = self.upload_image(png_path)

        # 2) 再上传 mp4，拿 file_key
        url = f"{BASE_URL}/open-apis/im/v1/files"
        self.log.info("POST %s | file_path=%s", url, file_path)
        with open(file_path, "rb") as f:
            form = {
                "file_type": "mp4",
                "file_name": os.path.basename(file_path),
                "file": f,
                "duration": "8041"
            }
            print(form)
            multi_form = MultipartEncoder(form)
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": multi_form.content_type
            }
            response = requests.post(url, headers=headers, data=multi_form, timeout=60)

        self.log.info("Response %d | %s", response.status_code, response.text)
        response.raise_for_status()
        file_key = response.json().get("data", {}).get("file_key")

        return {
            "file_key": file_key,
            "image_key": image_key
        }

    def send_message(self):
        if self.chat_id.startswith("ou_"):
            receive_id_type = "open_id"
        else:
            receive_id_type = "chat_id"
        receive_id = self.chat_id

        url = f"{BASE_URL}/open-apis/im/v1/messages?receive_id_type={receive_id_type}"



        # 判断self.file_path是图片还是视频，目前仅支持这两种类型
        if self.file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):

            image_key = self.upload_image(self.file_path)

            payload = {
                "receive_id": receive_id,
                "content": json.dumps({
                    "image_key": image_key,
                    "alt": "Image"
                }),
                "msg_type": "image"
            }
            self.log.info(
                "POST %s | receive_id=%s receive_id_type=%s image_key=%s",
                url, receive_id, receive_id_type, image_key,
            )
        elif self.file_path.lower().endswith(".mp4"):
            media_keys = self.upload_video(self.file_path)
            payload = {
                "receive_id": receive_id,
                "msg_type": "media",
                "content": json.dumps({
                    "file_key": media_keys["file_key"],
                    "image_key": media_keys["image_key"]
                })
            }
            self.log.info(
                "POST %s | receive_id=%s receive_id_type=%s file_key=%s image_key=%s",
                url, receive_id, receive_id_type, media_keys["file_key"], media_keys["image_key"]
            )
        else:
            payload = {
                "receive_id": receive_id,
                "msg_type": "text",
                "content": json.dumps({
                    "text": "嘿嘿，好像文件有点对不上，没发出来"
                })
            }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        self.log.info("Response %d | %s", response.status_code, response.text)
        response.raise_for_status()

        return 'File sent successfully!'


def start(file_path: str, chat_id: str = None):
    sender = LarkFileSender(chat_id=chat_id, file_path=file_path)
    return sender.send_message()


if __name__ == '__main__':
    print(start(file_path="/Users/rexng/PycharmProjects/rComfyUI-t2i/output/ede46034-3832-4136-8298-fbed79a66069.mp4", chat_id="oc_05c5e4841b334bc11ec0a5c6678a1d7b"))