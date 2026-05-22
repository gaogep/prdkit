import os
import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("错误: 缺少文件名参数。")
        print("用法: prdkit-create-md <markdown文件路径>")
        sys.exit(1)

    filename = sys.argv[1]
    if not filename.lower().endswith(".md"):
        filename += ".md"

    if os.path.exists(filename):
        print(f"提示: 文件 '{filename}' 已经存在，操作已取消。")
        sys.exit(1)

    try:
        parent = os.path.dirname(filename)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filename, "w", encoding="utf-8"):
            pass
        print(f"✅ 成功创建空的 Markdown 文件: {filename}")
    except OSError as exc:
        print(f"❌ 创建文件时发生错误: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
