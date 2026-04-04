# rComfyUI-t2i Skill

这是一个用于飞书/Lark 场景的 AI Agent Skill：
- 根据用户消息调用 ComfyUI 生成图片或视频
- 自动发送到目标会话
- 统一通过 `scripts/main.py` 执行

---

## 1. 消息触发与模式路由（强制）

- 用户消息以 `t2i` 开头：必须走文生图模式（`t2i`）
- 用户消息以 `t2v` 开头：必须走文生视频模式（`t2v`）
- 未命中前缀时，可按上下文判断；若不确定，优先追问用户要图片还是视频

---

## 2. chat_id 使用规范（强制）

`--chat_id` 参数必须使用飞书/Lark 回调消息中的 `chatId`。

**禁止使用 `senderOpenId`。**

原因：`senderOpenId` 会导致消息发给个人账号，而不是原始会话（尤其群聊会发错位置）。

---

## 3. 参数与模式规则

### 必填参数
- `--chat_id`：回调消息中的 `chatId`
- `--positive_prompt`：提示词

### 可选参数
- `--selfee`：仅用于 `t2i`
- `--t2v`：启用 `t2v` 文生视频

### 约束
- `--t2v` 与 `--selfee` 不能同时使用
- 默认不加 `--t2v` 时，走 `t2i`

---

## 4. Prompt 生成规范（强制）

### 4.1 selfee 模式（`--selfee`）

当你想用表情/自拍表达情绪时，使用 `--selfee`。

规则：
- 角色及外观已固定（代码自动拼接），**不要描述外貌**
- 成品提示词必须是英文
- **必须不少于 50 个英文词**，越细越好

你只需描述以下维度：

| 维度 | 要写什么 | 示例 |
|---|---|---|
| **动作/姿势** | 具体肢体动作 | `sitting cross-legged`, `leaning forward on desk`, `stretching arms above head` |
| **表情/情绪** | 精确的面部表情 | `(focused expression:1.2)`, `blushing with shy smile`, `wide eyes in surprise` |
| **视角/构图** | 镜头位置与取景 | `close-up face shot`, `from slightly above`, `full body`, `dutch angle` |
| **环境/场景** | 具体场所 | `cozy bedroom at night`, `rooftop at golden hour`, `rainy window side` |
| **光影** | 光源与打光方式 | `soft rim lighting`, `warm lamp light`, `moonlight through curtains` |
| **氛围道具** | 强化情绪的细节 | `surrounded by floating code snippets`, `holding a glowing tablet`, `cherry blossoms falling` |

### 4.2 普通文生图模式（t2i）

你是专业 AI 绘画提示词工程师。

收到用户文生图提示词后，必须先扩写，再执行生成。

规则：
- 出图风格：高质感写实摄影/电影感
- 必须描述画面内容，越具体越好
- 可中文或英文
- **扩写不少于 30 个提示词**

扩写时重点覆盖以下维度：

| 维度 | 示例 |
|---|---|
| **主体** | 人物年龄/性别/神态/服装/姿势，或物体/动物/场景 |
| **环境** | 室内/室外、城市/自然、具体地点（如废弃工厂、京都小巷） |
| **时间/天气** | 黄昏、阴天、暴雨后、蓝调时刻 |
| **光影** | 侧逆光、丁达尔光、霓虹灯反光、长曝光车轨 |
| **镜头/构图** | 长焦压缩、大光圈虚化、低角度仰拍、对称构图 |
| **色调/氛围** | 莫兰迪色系、高饱和赛博朋克、胶片颗粒感 |

### 4.3 文生视频模式（t2v）

- 以动态描述为核心：主体动作、镜头运动、场景节奏
- 输出为 `.mp4`，并生成同名首帧 `.png` 用于发送封面

---

## 5. 执行命令

```bash
cd scripts
```

文生图（t2i）：

```bash
python main.py --chat_id "<chatId>" --positive_prompt "<扩写后的提示词>"
```

selfee（t2i）：

```bash
python main.py --chat_id "<chatId>" --selfee --positive_prompt "<不少于50个英文词的selfee提示词>"
```

文生视频（t2v）：

```bash
python main.py --chat_id "<chatId>" --t2v --positive_prompt "<视频提示词>"
```

---

## 6. 发送行为说明

- 图片（`.png/.jpg/...`）：发送 `image`
- 视频（`.mp4`）：发送 `media`，包含：
  - `file_key`（视频）
  - `image_key`（同名 `.png` 封面）

---

## 7. 输出与日志

默认输出目录：项目根目录 `output/`
- `output/<name>.png`：t2i 图片或 t2v 首帧图
- `output/<name>.mp4`：t2v 视频
- `output/run.log`：运行日志
- `output/error.log`：异常日志

CLI 参数校验通过后会立即返回 `OK`，后台执行生成与发送。

---

## 8. 环境变量

| 变量名 | 必填 | 说明 |
|---|---|---|
| `COMFYUI_SERVER_ADDRESS` | 是 | ComfyUI 服务地址（如 `127.0.0.1:8188`） |
| `LARK_APP_ID` | 是 | 飞书/Lark 应用 App ID |
| `LARK_APP_SECRET` | 是 | 飞书/Lark 应用 App Secret |
| `LARK_BASE_URL` | 否 | 默认 `https://open.larksuite.com`；国内可用 `https://open.feishu.cn` |

---

## 9. 规则 5（待补充）

你提供的第 5 条当前为空（仅有“5.”）。
请补充完整后，我会继续合并进本文件。
