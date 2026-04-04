import argparse
import multiprocessing
import os
import sys
import t2i
import t2v
import lark_send


def parse_args():
    parser = argparse.ArgumentParser(description="ComfyUI Generation → Lark Sender")
    parser.add_argument("--chat_id", type=str, help="Lark chat ID (oc_) or open ID (ou_)")
    parser.add_argument("--positive_prompt", type=str, default="", help="Prompt for generation")
    parser.add_argument("--selfee", action="store_true", help="Use selfee model/size (t2i only)")
    parser.add_argument("--t2v", action="store_true", help="Use t2v module to generate video")
    return parser.parse_args()


def validate(args):
    if not args.chat_id:
        print("Error: --chat_id is required", file=sys.stderr)
        sys.exit(1)
    if not args.positive_prompt:
        print("Error: --positive_prompt is required", file=sys.stderr)
        sys.exit(1)
    if args.t2v and args.selfee:
        print("Error: --selfee is only supported for t2i mode", file=sys.stderr)
        sys.exit(1)


def _run(args):
    try:
        if args.t2v:
            generated_file_path = t2v.start(args.positive_prompt)
        else:
            generated_file_path = t2i.start(args.positive_prompt, selfee=args.selfee)
        lark_send.start(generated_file_path, args.chat_id)
    except Exception:
        import traceback
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "error.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            traceback.print_exc(file=f)


def main():
    args = parse_args()
    validate(args)

    if hasattr(os, 'fork'):
        pid = os.fork()
        if pid > 0:
            print("OK")
            sys.exit(0)
        # 子进程：脱离终端，后台执行
        os.setsid()
        with open(os.devnull, 'r') as dn:
            os.dup2(dn.fileno(), sys.stdin.fileno())
        with open(os.devnull, 'w') as dn:
            os.dup2(dn.fileno(), sys.stdout.fileno())
            os.dup2(dn.fileno(), sys.stderr.fileno())
        _run(args)
    else:
        p = multiprocessing.Process(target=_run, args=(args,), daemon=False)
        p.start()
        print("OK")
        sys.exit(0)


if __name__ == "__main__":
    main()

# 运行示例：

# 文生图：
# python main.py --chat_id "oc_05c5e4841b334bc11ec0a5c6678a1d7b" --positive_prompt "masterpiece, best quality, 1girl, solo, looking at viewer, smile"

# 文生视频
# python main.py --t2v --chat_id "oc_05c5e4841b334bc11ec0a5c6678a1d7b" --positive_prompt "一个时髦的女人走在东京的街道上，到处都是温暖的霓虹灯和生动的城市标志。她穿着黑色皮夹克、红色长裙、黑色靴子，拿着一个黑色钱包。她戴着太阳镜，涂着红色的口红。她走起路来自信而随意。街道是潮湿和反光的，创造了一个彩色灯光的镜子效果。许多行人走来走去。"
