import configparser
import io
import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request
import uuid

import websocket
from PIL import Image


def _load_config() -> dict:

    config = configparser.ConfigParser()
    if not config.read("config.ini"):
        raise FileNotFoundError(f"Config file not found or unreadable: config.ini")
    if "config" not in config:
        raise KeyError("Missing [config] section in config.ini")

    c = config["config"]
    if "model" not in c or not c["model"].strip():
        raise ValueError("Missing required 'model' setting in [config] section of config.ini")

    return {
        "server": os.getenv("COMFYUI_SERVER_ADDRESS", "localhost:8188"),
        "model": c["model"],
        "image_width": c.getint("image-width", 512),
        "image_height": c.getint("image-height", 512),
        "steps": c.getint("steps", 28),
        "cfg": c.getfloat("cfg", 8.0),
        "sampler": c.get("sampler", "euler"),
        "scheduler": c.get("scheduler", "sgm_uniform"),
        "denoise_strength": c.getfloat("denoise_strength", 1.0),
    }


class ComfyUIClient:
    def __init__(self, positive_prompt: str, negative_prompt: str = '', output_name: str = None):
        self.config = _load_config()

        if not positive_prompt:
            raise ValueError("positive_prompt is empty. Please provide a positive prompt.")
        else:
            self.positive_prompt = positive_prompt

        default_negative = "worst quality, low quality, blurry, bad anatomy, bad hands, extra digits, fewer digits, cropped, watermark, signature, text, deformed, monochrome, greyscale, "
        self.negative_prompt = f'{default_negative}{negative_prompt}'

        # 生成的图片保存在项目根目录下的 output 文件夹
        self.output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

        if output_name:
            self.output_name = os.path.join(self.output_path, f'{output_name}.png')
        else:
            self.output_name = os.path.join(self.output_path, f'{str(uuid.uuid4())}.png')

        self.server = f"http://{self.config['server']}"
        self.ws = f"ws://{self.config['server']}"

        self.client_id = str(uuid.uuid4())
        self.prompt_id = None

    def generate_workflow_dict(self) -> dict:
        return {
            "1": {
                "inputs": {"ckpt_name": self.config["model"]},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"},
            },
            "2": {
                "inputs": {"text": self.positive_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"},
            },
            "3": {
                "inputs": {"text": self.negative_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative)"},
            },
            "4": {
                "inputs": {"width": self.config['image_width'], "height": self.config['image_height'], "batch_size": 1},
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"},
            },
            "5": {
                "inputs": {
                    "seed": random.randint(0, 18446744073709551615),
                    "steps": self.config['steps'],
                    "cfg": self.config['cfg'],
                    "sampler_name": self.config['sampler'],
                    "scheduler": self.config['scheduler'],
                    "denoise": self.config['denoise_strength'],
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"},
            },
            "6": {
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"},
            },
            "7": {
                "inputs": {"images": ["6", 0]},
                "class_type": "PreviewImage",
                "_meta": {"title": "Preview Image"},
            },
        }

    def queue_prompt(self):
        payload = {"prompt": self.generate_workflow_dict(), "client_id": self.client_id}
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            f"{self.server}/prompt",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        response = json.loads(urllib.request.urlopen(req, timeout=30).read())
        self.prompt_id = response["prompt_id"]

    def get_history(self) -> dict:
        req = urllib.request.Request(f"{self.server}/history/{self.prompt_id}")
        res = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return res


    def download_image(self, filename: str, subfolder: str = "", folder_type: str = "output"):
        params = urllib.parse.urlencode(
            {
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type,
            }
        )
        url = f"{self.server}/view?{params}"

        with urllib.request.urlopen(url, timeout=30) as resp:
            return Image.open(io.BytesIO(resp.read()))


    def _receive_images_via_ws(self, ws: websocket.WebSocket) -> dict:
        """
        监听 WebSocket 消息，收集预览节点(7)输出的二进制图片。
        返回格式：{"7": [bytes, ...]}
        """
        output_images = {}
        executing_node = None
        binary_count = 0

        while True:
            try:
                out = ws.recv()
            except:
                break

            if isinstance(out, str):
                try:
                    message = json.loads(out)
                except json.JSONDecodeError:
                    continue

                msg_type = message.get("type")
                data = message.get("data", {})

                if msg_type == "executing" and data.get("prompt_id") == self.prompt_id:
                    node = data.get("node")
                    if node is None:
                        break
                    executing_node = node
                continue

            # 二进制图片数据：只有当前执行到预览节点(7)时才收集
            if executing_node == "7":
                img_data = out[8:] if len(out) > 8 else out
                output_images.setdefault("7", []).append(img_data)
                binary_count += 1

        return output_images

    def _save_images_from_history(self):
        history = self.get_history()
        outputs = history.get(self.prompt_id, {}).get("outputs", {})
        saved_index = 0

        for _, node_output in outputs.items():
            images = node_output.get("images", [])
            for img_info in images:
                img = self.download_image(
                    filename=img_info["filename"],
                    subfolder=img_info.get("subfolder", ""),
                    folder_type=img_info.get("type", "output"),
                )
                if not img:
                    continue

                img.save(self.output_name)
                saved_index += 1


    def gen_image(self):
        ws = websocket.WebSocket()
        ws.connect(f"{self.ws}/ws?clientId={self.client_id}")
        self.queue_prompt()
        self._receive_images_via_ws(ws)
        ws.close()
        os.makedirs(self.output_path, exist_ok=True)
        self._save_images_from_history()
        return self.output_name


def start(positive_prompt: str, negative_prompt: str = '', output_name: str = '') -> str:
    client = ComfyUIClient(positive_prompt, negative_prompt, output_name)
    saved_files = client.gen_image()
    return saved_files


if __name__ == "__main__":
    positive_prompt = "masterpiece, best quality, 1girl, solo, looking at viewer, smile"

    out_file = start(positive_prompt=positive_prompt)

    print(out_file)
