import argparse
import json
import requests
import os
from requests_toolbelt import MultipartEncoder


def parse_args():
    parser = argparse.ArgumentParser(description="Lark Suite Image Sender")
    parser.add_argument("--chat_id", type=str, required=False, help="The chat_id of the recipient")
    parser.add_argument("--open_id", type=str, required=False, help="The open_id of the recipient")
    parser.add_argument("--image_path", type=str, required=True, help="Path to the image you want to send")
    args = parser.parse_args()

    if not args.chat_id and not args.open_id:
        parser.error("One of --chat_id or --open_id must be provided")

    return args


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


def upload_image(token, image_path):
    url = "https://open.larksuite.com/open-apis/im/v1/images"
    with open(image_path, "rb") as f:
        form = {
            "image_type": "message",
            "image": f
        }
        multi_form = MultipartEncoder(form)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": multi_form.content_type
        }
        response = requests.post(url, headers=headers, data=multi_form)
        response.raise_for_status()
        image_key = response.json().get("data", {}).get("image_key")
        return image_key


def send_message(token, chat_id, open_id, image_key):
    if chat_id:
        receive_id_type = "chat_id"
        receive_id = chat_id
    else:
        receive_id_type = "open_id"
        receive_id = open_id

    url = f"https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type={receive_id_type}"
    payload = {
        "receive_id": receive_id,
        "content": json.dumps({
            "image_key": image_key,
            "alt": "Image"
        }),
        "msg_type": "image"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()


def main():
    args = parse_args()
    token = get_token()
    image_key = upload_image(token, args.image_path)
    send_message(token, args.chat_id, args.open_id, image_key)
    return 'Image sent successfully!'


if __name__ == "__main__":
    main()
