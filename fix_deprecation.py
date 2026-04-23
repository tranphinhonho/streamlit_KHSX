"""Script để thay thế use_container_width deprecated parameter"""
import os
import re

def fix_file(filepath):
    """Fix use_container_width trong một file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Thay thế width="stretch" -> width="stretch"
        content = re.sub(r'use_container_width\s*=\s*True', 'width="stretch"', content)
        
        # Thay thế width="content" -> width="content"
        content = re.sub(r'use_container_width\s*=\s*False', 'width="content"', content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    count = 0
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment and cache folders
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', '.git']]
        
        for name in files:
            if name.endswith('.py'):
                filepath = os.path.join(root, name)
                if fix_file(filepath):
                    print(f"[OK] Fixed: {filepath}")
                    count += 1
    
    print(f"\nDone! Fixed {count} files!")

if __name__ == '__main__':
    main()
