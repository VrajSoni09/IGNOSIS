import os
import json
import re
import ast

def fix_problematic_json(filepath):
    """
    Fix JSON files with literal backslash-n sequences and UTF-8 characters.
    """
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
    
    # Decode as UTF-8 (these files are UTF-8 with special characters)
    content = raw_bytes.decode('utf-8')
    
    # The issue: the JSON has literal \\n sequences
    # We need to be more careful about parsing
    
    #Try to parse as-is first
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        pass
    
    # If that fails, try to manually fix by finding structure
    # Look for the JSON structure
    
    # Find the start
    start = content.find('{')
    if start == -1:
        raise ValueError("No JSON object found")
    
    # Try to find the matching closing brace
    # Count braces to find the end
    brace_count = 0
    pos = start
    in_string = False
    escape_next = False
    
    while pos < len(content):
        char = content[pos]
        
        if escape_next:
            escape_next = False
            pos += 1
            continue
        
        if char == '\\':
            escape_next = True
            pos += 1
            continue
        
        if char == '"':
            in_string = not in_string
            pos += 1
            continue
        
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found the end
                    json_str = content[start:pos+1]
                    try:
                        return json.loads(json_str)
                    except:
                        pass
                    break
        
        pos += 1
    
    raise ValueError("Could not parse JSON")

def convert_corrupted_files(base_dir):
    """
    Convert only the 12 problematic physics JSON files.
    """
    problem_files = [
        'p_rectilinear_motion_q10.json',
        'p_rectilinear_motion_q11.json',
        'p_rectilinear_motion_q13.json',
        'p_rectilinear_motion_q14.json',
        'p_rectilinear_motion_q20.json',
        'p_rectilinear_motion_q3.json',
        'p_rectilinear_motion_q4.json',
        'p_rectilinear_motion_q5.json',
        'p_rectilinear_motion_q6.json',
        'p_rectilinear_motion_q7.json',
        'p_rectilinear_motion_q8.json',
        'p_rectilinear_motion_q9.json',
    ]
    
    converted = 0
    failed = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file not in problem_files:
                continue
            
            filepath = os.path.join(root, file)
            print(f'Processing: {file}...')
            
            try:
                data = fix_problematic_json(filepath)
            except Exception as e:
                print(f'  ✗ Failed to parse: {e}')
                failed.append(file)
                continue
            
            # Remove filename_suggestion
            if 'filename_suggestion' in data:
                del data['filename_suggestion']
            
            old_output = data.get('output', '')
            input_text = data.get('input', '')
            
            if not isinstance(old_output, str):
                failed.append(file)
                continue
            
            # Create thinking and output
            thinking = old_output.strip()
            
            # Extract solution summary for output
            output_parts = []
            
            # Extract EXECUTE THE SOLUTION section
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
            
            # Extract FINAL ANSWER section
            final_match = re.search(
                r'##\s*FINAL\s*ANSWERS?:\s*(.*?)$',
                old_output,
                re.DOTALL | re.MULTILINE | re.IGNORECASE
            )
            
            if final_match:
                final_text = final_match.group(1).strip()
                final_text = re.sub(r'^\s*---\s*$', '', final_text, flags=re.MULTILINE)
                output_parts.append('**Answer:** ' + final_text if not final_text.startswith('**') else final_text)
            
            # Build new output
            if output_parts:
                new_output = '\n\n'.join(output_parts).strip()
            else:
                new_output = thinking.strip()
            
            # Create new structure
            new_data = {
                'input': input_text,
                'thinking': thinking,
                'output': new_output
            }
            
            # Write back
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                print(f'  ✓ Converted successfully')
                converted += 1
            except Exception as e:
                print(f'  ✗ Failed to write: {e}')
                failed.append(file)
    
    return converted, failed

if __name__ == '__main__':
    base_dir = r'd:\IPD\PHYSDICS'
    converted, failed = convert_corrupted_files(base_dir)
    
    print(f'\n{"="*50}')
    print(f'✓ Converted: {converted} files')
    if failed:
        print(f'✗ Failed: {len(failed)} files')
        for f in failed:
            print(f'  - {f}')
    print(f'{"="*50}')
