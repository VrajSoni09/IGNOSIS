import os
import json
import re

def repair_and_parse_json(filepath):
    """
    Attempt to repair and parse corrupted JSON files.
    """
    with open(filepath, 'rb') as f:
        raw_content = f.read()
    
    # Try different encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            content = raw_content.decode(encoding)
            break
        except:
            continue
    else:
        raise ValueError("Could not decode file")
    
    # More aggressive escape fixing
    # Replace all backslashes outside of strings and then handle them properly
    
    # First, try to fix incomplete escape sequences
    content = re.sub(r'\\([^"\\bfnrtu/])', r'\\\\\1', content)
    
    # Replace control characters < 32 (except tab, newline, carriage return)
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = ''
        for char in line:
            # Keep valid characters, escape others
            if ord(char) < 32 and char not in '\t\r':
                cleaned_line += f'\\u{ord(char):04x}'
            else:
                cleaned_line += char
        cleaned_lines.append(cleaned_line)
    
    content = '\n'.join(cleaned_lines)
    
    # Try standard JSON parsing
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # If that fails, try to manually extract the structure
        pass
    
    # Last resort: extract fields manually
    data = {}
    
    # Extract filename_suggestion
    match = re.search(r'"filename_suggestion"\s*:\s*"([^"]*)"', content)
    if match:
        data['filename_suggestion'] = match.group(1)
    
    # Extract input
    match = re.search(r'"input"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
    if match:
        data['input'] = json.loads('"' + match.group(1) + '"')
    
    # Extract output (the big one)
    match = re.search(r'"output"\s*:\s*"((?:[^"\\]|\\.)*)"(?:\s*[,}])', content)
    if match:
        data['output'] = json.loads('"' + match.group(1) + '"')
    
    if 'output' not in data or 'input' not in data:
        raise ValueError("Could not extract necessary fields from JSON")
    
    return data

def convert_physics_json_format(base_dir):
    """
    Convert physics JSON files from old format to match chemistry format.
    """
    converted_count = 0
    failed_count = 0
    skipped_count = 0
    failed_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if not file.endswith('.json'):
                continue
                
            filepath = os.path.join(root, file)
            
            try:
                data = repair_and_parse_json(filepath)
                
            except Exception as e:
                print(f'Failed to parse: {file}')
                failed_count += 1
                failed_files.append(file)
                continue
            
            # Skip if already in correct format with exactly 3 keys
            if set(data.keys()) == {'input', 'thinking', 'output'} and len(data) == 3:
                skipped_count += 1
                continue
            
            # Remove filename_suggestion if present
            if 'filename_suggestion' in data:
                del data['filename_suggestion']
            
            old_output = data.get('output', '')
            input_text = data.get('input', '')
            
            if not isinstance(old_output, str) or not old_output.strip():
                skipped_count += 1
                continue
            
            # Generate thinking
            thinking = old_output.strip()
            
            # Generate concise output
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
                if not final_text.startswith('**'):
                    output_parts.append('**Answer:** ' + final_text)
                else:
                    output_parts.append(final_text)
            
            # Create output
            if output_parts:
                new_output = '\n\n'.join(output_parts).strip()
            else:
                new_output = thinking.strip()
            
            # Create new data structure
            new_data = {
                'input': input_text,
                'thinking': thinking,
                'output': new_output
            }
            
            # Write back to file
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                converted_count += 1
                print(f'✓ Converted: {file}')
            except Exception as e:
                print(f'Failed to write: {file}')
                failed_count += 1
    
    return converted_count, failed_count, skipped_count, failed_files

if __name__ == '__main__':
    base_dir = r'd:\IPD\PHYSDICS'
    converted, failed, skipped, failed_files = convert_physics_json_format(base_dir)
    
    print(f'\n{"="*50}')
    print(f'✓ Successfully converted: {converted} files')
    print(f'✗ Failed: {failed} files')
    if failed_files:
        print(f'  Failed files: {failed_files}')
    print(f'⊘ Already correct or skipped: {skipped} files')
    print(f'Total: {converted + failed + skipped} files')
    print(f'{"="*50}')
