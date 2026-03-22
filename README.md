# rComfyUI-t2i

一个通过 ComfyUI HTTP/WebSocket API 触发文生图并将结果保存到本地的 Python 脚本项目。

当前入口文件是 `main.py`。

## 功能概览

- 通过命令行参数控制生成参数（模型、提示词、尺寸、采样参数等）
- 通过 WebSocket 监听执行过程，优先接收二进制图像数据
- 若未收到二进制图像，自动回退到 History API 拉取并下载图像
- 图片默认保存到脚本目录下 `output/text2image`
- 日志同时��出到终端和脚本同目录日志文件 `rcomfyui.log`

## 环境要求

- Python 3.9+
- 一个可访问的 ComfyUI 服务（默认 `127.0.0.1:8188`）
- ComfyUI 服务中存在你指定的模型文件（`--model`）

## 安装依赖

在项目目录执行：

```bash
python -m pip install --upgrade pip
python -m pip install websocket-client pillow
```

## 快速开始

在项目根目录执行（最小可用示例）：

```bash
python main.py \
  --model "your_model.safetensors" \
  --positive-prompt "a dog driving a car in traffic jam, cinematic lighting"
```

默认行为：

- 服务地址：`127.0.0.1:8188`
- 图片输出目录：`./output/text2image`
- 日志文件：`./rcomfyui.log`
- `seed`：随机

## 常用命令示例

### 1) 指定服务器、模型、固定 seed（可复现）

```bash
python main.py \
  --server-address "192.168.31.188:8188" \
  --model "NSFWAnimexl_10.safetensors" \
  --positive-prompt "masterpiece, best quality, city night, neon" \
  --seed 123456
```

### 2) 指定完整采样参数

```bash
python main.py \
  --server-address "127.0.0.1:8188" \
  --model "your_model.safetensors" \
  --positive-prompt "portrait, detailed face, soft light" \
  --negative-prompt "blurry, low quality, bad anatomy" \
  --image-width 1024 \
  --image-height 1024 \
  --steps 30 \
  --cfg 7.5 \
  --sampler "euler" \
  --scheduler "sgm_uniform" \
  --denoise-strength 1.0 \
  --output-dir "./output/text2image" \
  --log-level DEBUG
```

### 3) 连接 HTTPS/WSS 的 ComfyUI

```bash
python main.py \
  --server-address "your-domain:8188" \
  --https \
  --model "your_model.safetensors" \
  --positive-prompt "a futuristic vehicle, cinematic"
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `--server-address` | string | 否 | `127.0.0.1:8188` | ComfyUI 服务地址（不带协议） |
| `--model` | string | 是 | - | ComfyUI 中可用的 checkpoint 文件名 |
| `--positive-prompt` | string | 是 | - | 正向提示词 |
| `--negative-prompt` | string | 否 | 脚本内置默认负面词 | 负向提示词 |
| `--image-width` | int | 否 | `1024` | 输出图像宽度 |
| `--image-height` | int | 否 | `1024` | 输出图像高度 |
| `--seed` | int | 否 | 随机 | 随机种子；传入后可复现 |
| `--steps` | int | 否 | `28` | 采样步数 |
| `--cfg` | float | 否 | `8.0` | CFG scale |
| `--sampler` | string | 否 | `euler` | 采样器名称 |
| `--scheduler` | string | 否 | `sgm_uniform` | 调度器名称 |
| `--denoise-strength` | float | 否 | `1.0` | 去噪强度 |
| `--output-dir` | string | 否 | `./output/text2image` | 输出目录 |
| `--https` | flag | 否 | `false` | 使用 `https/wss` 协议 |
| `--log-level` | string | 否 | `INFO` | 日志级别：`DEBUG/INFO/WARNING/ERROR/CRITICAL` |

## 输出与日志

- 图片输出：默认 `output/text2image`
- 命名示例：`gen_<seed>_<index>.png`
- 日志文件：`rcomfyui.log`

运行时会打印关键信息（输出目录、日志路径、核心参数），便于排查保存失败、连接失败、参数未生效等问题。

## 常见问题排查

### 1) 图片没有保存到本地

优先检查：

- 启动日志中的 `Output directory` 是什么
- 当前用户对该目录是否有写权限
- 任务是否真正执行完（日志中有无“生成任务执行完毕”）
- ComfyUI 服务是否返回了图片（WebSocket 或 History API）

### 2) 提示词提交失败 / 连接失败

- 确认 ComfyUI 已启动并可访问（地址、端口正确）
- 确认 `--https` 与实际服务协议一致
- 确认防火墙或局域网访问策略未拦截

### 3) 模型找不到

- 确认 `--model` 与 ComfyUI 可用 checkpoint 文件名完全一致

## 查看帮助

```bash
python main.py --help
```

## 目录结构（当前）

```text
rComfyUI-t2i/
  main.py
  README.md
  rcomfyui.log              # 运行后生成
  output/
    text2image/             # 运行后生成
```

