import json
import requests
import os
from requests_toolbelt import MultipartEncoder


def get_token():
    lark_token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    if not app_id or not app_secret:
        raise ValueError("LARK_APP_ID and LARK_APP_SECRET must be set in environment variables")

    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    resp = requests.post(lark_token_url, json=payload)
    resp.raise_for_status()
    token = resp.json().get("tenant_access_token")
    return token


class LarkImageSender:
    def __init__(self, chat_id=None, open_id=None, image_path=None):
        self.token = get_token()
        self.chat_id = chat_id
        self.open_id = open_id
        self.image_path = image_path

    def upload_image(self, image_path):
        url = "https://open.larksuite.com/open-apis/im/v1/images"
        with open(image_path, "rb") as f:
            form = {
                "image_type": "message",
                "image": f
            }
            multi_form = MultipartEncoder(form)
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": multi_form.content_type
            }
            response = requests.post(url, headers=headers, data=multi_form)
            response.raise_for_status()
            image_key = response.json().get("data", {}).get("image_key")
            return image_key


    def send_message(self):
        if self.chat_id:
            receive_id_type = "chat_id"
            receive_id = self.chat_id
        else:
            receive_id_type = "open_id"
            receive_id = self.open_id

        url = f"https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type={receive_id_type}"

        image_key = self.upload_image(self.image_path)

        payload = {
            "receive_id": receive_id,
            "content": json.dumps({
                "image_key": image_key,
                "alt": "Image"
            }),
            "msg_type": "image"
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        print('Image sent successfully!')
        return 'Image sent successfully!'


def start(image_path: str, chat_id: str = None, open_id: str = None):
    sender = LarkImageSender(chat_id=chat_id, open_id=open_id, image_path=image_path)
    return sender.send_message()

