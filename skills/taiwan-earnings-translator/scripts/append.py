import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: append.py <file_path> [content]")
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    if len(sys.argv) < 3:
        # 模式：從 stdin 讀取內容 (最穩定，適合長文本)
        content = sys.stdin.read()
    else:
        # 模式：從參數讀取內容
        content = sys.argv[2]
    
    # 確保段落之間有足夠的空行（雙換行）
    if not content.startswith('\n'):
        content = '\n' + content
    if not content.endswith('\n'):
        content = content + '\n'
        
    # 自動建立父目錄 (防呆)
    target_dir = os.path.dirname(os.path.abspath(file_path))
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

if __name__ == "__main__":
    main()
