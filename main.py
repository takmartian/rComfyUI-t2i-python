import random
import json
import uuid
import websocket
import urllib.request
import urllib.error
import urllib.parse
import io
import os
from PIL import Image
import logging
import sys
import argparse


class ComfyUIClient:
    def __init__(self, server_address: str, model: str, https: bool = False, **kwargs):
        self._setup_logger(kwargs.get('log_level', logging.INFO))

        if https:
            self.server_address = f"https://{server_address}"
            self.ws_address = f"wss://{server_address}"
        else:
            self.server_address = f"http://{server_address}"
            self.ws_address = f"ws://{server_address}"
        self.model = model

        self.client_id = str(uuid.uuid4())
        self.prompt_id = None

        self.logger.info(f"ComfyUIClient init | server={self.server_address} | model={self.model}")

    def _setup_logger(self, level):
        """Configure instance logger with console + file handlers."""
        self.logger = logging.getLogger(f"{__name__}.{id(self)}")
        self.logger.setLevel(level)
        if not self.logger.handlers:
            fmt = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%H:%M:%S'
            )

            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(level)
            stream_handler.setFormatter(fmt)
            self.logger.addHandler(stream_handler)

            log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rcomfyui.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(fmt)
            self.logger.addHandler(file_handler)

    # ── 公开方法 ─────────────────────────────────────────────────

    def generate_workflow_dict(self, positive_prompt: str, negative_prompt: str, image_width: int, image_height: int, seed: int, steps: int,
                               cfg: float, sampler: str, scheduler: str, denoise_strength: float) -> dict:

        workflow_dict = {
            "1": {
                "inputs": {"ckpt_name": self.model},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "2": {
                "inputs": {"text": positive_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "3": {
                "inputs": {"text": negative_prompt, "clip": ["1", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "4": {
                "inputs": {"width": image_width, "height": image_height, "batch_size": 1},
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "5": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": denoise_strength,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "6": {
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "7": {
                "inputs": {"images": ["6", 0]},
                "class_type": "PreviewImage",
                "_meta": {"title": "Preview Image"}
            }
        }

        return workflow_dict

    def queue_prompt(self, workflow_dict: dict):

        self.logger.info("提交提示词到服务器...")
        p = {"prompt": workflow_dict, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(
            f"{self.server_address}/prompt",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            response = json.loads(urllib.request.urlopen(req, timeout=30).read())
            self.prompt_id = response['prompt_id']
            self.logger.info(f"提示词已提交 | prompt_id={self.prompt_id}")
            return response
        except urllib.error.HTTPError as e:
            self.logger.error(f"提交提示词失败 HTTP {e.code}: {e.reason}")
            raise
        except Exception as e:
            self.logger.error(f"提交提示词失败: {e}")
            raise

    def get_history(self):
        self.logger.debug(f"获取 history | prompt_id={self.prompt_id}")
        req = urllib.request.Request(
            f"{self.server_address}/history/{self.prompt_id}"
        )
        try:
            return json.loads(urllib.request.urlopen(req, timeout=15).read())
        except Exception as e:
            self.logger.error(f"获取 history 失败: {e}")
            raise

    def download_image(self, filename, node_id, subfolder="", folder_type="output"):
        params = urllib.parse.urlencode({
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        })
        url = f"{self.server_address}/view?{params}"
        self.logger.debug(f"下载图片 | url={url}")
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return Image.open(io.BytesIO(resp.read()))
        except Exception as e:
            self.logger.warning(f"下载图片失败 [{filename}]: {e}")
            return None

    def start(self, positive_prompt: str, **kwargs):
        negative_prompt = kwargs.get('negative_prompt',
                                     'worst quality, low quality, blurry, bad anatomy, bad hands, extra digits, '
                                     'fewer digits, cropped, watermark, signature, text, deformed, monochrome, greyscale')
        image_width = kwargs.get('image_width')
        image_height = kwargs.get('image_height')
        seed = kwargs.get('seed', random.randint(0, 18446744073709551615))
        steps = kwargs.get('steps', 28)
        cfg = kwargs.get('cfg', 8.0)
        sampler = kwargs.get('sampler', 'euler')
        scheduler = kwargs.get('scheduler', 'sgm_uniform')
        denoise_strength = kwargs.get('denoise_strength', 1.0)
        output_path = kwargs.get('output_dir')
        output_name = kwargs.get('output_name')
        if not output_path:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "text2image")

        workflow_dict = self.generate_workflow_dict(positive_prompt,
                                                    negative_prompt=negative_prompt,
                                                    image_width=image_width,
                                                    image_height=image_height,
                                                    seed=seed,
                                                    steps=steps,
                                                    cfg=cfg,
                                                    sampler=sampler,
                                                    scheduler=scheduler,
                                                    denoise_strength=denoise_strength
                                                    )

        output_images = {}
        self.logger.info(f"Output directory: {os.path.abspath(output_path)}")
        self.logger.info("Connecting WebSocket...")
        ws = websocket.WebSocket()
        try:
            ws.connect(f"{self.ws_address}/ws?clientId={self.client_id}")
            self.logger.info("WebSocket 已连接")
        except Exception as e:
            self.logger.error(f"WebSocket 连接失败: {e}")
            raise

        try:
            self.queue_prompt(workflow_dict)
        except Exception:
            ws.close()
            raise

        executing_node = None
        binary_count = 0

        while True:
            try:
                out = ws.recv()
            except websocket.WebSocketTimeout:
                self.logger.warning("WebSocket 接收超时")
                continue
            except Exception as e:
                self.logger.error(f"WebSocket 接收错误: {e}")
                break

            if isinstance(out, str):
                try:
                    message = json.loads(out)
                except json.JSONDecodeError:
                    self.logger.warning(f"收到无效 JSON: {out[:100]}")
                    continue

                msg_type = message.get('type')
                data = message.get('data', {})

                if msg_type == 'executing':
                    if data.get('prompt_id') == self.prompt_id:
                        node = data.get('node')
                        if node is None:
                            self.logger.info("✅ 生成任务执行完毕")
                            break
                        executing_node = node
                        self.logger.debug(f"执行节点: {node}")

                elif msg_type == 'executed':
                    node_id = data.get('node')
                    self.logger.debug(f"节点 {node_id} 执行完成")

                elif msg_type == 'error':
                    self.logger.error(f"服务器错误: {data.get('message', data)}")

                elif msg_type == 'bubble':
                    bubble_data = data.get('data', {})
                    if bubble_data.get('error'):
                        self.logger.error(f"节点执行异常: {bubble_data['error']}")

            else:
                # 二进制图片数据
                if executing_node == '7':
                    try:
                        img_data = out[8:] if len(out) > 8 else out
                        output_images.setdefault('7', []).append(img_data)
                        binary_count += 1
                        self.logger.debug(f"收到二进制图片数据 #{binary_count} | 大小={len(img_data)} bytes")
                    except Exception as e:
                        self.logger.error(f"处理二进制数据出错: {e}")

        ws.close()
        self.logger.info("WebSocket 连接已关闭")

        # ── 保存图片 ────────────────────────────────────────────
        os.makedirs(output_path, exist_ok=True)
        saved_files = []

        if '7' in output_images:
            for idx, img_data in enumerate(output_images['7']):
                try:
                    image = Image.open(io.BytesIO(img_data))
                    if output_name:
                        filename = f"{output_name}.png" if len(output_images['7']) == 1 else f"{output_name}_{idx}.png"
                    else:
                        filename = f"gen_{seed}_{idx}.png"
                    out_file = os.path.join(output_path, filename)
                    image.save(out_file)
                    saved_files.append(out_file)
                    self.logger.info(f"✅ 图片已保存 [{idx + 1}/{len(output_images['7'])}]: {out_file}")
                except Exception as e:
                    self.logger.error(f"保存图片失败 [{idx}]: {e}")

        else:
            self.logger.warning("WebSocket 未收到图片数据，尝试通过 History API 获取...")
            try:
                history = self.get_history()
                outputs = history.get(self.prompt_id, {}).get('outputs', {})
                saved = 0
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for img_info in node_output['images']:
                            img = self.download_image(
                                img_info['filename'], node_id,
                                subfolder=img_info.get('subfolder', ''),
                                folder_type=img_info.get('type', 'output')
                            )
                            if img:
                                if output_name:
                                    # Use deterministic naming for history fallback as well.
                                    filename = f"{output_name}.png" if len(node_output.get('images', [])) == 1 else f"{output_name}_{saved}.png"
                                else:
                                    filename = img_info['filename']
                                out_file = os.path.join(output_path, filename)
                                img.save(out_file)
                                saved += 1
                                saved_files.append(out_file)
                                self.logger.info(f"✅ 图片已保存: {out_file}")
                if saved == 0:
                    self.logger.warning("History API 中未找到任何图片")
            except Exception as e:
                self.logger.error(f"History API 获取失败: {e}")

        return saved_files


def _main_logger(level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    if not logger.handlers:
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(fmt)
        logger.addHandler(h)

        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rcomfyui.log")
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def parse_args():
    parser = argparse.ArgumentParser(description="ComfyUI text2image client")
    parser.add_argument("--model", required=True, help="Checkpoint model name in ComfyUI")
    parser.add_argument("--positive-prompt", required=True, help="Positive prompt text")
    parser.add_argument("--negative-prompt", default=None, help="Optional negative prompt override")
    parser.add_argument("--image-width", type=int, default=1024, help="Image width")
    parser.add_argument("--image-height", type=int, default=1024, help="Image height")
    parser.add_argument("--seed", type=int, default=None, help="Random seed; omit to use random")
    parser.add_argument("--steps", type=int, default=28, help="Sampling steps")
    parser.add_argument("--cfg", type=float, default=8.0, help="CFG scale")
    parser.add_argument("--sampler", default="euler", help="Sampler name")
    parser.add_argument("--scheduler", default="sgm_uniform", help="Scheduler name")
    parser.add_argument("--denoise-strength", type=float, default=1.0, help="Denoise strength")
    parser.add_argument("--output-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "text2image"), help="Directory for generated images")
    parser.add_argument("--output-name", default=None, help="Output filename without extension, e.g. my_image")
    parser.add_argument("--https", action="store_true", help="Use HTTPS/WSS")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Log level")
    return parser.parse_args()


def main():
    args = parse_args()
    log = _main_logger(getattr(logging, args.log_level.upper(), logging.INFO))

    log.info("=" * 50)
    log.info("ComfyUI generation started")
    log.info(f"Output directory: {os.path.abspath(args.output_dir)}")
    log.info(f"Log file: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rcomfyui.log')}")
    log.info(
        f"Params | size={args.image_width}x{args.image_height} seed={args.seed} steps={args.steps} "
        f"cfg={args.cfg} sampler={args.sampler} scheduler={args.scheduler} denoise={args.denoise_strength}"
    )
    log.info("=" * 50)

    comfyui_client = ComfyUIClient(
        os.getenv("COMFYUI_SERVER_ADDRESS"),
        args.model,
        https=args.https,
        log_level=getattr(logging, args.log_level.upper(), logging.INFO)
    )

    start_kwargs = {
        "image_width": args.image_width,
        "image_height": args.image_height,
        "steps": args.steps,
        "cfg": args.cfg,
        "sampler": args.sampler,
        "scheduler": args.scheduler,
        "denoise_strength": args.denoise_strength,
        "output_dir": args.output_dir,
        "output_name": args.output_name,
    }
    if args.seed is not None:
        start_kwargs["seed"] = args.seed
    if args.negative_prompt is not None:
        start_kwargs["negative_prompt"] = args.negative_prompt

    saved_files = comfyui_client.start(args.positive_prompt, **start_kwargs)
    if saved_files:
        log.info(f"Saved {len(saved_files)} image(s)")
        # Print first file path for CLI consumers.
        print(saved_files[0])
    else:
        log.warning("No image file was saved")


if __name__ == "__main__":
    main()
