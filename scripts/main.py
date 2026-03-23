import argparse
import t2i
import lark_send

# 命令行入参
def parse_args():
    parser = argparse.ArgumentParser(description="Lark Image Sender")
    parser.add_argument("--chat_id", type=str, help="Lark chat ID to send the image to")
    parser.add_argument("--open_id", type=str, help="Lark open ID to send the image to")
    parser.add_argument("--positive_prompt", type=str, default="best quality, masterpiece", help="Positive prompt for image generation")
    parser.add_argument("--negative_prompt", type=str, default="", help="Negative prompt for image generation")
    return parser.parse_args()


def main():
    args = parse_args()
    generated_image_path = t2i.start(args.positive_prompt, args.negative_prompt)
    lark_send.start(generated_image_path, args.chat_id, args.open_id)


if __name__ == "__main__":
    main()

# 运行示例：
# python main.py --chat_id "oc_05c5e4841b334bc11ec0a5c6678a1d7b" --positive_prompt "masterpiece, best quality, 1girl, solo, looking at viewer, smile"
