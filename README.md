# rComfyUI-t2i

通过 ComfyUI WebSocket API 进行文生图，支持生成完毕后推送图片到飞书。

## 快速概览

| 项目 | 说明 |
|---|---|
| ComfyUI 地址 | `192.168.31.188:8188`（可通过环境变量覆盖） |
| 模型 | Pony (SDXL-based) |
| 输出尺寸 | 1024×1024（默认） |
| 输出格式 | PNG |
| 图片推送 | 飞书（lark_send.py） |

## 目录结构

```
rComfyUI-t2i/
├── main.py          # 文生图主程序（ComfyUIClient 类）
├── lark_send.py     # 飞书图片发送脚本
├── config.ini       # 运行参数配置
├── rcomfyui.log     # 日志输出
└── output/
    └── text2image/   # 生成图片输出目录
```

## main.py

通过 WebSocket 连接 ComfyUI 服务，执行文生图 pipeline：

```
用户输入（中文）
  → AI 扩写提示词（英文）
    → main.py（组装 workflow JSON）
      → ComfyUI WebSocket
        → KSampler（采样）
          → VAEDecode（解码）
            → 保存 PNG
              → lark_send.py（推飞书）
```

### CLI 参数

| 参数 | 必传 | 说明 |
|---|---|---|
| `--model` | ✅ | 模型文件名，如 `ponyRealism_V22.safetensors` |
| `--positive-prompt` | ✅ | 正向提示词（英文） |
| `--negative-prompt` | ❌ | 负向提示词（默认内置） |
| `--image-width` | ❌ | 输出宽度（默认 1024） |
| `--image-height` | ❌ | 输出高度（默认 1024） |
| `--steps` | ❌ | 采样步数（默认 28） |
| `--cfg` | ❌ | CFG 强度（默认 8.0） |
| `--sampler` | ❌ | 采样器（默认 euler） |
| `--scheduler` | ❌ | 调度器（默认 sgm_uniform） |
| `--output-name` | ❌ | 输出文件名（不含路径和扩展名），默认自动生成 |

### 环境变量

| 变量名 | 说明 |
|---|---|
| `COMFYUI_SERVER_ADDRESS` | ComfyUI 服务地址，默认 `192.168.31.188:8188` |

### 调用示例

```bash
python3 main.py \
  --model ponyRealism_V22.safetensors \
  --positive-prompt "a golden retriever holding a Coca-Cola bottle, realistic photography, detailed fur, soft natural lighting" \
  --negative-prompt "worst quality, low quality, blurry, bad anatomy" \
  --image-width 1024 \
  --image-height 1024 \
  --steps 28 \
  --cfg 8.0 \
  --sampler euler \
  --scheduler sgm_uniform \
  --output-name 1742700000123
```

## lark_send.py

将生成的图片推送到飞书会话。

### CLI 参数

| 参数 | 必传 | 说明 |
|---|---|---|
| `--chat_id` | 群聊/频道时 ✅ | 群聊或频道的 chat_id |
| `--open_id` | 私聊时 ✅ | 用户的 open_id |
| `--image_path` | ✅ | 图片本地路径 |

> `chat_id` 和 `open_id` 二选一，都传也可以。

### 环境变量

| 变量名 | 说明 |
|---|---|
| `LARK_APP_ID` | 飞书应用 App ID |
| `LARK_APP_SECRET` | 飞书应用 App Secret |

### 调用示例

```bash
# 推送到群聊
python3 lark_send.py \
  --chat_id ocxxxxxxx \
  --image_path output/text2image/1742700000123.png

# 推送到私聊
python3 lark_send.py \
  --open_id ouxxxxxxx \
  --image_path output/text2image/1742700000123.png
```

### 推送逻辑

1. 上传图片到飞书临时素材（`image_type=message`），获取 `image_key`
2. 调用[发送消息 API](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create)，把 `image_key` 作为消息内容发送
3. 如果 `image_path` 是远程 URL（http/https 开头），跳过上传直接使用 URL

## config.ini

运行参数配置文件，**每次调用 main.py 前会重新读取**，支持热更新。

```ini
[config]
server-address=192.168.31.188:8188
model=ponyRealism_V22.safetensors
image-width=1024
image-height=1024
steps=28
cfg=8.0
sampler=euler
scheduler=sgm_uniform
```

修改此文件后下次调用自动生效，无需重启。

## ComfyUI Workflow 构造逻辑

main.py 内部通过 `generate_workflow_dict()` 拼装 ComfyUI 的 workflow JSON，注入以下关键节点：

```
LoadCheckpoint(model)  →  CLIPTextEncode(positive_prompt)
                              ↓
KSampler(model, seed, steps, cfg, sampler, scheduler)
                              ↓
VAEDecode(samples)     →  SaveImage(output_name)
```

具体节点 ID 和输入对应关系（供参考）：

| 节点 | 用途 |
|---|---|
| 3 | CheckpointLoader（加载模型） |
| 4 | CLIPTextEncode（正向提示词） |
| 5 | CLIPTextEncode（负向提示词） |
| 6 | KSampler（采样器） |
| 7 | EmptyLatentImage（潜在空间尺寸） |
| 8 | VAEDecode（解码） |
| 9 | SaveImage（保存输出） |

## 提示词扩写参考

原文生图 prompt 工程师经验，扩写时参考以下结构：

**主体描述 → 细节补充 → 环境背景 → 光线色调 → 画质标签**

| 用户输入 | 扩写示例 |
|---|---|
| 狗喝可乐 | a golden retriever holding a Coca-Cola bottle, realistic photography, detailed fur, happy expression, soft natural lighting |
| 猫猫抽烟 | a black cat smoking a cigarette, cool attitude, relaxed pose, detailed fur texture, moody atmosphere, cinematic lighting |
| 穿西装的猫 | a cat wearing a tailored black suit, white shirt, red tie, formal pose, studio lighting, sharp focus, high quality |

## 日志

main.py 和 lark_send.py 的日志同时输出到 stdout 和 `rcomfyui.log`（在 main.py 同目录下）。

日志格式：`[HH:MM:SS] [LEVEL] classId: message`

示例：
```
10:17:16 [INFO] __main__.4389475568: ✅ 图片已保存: .../1742700000123.png
10:17:16 [INFO] __main__.4389475568: ✅ 图片发送成功
```
