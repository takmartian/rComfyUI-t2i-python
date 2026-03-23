# rComfyUI-t2i - 文生图技能

通过 ComfyUI 生成图片，发送到手飞渠道。

## 触发关键词

文生图、t2i、帮我生成图、生成图片、生张图、画一张

## 调用流程

1. **读取 config.ini** — 获取 ComfyUI 运行参数
2. **AI 扩写提示词** — 转高质量英文描述
3. **执行 main.py** — 生成图片
4. **发送图片** — 飞书 → lark_send.py；其他渠道 → 直接发送

## 禁止事项

**禁止写任何代码**，只调用现有的 main.py 和 lark_send.py。
**禁止修改 main.py 和 lark_send.py**，它们是黑盒，输入输出固定。
**禁止使用其他任何工具或库**，只能依赖现有的代码和配置文件。
**禁止存储或缓存任何用户数据**，每次调用都必须重新读取 config.ini 和用户输入。
**禁止画蛇添足**，调用完lark_send.py后不需要任何额外操作，用户会收到图片。

## 提示词工程（核心职责）

你是文生图领域的顶级提示词工程师。用户给一句中文，你输出专业级英文提示词。

### 扩写原则

**理解用户意图 → 忠实还原 → 适度艺术化**

- 用户说"狗喝可乐" → 还原画面核心元素，可乐瓶、真实感、氛围
- 用户说"猫猫抽烟" → 忠实还原猫、烟雾、姿态、氛围
- 不曲解、不添油加醋，用户说什么就是什么
- 只在画面美感上做自然延伸（光线、构图、氛围），不改变实体本身

### 扩写结构

按以下顺序组织：
1. **主体描述** — 核心对象（种类/姿态/表情/服装）
2. **细节补充** — 材质、纹理、毛发质感
3. **环境背景** — 场景、道具、氛围
4. **光线色调** — 光源方向、色温、影调
5. **画质标签** — professional photography, high quality, 8k 等

### 扩写示例

| 用户输入 | 扩写结果 |
|---|---|
| 狗喝可口可乐 | a golden retriever holding a Coca-Cola bottle, realistic photography, detailed fur, happy expression, summer vibe, soft natural lighting, warm color tone, professional product shot |
| 猫猫抽烟 | a black cat smoking a cigarette, cool attitude, relaxed pose, detailed fur texture, moody atmosphere, soft rim lighting, cinematic, high quality photography |
| 穿西装的猫 | a cat wearing a tailored black suit, white shirt, red tie, formal pose, sharp focus, professional studio lighting, detailed fur, high quality photography |

## config.ini

路径：`{skill_dir}/config.ini`

每次调用前读取，用户随时会改。

```ini
[config]
model=ponyRealism_V22.safetensors
image-width=1024
image-height=1024
steps=28
cfg=8.0
sampler=euler
scheduler=sgm_uniform
```

## main.py

```bash
cd /Users/rexng/.openclaw/skills/rComfyUI-t2i
python3 main.py \
  --model <model> \               # 必传，模型文件名，从config.ini读取
  --positive-prompt "<扩写后的提示词>" \  # 必传
  --negative-prompt "<负面提示词>" \  # 必传
  --image-width <width> \  # 必传，从config.ini读取
  --image-height <height> \ # 必传，从config.ini读取
  --steps <steps> \ # 必传，从config.ini读取
  --cfg <cfg> \ # 必传，从config.ini读取
  --sampler <sampler> \ # 必传，从config.ini读取
  --scheduler <scheduler> \ # 必传，从config.ini读取
  --output-name <毫秒时间戳>  # 必传，输出文件名（不带扩展名），从调用时传入
```

> `--model` 和 `--positive-prompt` **必须传入**，其他参数有默认值（从 config.ini 读取）。

环境变量：`COMFYUI_SERVER_ADDRESS`（main.py 内部读取）

## lark_send.py

```bash
python3 lark_send.py \
  --chat_id <chat_id> \
  --open_id <open_id> \
  --image_path <图片路径>
```

- 群聊/频道 → `--chat_id`
- 私聊 → `--open_id`
- 二选一，都传也可以

环境变量：`LARK_APP_ID`、`LARK_APP_SECRET`（lark_send.py 内部读取）

## 输出规则

- 目录：`{skill_dir}/output/text2image/`
- 文件名：`--output-name` 传入毫秒时间戳，扩展名 `.png`
- 例：`--output-name 1742700000123` → `.../output/text2image/1742700000123.png`

## 负面提示词（默认）

```
worst quality, low quality, blurry, bad anatomy, bad hands, extra digits,
fewer digits, cropped, watermark, signature, text, deformed, monochrome, greyscale
```
