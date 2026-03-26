# rComfyUI-t2i Skill

通过 ComfyUI 文生图，图片自动发送到对应飞书会话。

## 触发时机

- 用户发送"t2i"、"生成图片"、"帮我画"等字眼
- 你想用图片表达情绪时
- **每次你回复任何一句话时**：分析该句话所传达的情绪或语境，用 `--selfee` 模式生成一张对应的 selfee 图片

## 使用方法

### 第一步：获取 chat_id

从消息元数据中获取 `chat_id`，填入 `--chat_id` 参数。

`--chat_id` 根据前缀自动判断发送类型：
- `oc_` 开头 → 群聊（chat_id）
- `ou_` 开头 → 私聊（open_id）

### 第二步：生成提示词

你需要代入**精通 Stable Diffusion 提示词**的专家角色来撰写提示词，善用权重语法（如 `(tag:1.3)`）、质量标签、镜头语言、光影描述等。

**方式一：扩写用户的提示词**

将用户的中文描述扩写为高质量英文提示词，作为 `--positive_prompt`，可附加 `--negative_prompt`。

**方式二：selfee 模式（情绪表达）**

当你想用图片表达自己的情绪，或**每次回复任何一句话时**，使用 `--selfee` 参数。此模式下：

- 人物已预设（粉发猫耳少女），**无需在提示词中描述人物**
- `--positive_prompt` **只需描述**：动作、表情、情绪、环境、场所、天气、光影、构图等
- `--negative_prompt` 已固定，**无需填写**
- **每句话配图规则**：提取该句的核心情绪或语境（如解释代码→专注/思考，报错→紧张/困惑，完成任务→开心/满足），据此撰写 prompt

> 示例：心情很好 → `--positive_prompt "laughing, sitting under cherry blossoms, petals falling, soft spring light, park bench"`
> 示例：正在思考 → `--positive_prompt "thinking, finger on chin, soft indoor light, slightly tilted head, calm expression"`
> 示例：任务完成 → `--positive_prompt "arms raised in celebration, big smile, confetti falling, bright room"`

**成品提示词必须是英文。**

### 第三步：执行

普通模式：
```bash
cd scripts
python main.py --chat_id "<chat_id 或 open_id>" --positive_prompt "<prompt>" [--negative_prompt "<negative>"]
```

selfee 模式（情绪表达）：
```bash
cd scripts
python main.py --chat_id "<chat_id 或 open_id>" --selfee --positive_prompt "<动作/表情/环境/天气/场所等>"
```

执行后图片自动发送到对应会话，无需额外操作。

## 项目结构

```
rComfyUI-t2i/
├── SKILL.md              # 本文件，Agent 使用指南
├── README.md             # 项目说明
└── scripts/              # 核心脚本目录（禁止修改）
    ├── main.py           # 入口，解析命令行参数，串联生图与发送
    ├── t2i.py            # ComfyUI 文生图客户端
    ├── lark_send.py      # 飞书图片发送
    └── config.ini        # 配置文件（模型、分辨率、采样参数等）
```

## 禁止事项

**禁止另外写脚本或程序来绕过调用 main.py 或 scripts 里面的其他脚本。**

**禁止修改 skills 目录里面的任何文件或内容。**

## 环境变量

| 变量名 | 必填 | 说明 |
|---|---|---|
| `COMFYUI_SERVER_ADDRESS` | 是 | ComfyUI 服务地址 |
| `LARK_APP_ID` | 是 | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | 飞书应用 App Secret |