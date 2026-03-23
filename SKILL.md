# rComfyUI-t2i Skill

通过 ComfyUI 文生图，图片自动发送到对应飞书会话。

## 触发时机

- 用户发送"t2i"、"生成图片"、"帮我画"等字眼
- 你想用图片表达情绪时

## 使用方法

### 第一步：获取 chat_id

从消息元数据中获取 `chat_id`，填入 `--chat_id` 参数。

### 第二步：生成提示词

**方式一**：扩写用户的提示词
将用户的中文描述二次扩写为高质量英文提示词，作为 `--positive_prompt`。

**方式二**：情绪表达
将你想表达的情绪自行转化为高质量英文提示词，作为 `--positive_prompt`。

**成品提示词必须是英文。**

### 第三步：执行

```bash
cd scripts
python main.py --chat_id "<chat_id>" --positive_prompt "<prompt>"
```

执行后图片自动发送到对应会话，无需额外操作。

## 禁止事项

**禁止另外写脚本或程序来绕过调用 main.py 或 scripts 里面的其他脚本。**

## 环境变量

| 变量名 | 必填 | 说明 |
|---|---|---|
| `COMFYUI_SERVER_ADDRESS` | 是 | ComfyUI 服务地址 |
| `LARK_APP_ID` | 是 | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | 飞书应用 App Secret |
