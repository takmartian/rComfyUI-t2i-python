# rComfyUI-t2i

通过 ComfyUI WebSocket API 进行文生图/文生视频，生成完成后自动发送到飞书会话。

Text-to-image and text-to-video via ComfyUI WebSocket API, with automatic delivery to Lark conversations.

---

## 功能概览 / Features

- 支持 `t2i` 文生图（普通模式 + `--selfee` 模式）
- 支持 `t2v` 文生视频（`--t2v`）
- 自动将生成结果发送到指定飞书会话（图片消息或媒体消息）
- CLI 参数校验通过后立即返回 `OK`，后台异步执行生成与发送

---

## 项目结构 / Project Structure

```text
rComfyUI-t2i/
├── README.md
├── SKILL.md
├── output/                 # 生成结果与日志
└── scripts/
    ├── main.py             # CLI 入口：参数解析、模式选择、后台执行
    ├── t2i.py              # ComfyUI 文生图客户端
    ├── t2v.py              # ComfyUI 文生视频客户端（含首帧提取）
    └── lark_send.py        # 飞书发送（图片/视频）
```

---

## 安装依赖 / Installation

```bash
pip install websocket-client requests requests-toolbelt Pillow opencv-python
```

---

## 环境变量 / Environment Variables

| 变量名 / Variable | 必填 / Required | 说明 / Description |
|---|---|---|
| `COMFYUI_SERVER_ADDRESS` | 是 / Yes | ComfyUI 服务地址，例如 `127.0.0.1:8188` |
| `LARK_APP_ID` | 是 / Yes | 飞书/Lark 应用 App ID |
| `LARK_APP_SECRET` | 是 / Yes | 飞书/Lark 应用 App Secret |
| `LARK_BASE_URL` | 否 / No | API 域名，默认 `https://open.larksuite.com`；国内飞书可用 `https://open.feishu.cn` |

---

## 使用方法 / Usage

```bash
cd scripts
```

### 1) 普通文生图 / Standard t2i

```bash
python main.py \
  --chat_id "<chat_id 或 open_id>" \
  --positive_prompt "夕阳下的海边，一个女孩站在礁石上眺望远方，逆光剪影，海浪拍打，胶片质感"
```

### 2) selfee 文生图 / Selfee t2i

> `--selfee` 仅用于 `t2i`。

```bash
python main.py \
  --chat_id "<chat_id 或 open_id>" \
  --selfee \
  --positive_prompt "sitting at a cozy desk, (focused expression:1.2), warm lamp light, dark room with blue monitor glow"
```

### 3) 文生视频 / t2v

```bash
python main.py \
  --chat_id "<chat_id 或 open_id>" \
  --t2v \
  --positive_prompt "一个时髦的女人走在东京霓虹街头，镜头跟拍，地面潮湿反光，电影感"
```

---

## 参数说明 / Arguments

| 参数 / Argument | 必传 / Required | 说明 / Description |
|---|---|---|
| `--chat_id` | 是 / Yes | 飞书会话 ID（`oc_...`）或用户 open_id（`ou_...`） |
| `--positive_prompt` | 是 / Yes | 生成提示词（图片或视频） |
| `--selfee` | 否 / No | 启用 selfee 模式（仅 `t2i` 有效） |
| `--t2v` | 否 / No | 启用 `t2v` 模式生成视频 |

**参数约束：**
- `--t2v` 与 `--selfee` 不能同时使用

---

## 发送行为 / Delivery Behavior

- 生成图片（`.png/.jpg/...`）时：
  - 上传图片到飞书 `im/v1/images`
  - 发送 `msg_type=image`
- 生成视频（`.mp4`）时：
  - 先上传同名封面图（`xxx.png`）获取 `image_key`
  - 再上传视频获取 `file_key`
  - 发送 `msg_type=media`，`content` 内包含 `file_key` 和 `image_key`

---

## 生成流程 / How It Works

1. `main.py` 校验参数
2. 父进程立即输出 `OK`
3. 子进程后台执行：
   - `t2i`：提交图片工作流并下载图片
   - `t2v`：提交视频工作流并下载 mp4，同时提取首帧为同名 png
4. `lark_send.py` 根据文件类型自动发送到飞书

---

## 输出文件 / Outputs

| 文件 / File | 说明 / Description |
|---|---|
| `output/<name>.png` | t2i 生成图片；或 t2v 的 mp4 首帧图 |
| `output/<name>.mp4` | t2v 生成视频 |
| `output/run.log` | 运行日志 |
| `output/error.log` | 后台异常日志 |

---

## 常见问题 / Notes

- 若发送视频时报“同名 PNG 不存在”，请先确保该 mp4 的首帧图已生成为同名 `.png`。
- 若 `LARK_APP_ID` / `LARK_APP_SECRET` 未配置，会在发送阶段报错。
- 若使用 `open_id` 发送，请传入 `ou_...`；传入 `oc_...` 会按 `chat_id` 处理。
