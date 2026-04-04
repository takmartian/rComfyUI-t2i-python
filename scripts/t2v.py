import json
import logging
import os
import random
import urllib.parse
import uuid
import cv2
import requests
import websocket

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
    def __init__(self, positive_prompt: str, output_name: str = None):
        self.log = _get_logger()
        self.host = os.getenv("COMFYUI_SERVER_ADDRESS", "localhost:8188")

        if not positive_prompt:
            raise ValueError("positive_prompt is empty. Please provide a positive prompt.")
        else:
            self.positive_prompt = positive_prompt

        # 生成的图片保存在项目根目录下的 output 文件夹
        self.output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

        if output_name:
            self.output_name = os.path.join(self.output_path, f'{output_name}.mp4')
        else:
            self.output_name = os.path.join(self.output_path, f'{str(uuid.uuid4())}.mp4')

        if self.host.startswith("192"):
            self.server = f"http://{self.host}"
            self.ws = f"ws://{self.host}"
        else:
            self.server = f"https://{self.host}"
            self.ws = f"wss://{self.host}"

        self.client_id = str(uuid.uuid4())
        self.prompt_id = None

        self.log.info("Positive prompt | %s", self.positive_prompt)

    def generate_t2v_dict(self) -> dict:
        wf_dict = {
            "1": {
                "inputs": {
                    "video_latent": [
                        "48",
                        0
                    ],
                    "audio_latent": [
                        "33",
                        0
                    ]
                },
                "class_type": "LTXVConcatAVLatent",
                "_meta": {
                    "title": "LTXVConcatAVLatent"
                }
            },
            "2": {
                "inputs": {
                    "sampler_name": "euler_cfg_pp"
                },
                "class_type": "KSamplerSelect",
                "_meta": {
                    "title": "K采样器选择"
                }
            },
            "3": {
                "inputs": {
                    "cfg": 1,
                    "model": [
                        "19",
                        0
                    ],
                    "positive": [
                        "17",
                        0
                    ],
                    "negative": [
                        "17",
                        1
                    ]
                },
                "class_type": "CFGGuider",
                "_meta": {
                    "title": "CFG引导器"
                }
            },
            "5": {
                "inputs": {
                    "cfg": 1,
                    "model": [
                        "19",
                        0
                    ],
                    "positive": [
                        "17",
                        0
                    ],
                    "negative": [
                        "17",
                        1
                    ]
                },
                "class_type": "CFGGuider",
                "_meta": {
                    "title": "CFG引导器"
                }
            },
            "6": {
                "inputs": {
                    "sampler_name": "euler_ancestral_cfg_pp"
                },
                "class_type": "KSamplerSelect",
                "_meta": {
                    "title": "K采样器选择"
                }
            },
            "7": {
                "inputs": {
                    "noise": [
                        "30",
                        0
                    ],
                    "guider": [
                        "5",
                        0
                    ],
                    "sampler": [
                        "6",
                        0
                    ],
                    "sigmas": [
                        "34",
                        0
                    ],
                    "latent_image": [
                        "1",
                        0
                    ]
                },
                "class_type": "SamplerCustomAdvanced",
                "_meta": {
                    "title": "自定义采样器（高级）"
                }
            },
            "8": {
                "inputs": {
                    "sigmas": "0.85, 0.7250, 0.4219, 0.0"
                },
                "class_type": "ManualSigmas",
                "_meta": {
                    "title": "自定义Sigmas"
                }
            },
            "9": {
                "inputs": {
                    "video_latent": [
                        "50",
                        0
                    ],
                    "audio_latent": [
                        "10",
                        1
                    ]
                },
                "class_type": "LTXVConcatAVLatent",
                "_meta": {
                    "title": "LTXVConcatAVLatent"
                }
            },
            "10": {
                "inputs": {
                    "av_latent": [
                        "7",
                        0
                    ]
                },
                "class_type": "LTXVSeparateAVLatent",
                "_meta": {
                    "title": "LTXV分离音视频潜空间"
                }
            },
            "11": {
                "inputs": {
                    "model_name": "ltx-2.3-spatial-upscaler-x2-1.0.safetensors"
                },
                "class_type": "LatentUpscaleModelLoader",
                "_meta": {
                    "title": "加载Latent放大模型"
                }
            },
            "12": {
                "inputs": {
                    "noise": [
                        "29",
                        0
                    ],
                    "guider": [
                        "3",
                        0
                    ],
                    "sampler": [
                        "2",
                        0
                    ],
                    "sigmas": [
                        "8",
                        0
                    ],
                    "latent_image": [
                        "9",
                        0
                    ]
                },
                "class_type": "SamplerCustomAdvanced",
                "_meta": {
                    "title": "自定义采样器（高级）"
                }
            },
            "13": {
                "inputs": {
                    "av_latent": [
                        "12",
                        0
                    ]
                },
                "class_type": "LTXVSeparateAVLatent",
                "_meta": {
                    "title": "LTXV分离音视频潜空间"
                }
            },
            "14": {
                "inputs": {
                    "tile_size": 512,
                    "overlap": 64,
                    "temporal_size": 512,
                    "temporal_overlap": 4,
                    "samples": [
                        "13",
                        0
                    ],
                    "vae": [
                        "26",
                        2
                    ]
                },
                "class_type": "VAEDecodeTiled",
                "_meta": {
                    "title": "VAE解码（分块）"
                }
            },
            "15": {
                "inputs": {
                    "samples": [
                        "13",
                        1
                    ],
                    "audio_vae": [
                        "25",
                        0
                    ]
                },
                "class_type": "LTXVAudioVAEDecode",
                "_meta": {
                    "title": "LTXV音频VAE解码"
                }
            },
            "16": {
                "inputs": {
                    "text": [
                        "46",
                        0
                    ],
                    "clip": [
                        "28",
                        0
                    ]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Positive Prompt)"
                }
            },
            "17": {
                "inputs": {
                    "frame_rate": [
                        "22",
                        0
                    ],
                    "positive": [
                        "16",
                        0
                    ],
                    "negative": [
                        "18",
                        0
                    ]
                },
                "class_type": "LTXVConditioning",
                "_meta": {
                    "title": "LTXV条件"
                }
            },
            "18": {
                "inputs": {
                    "text": "pc game, console game, video game, cartoon, childish, ugly,subtitles, caption, captions, closed captions, CC, on-screen text, text overlay, words, letters, characters, readable text, typography, subtitles bar, karaoke lyrics, lyric video, lower third, title card, UI, HUD, watermark, logo, signature, timestamp, sticker, banner, scrolling text, low quality, lowres, blurry, flicker, jitter, shaky camera, ghosting, frame doubling, temporal inconsistency, face warp, face melt, asymmetrical eyes, bad teeth, extra teeth, tongue artifact, mouth deformation, lip-sync mismatch, over-smoothing, plastic skin, heavy beauty filter, harsh sharpening, banding, noise, extra fingers, extra hands，字幕",
                    "clip": [
                        "28",
                        0
                    ]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Negative Prompt)"
                }
            },
            "19": {
                "inputs": {
                    "chunks": 4,
                    "dim_threshold": 4096,
                    "model": [
                        "21",
                        0
                    ]
                },
                "class_type": "LTXVChunkFeedForward",
                "_meta": {
                    "title": "LTXV Chunk FeedForward (optional)"
                }
            },
            "20": {
                "inputs": {
                    "sage_attention": "auto",
                    "allow_compile": False,
                    "model": [
                        "31",
                        0
                    ]
                },
                "class_type": "PathchSageAttentionKJ",
                "_meta": {
                    "title": "Patch Sage Attention KJ"
                }
            },
            "21": {
                "inputs": {
                    "enable_fp16_accumulation": True,
                    "model": [
                        "20",
                        0
                    ]
                },
                "class_type": "ModelPatchTorchSettings",
                "_meta": {
                    "title": "Model Patch Torch Settings"
                }
            },
            "22": {
                "inputs": {
                    "value": 24
                },
                "class_type": "PrimitiveFloat",
                "_meta": {
                    "title": "fps"
                }
            },
            "23": {
                "inputs": {
                    "frame_rate": 24,
                    "loop_count": 0,
                    "filename_prefix": "LTX2/ltx2-i2v",
                    "format": "video/h264-mp4",
                    "pix_fmt": "yuv420p",
                    "crf": 19,
                    "save_metadata": False,
                    "trim_to_audio": False,
                    "pingpong": False,
                    "save_output": True,
                    "images": [
                        "14",
                        0
                    ],
                    "audio": [
                        "15",
                        0
                    ]
                },
                "class_type": "VHS_VideoCombine",
                "_meta": {
                    "title": "Video Combine 🎥🅥🅗🅢"
                }
            },
            "24": {
                "inputs": {
                    "samples": [
                        "10",
                        0
                    ],
                    "upscale_model": [
                        "11",
                        0
                    ],
                    "vae": [
                        "26",
                        2
                    ]
                },
                "class_type": "LTXVLatentUpsampler",
                "_meta": {
                    "title": "LTXV潜空间上采样器"
                }
            },
            "25": {
                "inputs": {
                    "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"
                },
                "class_type": "LTXVAudioVAELoader",
                "_meta": {
                    "title": "LTXV音频VAE加载器"
                }
            },
            "26": {
                "inputs": {
                    "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Checkpoint加载器（简易）"
                }
            },
            "27": {
                "inputs": {
                    "lora_name": "ltx-2.3-22b-distilled-lora-384.safetensors",
                    "strength_model": 0.5,
                    "model": [
                        "26",
                        0
                    ]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {
                    "title": "LoRA加载器（仅模型）"
                }
            },
            "28": {
                "inputs": {
                    "text_encoder": "gemma_3_12B_it_fpmixed.safetensors",
                    "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors",
                    "device": "default"
                },
                "class_type": "LTXAVTextEncoderLoader",
                "_meta": {
                    "title": "LTXV音频文本编码器加载器"
                }
            },
            "29": {
                "inputs": {
                    "noise_seed": random.randint(0, 1125899906842624),
                },
                "class_type": "RandomNoise",
                "_meta": {
                    "title": "随机噪波"
                }
            },
            "30": {
                "inputs": {
                    "noise_seed": random.randint(0, 1125899906842624),
                },
                "class_type": "RandomNoise",
                "_meta": {
                    "title": "随机噪波"
                }
            },
            "31": {
                "inputs": {
                    "reserved": 4,
                    "mode": "manual",
                    "seed": random.randint(0, 1125899906842624),
                    "auto_max_reserved": 0,
                    "clean_gpu_before": True,
                    "anything": [
                        "27",
                        0
                    ]
                },
                "class_type": "ReservedVRAMSetter",
                "_meta": {
                    "title": "Set Reserved VRAM(GB) ⚙️"
                }
            },
            "33": {
                "inputs": {
                    "frames_number": [
                        "41",
                        0
                    ],
                    "frame_rate": [
                        "40",
                        0
                    ],
                    "batch_size": 1,
                    "audio_vae": [
                        "25",
                        0
                    ]
                },
                "class_type": "LTXVEmptyLatentAudio",
                "_meta": {
                    "title": "LTXV 空音频潜空间"
                }
            },
            "34": {
                "inputs": {
                    "sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
                },
                "class_type": "ManualSigmas",
                "_meta": {
                    "title": "自定义Sigmas"
                }
            },
            "36": {
                "inputs": {
                    "width": [
                        "39",
                        0
                    ],
                    "height": [
                        "37",
                        0
                    ],
                    "length": [
                        "41",
                        0
                    ],
                    "batch_size": 1
                },
                "class_type": "EmptyLTXVLatentVideo",
                "_meta": {
                    "title": "空Latent视频（LTXV）"
                }
            },
            "37": {
                "inputs": {
                    "value": "a/2",
                    "a": [
                        "44",
                        0
                    ]
                },
                "class_type": "easy simpleMath",
                "_meta": {
                    "title": "easy simpleMath"
                }
            },
            "38": {
                "inputs": {
                    "value": 1280
                },
                "class_type": "INTConstant",
                "_meta": {
                    "title": "INT Constant"
                }
            },
            "39": {
                "inputs": {
                    "value": "a/2",
                    "a": [
                        "38",
                        0
                    ]
                },
                "class_type": "easy simpleMath",
                "_meta": {
                    "title": "easy simpleMath"
                }
            },
            "40": {
                "inputs": {
                    "a": [
                        "22",
                        0
                    ]
                },
                "class_type": "CM_FloatToInt",
                "_meta": {
                    "title": "FloatToInt"
                }
            },
            "41": {
                "inputs": {
                    "value": [
                        "42",
                        0
                    ]
                },
                "class_type": "PrimitiveInt",
                "_meta": {
                    "title": "number of frames"
                }
            },
            "42": {
                "inputs": {
                    "value": 193
                },
                "class_type": "INTConstant",
                "_meta": {
                    "title": "INT Constant"
                }
            },
            "44": {
                "inputs": {
                    "value": 720
                },
                "class_type": "INTConstant",
                "_meta": {
                    "title": "INT Constant"
                }
            },
            "46": {
                "inputs": {
                    "text": self.positive_prompt
                },
                "class_type": "CR Text",
                "_meta": {
                    "title": "🔤 CR Text"
                }
            },
            "48": {
                "inputs": {
                    "strength": 0.7,
                    "bypass": True,
                    "vae": [
                        "26",
                        2
                    ],
                    "image": [
                        "52",
                        0
                    ],
                    "latent": [
                        "36",
                        0
                    ]
                },
                "class_type": "LTXVImgToVideoConditionOnly",
                "_meta": {
                    "title": "🅛🅣🅧 LTXV Img To Video Condition Only"
                }
            },
            "50": {
                "inputs": {
                    "strength": 1,
                    "bypass": True,
                    "vae": [
                        "26",
                        2
                    ],
                    "image": [
                        "52",
                        0
                    ],
                    "latent": [
                        "24",
                        0
                    ]
                },
                "class_type": "LTXVImgToVideoConditionOnly",
                "_meta": {
                    "title": "🅛🅣🅧 LTXV Img To Video Condition Only"
                }
            },
            "52": {
                "inputs": {
                    "image": "1.jpg"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            }
        }
        return wf_dict

    def queue_prompt(self):
        workflow = self.generate_t2v_dict()
        payload = {"prompt": workflow, "client_id": self.client_id}
        response = requests.post(f"{self.server}/prompt", json=payload, timeout=30).json()
        print(response)
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
        return requests.get(f"{self.server}/history/{self.prompt_id}").json()[self.prompt_id]['outputs']['23']['gifs'][0]

    def get_video(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        params = urllib.parse.urlencode(
            {"filename": filename, "subfolder": subfolder, "type": folder_type}
        )
        res = requests.get(f"{self.server}/view?{params}", timeout=60)
        res.raise_for_status()
        return res.content

    def extract_first_frame(self, video_path: str) -> str:
        png_path = os.path.splitext(video_path)[0] + ".png"

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")

        ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            raise RuntimeError(f"Failed to read first frame from video: {video_path}")

        # OpenCV 直接写 png，若同名已存在会覆盖
        success = cv2.imwrite(png_path, frame)
        if not success:
            raise RuntimeError(f"Failed to write PNG file: {png_path}")

        self.log.info("first frame saved | path=%s", png_path)
        return png_path

    def gen_video(self):
        ws = websocket.WebSocket()
        ws.connect(f"{self.ws}/ws?clientId={self.client_id}", timeout=10)
        ws.sock.settimeout(300)
        self.queue_prompt()
        self._wait_for_completion(ws)
        ws.close()

        video_info = self.get_history()  # 你这里返回的是 outputs['23']['gifs'][0]
        video_bytes = self.get_video(
            video_info["filename"],
            video_info["subfolder"],
            video_info["type"]
        )

        os.makedirs(self.output_path, exist_ok=True)
        with open(self.output_name, "wb") as f:
            f.write(video_bytes)

        self.log.info("video saved | path=%s", self.output_name)

        first_frame_png = self.extract_first_frame(self.output_name)
        self.log.info("first frame extracted | path=%s", first_frame_png)

        return self.output_name

def start(positive_prompt: str, output_name: str = '') -> str:
    client = ComfyUIClient(positive_prompt, output_name)
    saved_files = client.gen_video()
    return saved_files


if __name__ == "__main__":
    positive_prompt = """
    一个时髦的女人走在东京的街道上，到处都是温暖的霓虹灯和生动的城市标志。她穿着黑色皮夹克、红色长裙、黑色靴子，拿着一个黑色钱包。她戴着太阳镜，涂着红色的口红。她走起路来自信而随意。街道是潮湿和反光的，创造了一个彩色灯光的镜子效果。许多行人走来走去。
    """

    out_file = start(positive_prompt=positive_prompt)

    print(out_file)
