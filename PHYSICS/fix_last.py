import os
import json
import re

def unescape_json_string(escaped_str):
    """Manually unescape JSON string without using json.loads()."""
    result = []
    i = 0
    while i < len(escaped_str):
        if escaped_str[i] == '\\' and i + 1 < len(escaped_str):
            next_char = escaped_str[i + 1]
            if next_char == 'n':
                result.append('\n')
                i += 2
            elif next_char == 't':
                result.append('\t')
                i += 2
            elif next_char == 'r':
                result.append('\r')
                i += 2
            elif next_char == '\\':
                result.append('\\')
                i += 2
            elif next_char == '"':
                result.append('"')
                i += 2
            elif next_char == '/':
                result.append('/')
                i += 2
            elif next_char == 'b':
                result.append('\b')
                i += 2
            elif next_char == 'f':
                result.append('\f')
                i += 2
            elif next_char == 'u' and i + 5 < len(escaped_str):
                # Unicode escape
                hex_str = escaped_str[i+2:i+6]
                try:
                    result.append(chr(int(hex_str, 16)))
                    i += 6
                except:
                    result.append(escaped_str[i])
                    i += 1
            else:
                result.append(escaped_str[i])
                i += 1
        else:
            result.append(escaped_str[i])
            i += 1
    return ''.join(result)

def fix_last_file(filepath):
    """
    Fix p_rectilinear_motion_q20.json with special handling for control characters.
    """
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
    
    # Decode, ignoring problematic characters
    content = raw_bytes.decode('utf-8', errors='replace')
    
    # Remove any actual control characters (not escaped ones)
    # But keep legitimate ones
    content_clean = []
    for char in content:
        if ord(char) < 32:
            if char in '\r\n\t':
                content_clean.append(char)
            # else: skip control character
        else:
            content_clean.append(char)
    content_clean = ''.join(content_clean)
    
    # Now try to extract fields
    data = {}
    
    # Extract input
    input_match = re.search(r'"input"\s*:\s*"((?:[^"\\]|\\["\\\\/bfnrtu]|\\\\.)*?)"', content_clean)
    if input_match:
        raw_input = input_match.group(1)
        data['input'] = unescape_json_string(raw_input)
    
    # Extract output
    output_match = re.search(
        r'"output"\s*:\s*"((?:[^"\\]|\\["\\\\/bfnrtu]|\\\\.)*?)"\s*[,}]',
        content_clean,
        re.DOTALL
    )
    
    if output_match:
        raw_output = output_match.group(1)
        data['output'] = unescape_json_string(raw_output)
    
    if 'input' not in data or 'output' not in data:
        raise ValueError("Could not extract required fields")
    
    return data

def process_last_file():
    """Process the final problematic file."""
    filepath = r'd:\IPD\PHYSDICS\chap 3\p_rectilinear_motion_q20.json'
    
    print('Processing: p_rectilinear_motion_q20.json...')
    
    try:
        data = fix_last_file(filepath)
    except Exception as e:
        print(f'✗ Failed: {e}')
        return False
    
    old_output = data.get('output', '')
    input_text = data.get('input', '')
    
    if not old_output or not input_text:
        print(f'✗ Empty fields')
        return False
    
    # Create thinking
    thinking = old_output.strip()
    
    # Create output
    output_parts = []
    
    # Extract EXECUTE section
    exec_match = re.search(
        r'##\s*EXECUTE\s*THE\s*SOLUTION:\s*(.*?)(?=##\s*VERIFY|##\s*FINAL|$)',
        old_output,
        re.DOTALL | re.IGNORECASE
    )
    
    if exec_match:
        exec_text = exec_match.group(1).strip()
        exec_text = re.sub(r'^\s*---\s*$', '', exec_text, flags=re.MULTILINE)
        exec_text = re.sub(r'\n{3,}', '\n\n', exec_text)
        output_parts.append(exec_text)
    
    # Extract FINAL ANSWER
    final_match = re.search(
        r'##\s*FINAL\s*ANSWERS?:\s*(.*?)$',
        old_output,
        re.DOTALL | re.MULTILINE | re.IGNORECASE
    )
    
    if final_match:
        final_text = final_match.group(1).strip()
        final_text = re.sub(r'^\s*---\s*$', '', final_text, flags=re.MULTILINE)
        output_parts.append('**Answer:** ' + final_text if not final_text.startswith('**') else final_text)
    
    new_output = '\n\n'.join(output_parts).strip() if output_parts else thinking.strip()
    
    # Create new data
    new_data = {
        'input': input_text,
        'thinking': thinking,
        'output': new_output
    }
    
    # Write back
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        print(f'✓ Converted successfully')
        return True
    except Exception as e:
        print(f'✗ Failed to write: {e}')
        return False

if __name__ == '__main__':
    success = process_last_file()
    print(f'\n{"="*50}')
    if success:
        print('All 12 problematic files have been fixed!')
    print(f'{"="*50}')
