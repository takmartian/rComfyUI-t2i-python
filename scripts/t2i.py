import io
import json
import logging
import os
import random
import urllib.parse
import uuid

import requests
import websocket
from PIL import Image

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




class ComfyUIClient:
    def __init__(self, positive_prompt: str, output_name: str = None, selfee: bool = False):
        self.log = _get_logger()
        self.host = os.getenv("COMFYUI_SERVER_ADDRESS", "localhost:8188")
        self.selfee = selfee

        if not positive_prompt:
            raise ValueError("positive_prompt is empty. Please provide a positive prompt.")
        else:
            self.positive_prompt = positive_prompt

        # 生成的图片保存在项目根目录下的 output 文件夹
        self.output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

        if output_name:
            self.output_name = os.path.join(self.output_path, f'{output_name}.png')
        else:
            self.output_name = os.path.join(self.output_path, f'{str(uuid.uuid4())}.png')

        if self.host.startswith("192"):
            self.server = f"http://{self.host}"
            self.ws = f"ws://{self.host}"
        else:
            self.server = f"https://{self.host}"
            self.ws = f"wss://{self.host}"

        self.client_id = str(uuid.uuid4())
        self.prompt_id = None

        self.log.info("Positive prompt | %s", self.positive_prompt)

    def generate_workflow_dict(self) -> dict:
        return {
            "11": {
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {
                    "title": "加载VAE"
                }
            },
            "12": {
                "inputs": {
                    "clip_name": "qwen_3_4b.safetensors",
                    "type": "lumina2",
                    "device": "default"
                },
                "class_type": "CLIPLoader",
                "_meta": {
                    "title": "加载CLIP"
                }
            },
            "14": {
                "inputs": {
                    "lora_name": "Z-Image-Fun-Lora-Distill-8-Steps-2603-ComfyUI.safetensors",
                    "strength_model": 0.45000000000000007,
                    "model": [
                        "23",
                        0
                    ]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {
                    "title": "LoRA加载器（仅模型）"
                }
            },
            "16": {
                "inputs": {
                    "text": "泛黄，发绿，模糊，低分辨率，低质量图像，扭曲的肢体，诡异的外观，丑陋，AI感，噪点，网格感，JPEG压缩条纹，异常的肢体，水印，乱码，意义不明的字符，泛蓝",
                    "clip": [
                        "12",
                        0
                    ]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP文本编码"
                }
            },
            "17": {
                "inputs": {
                    "samples": [
                        "22",
                        0
                    ],
                    "vae": [
                        "11",
                        0
                    ]
                },
                "class_type": "VAEDecode",
                "_meta": {
                    "title": "VAE解码"
                }
            },
            "18": {
                "inputs": {
                    "unet_name": "z_image_bf16.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {
                    "title": "UNet加载器"
                }
            },
            "21": {
                "inputs": {
                    "width": 1280,
                    "height": 720,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {
                    "title": "空Latent图像"
                }
            },
            "22": {
                "inputs": {
                    "seed": random.randint(0, 9223372036854775807),
                    "steps": 8,
                    "cfg": 1,
                    "sampler_name": "res_2s",
                    "scheduler": "bong_tangent",
                    "denoise": 1,
                    "model": [
                        "14",
                        0
                    ],
                    "positive": [
                        "24",
                        0
                    ],
                    "negative": [
                        "16",
                        0
                    ],
                    "latent_image": [
                        "21",
                        0
                    ]
                },
                "class_type": "KSampler",
                "_meta": {
                    "title": "K采样器"
                }
            },
            "23": {
                "inputs": {
                    "lora_name": "Kook_Zimage_瑶光.safetensors",
                    "strength_model": 1.0000000000000002,
                    "model": [
                        "18",
                        0
                    ]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {
                    "title": "LoRA加载器（仅模型）"
                }
            },
            "24": {
                "inputs": {
                    "text": [
                        "33",
                        0
                    ],
                    "clip": [
                        "12",
                        0
                    ]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP文本编码"
                }
            },
            "27": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": [
                        "29",
                        0
                    ]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "保存图像"
                }
            },
            "28": {
                "inputs": {
                    "grain_intensity": 0.015000000000000003,
                    "saturation_mix": 0.45000000000000007,
                    "batch_size": 4,
                    "images": [
                        "17",
                        0
                    ]
                },
                "class_type": "FastFilmGrain",
                "_meta": {
                    "title": "🎞️ Fast Film Grain"
                }
            },
            "29": {
                "inputs": {
                    "brightness": 0.9000000000000001,
                    "contrast": 1.2000000000000002,
                    "saturation": 0.8000000000000002,
                    "image": [
                        "28",
                        0
                    ]
                },
                "class_type": "LayerColor: BrightnessContrastV2",
                "_meta": {
                    "title": "图层颜色：亮度对比度 V2"
                }
            },
            "32": {
                "inputs": {
                    "unet_name": "moodyPornMix_v10DPO.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {
                    "title": "UNet加载器"
                }
            },
            "33": {
                "inputs": {
                    "text": f"超高清写实摄影，杰作，最佳质量，8K UHD，raw photo，无滤镜直出，超高细节，锐利焦点，CCD 感，{self.positive_prompt}"
                },
                "class_type": "CR Text",
                "_meta": {
                    "title": "🔤 CR Text"
                }
            }
        }

    def selfee_workflow_dict(self) -> dict:
        return {
            "3": {
                "inputs": {
                    "seed": random.randint(0, 9223372036854775807),
                    "steps": 38,
                    "cfg": 5.0,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"},
            },
            "4": {
                "inputs": {"ckpt_name": "flarediffusionNSFW_v18ENDOFLIFE.safetensors"},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"},
            },
            "5": {
                "inputs": {"width": 960, "height": 1024, "batch_size": 1},
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"},
            },
            "6": {
                "inputs": {"text": f"masterpiece, best quality, ultra-detailed, illustration,(1girl), full body, beautiful detailed eyes, pink hair, cat ears, kid, thighhighs, cute pink dress, black boots, {self.positive_prompt}", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"},
            },
            "7": {
                "inputs": {
                    "text": "sketches, (worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome:1.5)), ((grayscale)), skin spots, acnes, skin blemishes, manboobs, backlight,(ugly:1.331), (duplicate:1.331), (morbid:1.21), (mutilated:1.21), (tranny:1.331), mutated hands, (poorly drawn hands:1.331), blurry, (bad anatomy:1.21), (bad proportions:1.331), extra limbs, (disfigured:1.331), (missing arms:1.331), (extra legs:1.331), (fused fingers:1.61051), (too many fingers:1.61051), (unclear eyes:1.331), lowers, bad hands, missing fingers, extra digit, (futa:1.1), logo, white letters,missing fingers, extra digit, fewer digits,(mutated hands and fingers:1.5 ), (long body :1.3),bad hands, fused hand, missing hand, disappearing arms, error, missing fingers, missing limb, fused fingers, fused fingers",
                    "clip": ["4", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"},
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"},
            },
            "10": {
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"},
            },
        }

    def queue_prompt(self):
        workflow = self.selfee_workflow_dict() if self.selfee else self.generate_workflow_dict()
        payload = {"prompt": workflow, "client_id": self.client_id}
        response = requests.post(f"{self.server}/prompt", json=payload, timeout=30).json()
        self.prompt_id = response["prompt_id"]
        self.log.info("Prompt queued | prompt_id=%s client_id=%s", self.prompt_id, self.client_id)

    def _wait_for_completion(self, ws: websocket.WebSocket):
        while True:
            try:
                out = ws.recv()
            except Exception:
                break
            if not isinstance(out, str):
                continue
            message = json.loads(out)
            msg_type = message.get("type")
            data = message.get("data", {})
            print(f"Received message | type={msg_type} data={data}")
            if msg_type == "execution_error" and data.get("prompt_id") == self.prompt_id:
                raise RuntimeError(
                    f"ComfyUI execution error on node {data.get('node_id')} "
                    f"({data.get('node_type')}): {data.get('exception_message', '').strip()}"
                )
            if msg_type == "executing" and data.get("prompt_id") == self.prompt_id:
                if data.get("node") is None:
                    break

    def get_history(self) -> dict:
        return requests.get(f"{self.server}/history/{self.prompt_id}").json()[self.prompt_id]

    def get_image(self, filename, subfolder, folder_type) -> Image.Image:
        params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
        res = requests.get(f"{self.server}/view?{params}")
        return Image.open(io.BytesIO(res.content))

    def gen_image(self):
        ws = websocket.WebSocket()
        ws.connect(f"{self.ws}/ws?clientId={self.client_id}", timeout=10)
        ws.sock.settimeout(300)
        self.queue_prompt()
        self._wait_for_completion(ws)
        ws.close()

        history = self.get_history()
        for node_output in history["outputs"].values():
            if "images" in node_output:
                image_info = node_output["images"][0]
                img = self.get_image(image_info["filename"], image_info["subfolder"], image_info["type"])
                os.makedirs(self.output_path, exist_ok=True)
                img.save(self.output_name)
                self.log.info("Image saved | path=%s", self.output_name)
                return self.output_name

        raise RuntimeError("No images found in ComfyUI history")


def start(positive_prompt: str, output_name: str = '', selfee: bool = False) -> str:
    client = ComfyUIClient(positive_prompt, output_name, selfee)
    saved_files = client.gen_image()
    return saved_files


if __name__ == "__main__":
    positive_prompt = ""

    out_file = start(positive_prompt=positive_prompt)

    print(out_file)
