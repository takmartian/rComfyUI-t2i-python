# rComfyUI-t2i

通过 ComfyUI WebSocket API 进行文生图，生成完毕后自动推送图片到飞书会话。

## 项目结构

```
rComfyUI-t2i/
├── README.md
├── SKILL.md              # Agent 使用指南
├── .gitignore
└── scripts/
    ├── main.py           # CLI 入口，串联生图与发送
    ├── t2i.py            # ComfyUI 文生图客户端
    ├── lark_send.py      # 飞书图片推送
    └── config.ini        # 运行参数配置
```

## 安装依赖

```bash
pip install websocket-client requests requests-toolbelt Pillow
```

## 环境变量

| 变量名 | 必填 | 说明 |
|---|---|---|
| `COMFYUI_SERVER_ADDRESS` | 是 | ComfyUI 服务地址，如 `192.168.1.1:8188` |
| `LARK_APP_ID` | 是 | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | 飞书应用 App Secret |

## config.ini

```ini
[config]
model=ponyRealism_V22.safetensors
image-width=1024
image-height=1024
steps=45
cfg=5.0
sampler=euler
scheduler=karras
denoise_strength=1.0
selfeeModel=animePastelDream_softBakedVae.safetensors
selfeeWidth=512
selfeeHeight=768
```

| 参数 | 说明 |
|---|---|
| `model` | 默认模型文件名 |
| `image-width` / `image-height` | 默认输出分辨率 |
| `steps` | 采样步数 |
| `cfg` | CFG 强度 |
| `sampler` | 采样器 |
| `scheduler` | 调度器 |
| `denoise_strength` | 去噪强度 |
| `selfeeModel` | selfee 模式专用模型 |
| `selfeeWidth` / `selfeeHeight` | selfee 模式输出分辨率 |

## 使用方法

```bash
cd scripts
```

### 普通模式

```bash
python main.py \
  --chat_id "<chat_id 或 open_id>" \
  --positive_prompt "masterpiece, best quality, 1girl, solo, smile" \
  --negative_prompt "blurry, low quality"
```

### selfee 模式

使用预设的粉发猫耳少女角色，只需描述动作、表情、环境、场所、天气等，人物与负向提示词均已内置。

```bash
python main.py \
  --chat_id "<chat_id 或 open_id>" \
  --selfee \
  --positive_prompt "laughing, sitting under cherry blossoms, petals falling, soft spring light"
```

### 参数说明

| 参数 | 必传 | 说明 |
|---|---|---|
| `--chat_id` | 是 | 飞书群 ID（`oc_` 开头）或用户 open ID（`ou_` 开头） |
| `--positive_prompt` | 是 | 正向提示词（英文） |
| `--negative_prompt` | 否 | 负向提示词，selfee 模式下忽略 |
| `--selfee` | 否 | 启用 selfee 模式，覆盖模型与分辨率，并使用内置角色和负向提示词 |

`--chat_id` 根据前缀自动判断发送类型：
- `oc_` 开头 → 群聊（chat_id）
- `ou_` 开头 → 私聊（open_id）

## 生成流程

1. 连接 ComfyUI WebSocket `/ws?clientId=xxx`
2. POST `/prompt` 提交工作流
3. 监听 WebSocket，收集生成完毕的图片数据
4. 从 `/history/{prompt_id}` 下载图片，保存到 `output/` 目录
5. 上传图片到飞书临时素材，发送消息到指定会话

## 输出

生成的图片保存在项目根目录 `output/` 下，文件名为 UUID（或通过 Python API 指定 `output_name`）。