import os

def sanitize_files(directory):
    print(f"Sanitizing Python files in {directory}...")
    sanitized_count = 0
    
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
                        print(f"Fixing {path}...")
                        # Remove null bytes
                        new_content = content.replace(b'\x00', b'')
                        # Also remove UTF-16 BOM if present in the middle (PowerShell append)
                        new_content = new_content.replace(b'\xff\xfe', b'')
                        
                        with open(path, 'wb') as f:
                            f.write(new_content)
                        sanitized_count += 1
                        
                except Exception as e:
                    print(f"Error handling {path}: {e}")

    if sanitized_count == 0:
        print("No corrupted files found to sanitize.")
    else:
        print(f"Successfully sanitized {sanitized_count} files!")

if __name__ == "__main__":
    sanitize_files('.')
