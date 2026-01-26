import os

def check_for_null_bytes(directory):
    print(f"Scanning {directory} for null bytes...")
    corrupted_files = []
    
    for root, dirs, files in os.walk(directory):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                        if b'\x00' in content:
                            print(f"FOUND NULL BYTES: {path}")
                            corrupted_files.append(path)
                except Exception as e:
                    pass # Ignore errors

    if not corrupted_files:
        print("No null bytes found in .py files.")
    else:
        print(f"Found {len(corrupted_files)} corrupted files.")

if __name__ == "__main__":
    check_for_null_bytes('.')
