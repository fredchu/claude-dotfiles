import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: append.py <file_path> [content]")
        sys.exit(1)

    file_path = sys.argv[1]

    if len(sys.argv) < 3:
        content = sys.stdin.read()
    else:
        content = sys.argv[2]

    if not content.startswith('\n'):
        content = '\n' + content
    if not content.endswith('\n'):
        content = content + '\n'

    target_dir = os.path.dirname(os.path.abspath(file_path))
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

if __name__ == "__main__":
    main()
