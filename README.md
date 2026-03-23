# rComfyUI-t2i

通过 ComfyUI WebSocket API 进行文生图，支持生成完毕后直接推送图片到飞书会话。

## 项目结构

```
rComfyUI-t2i/
├── README.md
├── .gitignore
└── scripts/
    ├── main.py          # CLI 入口
    ├── t2i.py            # ComfyUIClient 文生图核心
    ├── lark_send.py      # 飞书图片推送
    └── config.ini        # 运行参数配置
```

## 安装依赖

```bash
pip install websocket-client requests requests-toolbelt Pillow
```

## config.ini

```ini
[config]
model=ponyRealism_V22.safetensors
image-width=1024
image-height=1024
steps=28
cfg=8.0
sampler=euler
scheduler=sgm_uniform
denoise_strength=1.0
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `model` | ponyRealism_V22.safetensors | 模型文件名 |
| `image-width` | 1024 | 输出宽度 |
| `image-height` | 1024 | 输出高度 |
| `steps` | 28 | 采样步数 |
| `cfg` | 8.0 | CFG 强度 |
| `sampler` | euler | 采样器 |
| `scheduler` | sgm_uniform | 调度器 |
| `denoise_strength` | 1.0 | 去噪强度 |

## 环境变量

| 变量名 | 说明 |
|---|---|
| `COMFYUI_SERVER_ADDRESS` | ComfyUI 服务地址（必填） |
| `LARK_APP_ID` | 飞书应用 App ID |
| `LARK_APP_SECRET` | 飞书应用 App Secret |

## main.py — CLI 入口

```bash
cd scripts
python main.py --chat_id "oc_xxxx" --positive_prompt "1girl, solo, smile"
```

```bash
python main.py \
  --chat_id "oc_05c5e4841b334bc11ec0a5c6678a1d7b" \
  --positive_prompt "masterpiece, best quality, 1girl, solo, looking at viewer, smile"
```

### 参数说明

| 参数 | 必传 | 默认值 | 说明 |
|---|---|---|---|
| `--positive_prompt` | 是 | — | 正向提示词（英文） |
| `--negative_prompt` | 否 | worst quality, low quality... | 负向提示词 |
| `--chat_id` | 二选一 | — | 飞书群 ID（群聊/频道） |
| `--open_id` | 二选一 | — | 飞书用户 open ID（私聊） |

## t2i.py — ComfyUIClient

WebSocket 与 ComfyUI 通信的核心类。

### 节点映射

| 节点 ID | 类型 | 用途 |
|---|---|---|
| 1 | CheckpointLoaderSimple | 加载模型 |
| 2 | CLIPTextEncode | 正向提示词 |
| 3 | CLIPTextEncode | 负向提示词 |
| 4 | EmptyLatentImage | 潜在空间尺寸 |
| 5 | KSampler | 采样器 |
| 6 | VAEDecode | VAE 解码 |
| 7 | PreviewImage | 预览图片（WebSocket 二进制输出） |

### 生成流程

1. 连接 WebSocket `/ws?clientId=xxx`
2. POST `/prompt` 提交任务
3. 监听 WebSocket，收集节点 7 的二进制图片数据
4. 任务完成后，从 `/history/{prompt_id}` 获取输出文件
5. 下载图片保存到 `output/` 目录

### Python API

```python
from t2i import start, ComfyUIClient

# 简单用法
saved_file = start(
    positive_prompt="a golden retriever holding a Coca-Cola bottle, realistic photography",
    negative_prompt="",
    output_name="dog_coke"  # 可选，默认 UUID
)

# 直接用 Client
client = ComfyUIClient(
    positive_prompt="1girl, solo, smile",
    negative_prompt="",
    output_name="test_001"
)
client.gen_image()  # 返回输出文件路径
```

## lark_send.py — 飞书发送

上传图片到飞书临时素材，再发送消息到指定会话。

### 推送流程

1. 调用 `https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal` 获取 token
2. POST `https://open.larksuite.com/open-apis/im/v1/images` 上传图片，获取 `image_key`
3. POST `https://open.larksuite.com/open-apis/im/v1/messages` 发送图片消息

### Python API

```python
from lark_send import start

# 发送到群聊
start(
    image_path="/path/to/image.png",
    chat_id="oc_xxxxxxx",
    open_id=None
)

# 发送到私聊
start(
    image_path="/path/to/image.png",
    chat_id=None,
    open_id="ou_xxxxxxx"
)
```

## 输出

生成的图片保存在项目根目录下的 `output/` 文件夹，文件名 `{output_name}.png`（未指定 output_name 时为 UUID）。

## .gitignore

已忽略：`__pycache__/`、`venv/`、`.venv/`、`output/`、`rcomfyui.log`、`.idea/`、`.DS_Store`
