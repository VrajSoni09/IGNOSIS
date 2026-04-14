import os
import json
import re

def extract_json_fields_regex(filepath):
    """
    Extract JSON fields using regex when standard JSON parsing fails.
    """
    with open(filepath, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    data = {}
    
    # Extract each field using careful regex
    # Extract input
    input_match = re.search(r'"input"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
    if input_match:
        raw_input = input_match.group(1)
        # Unescape manually
        data['input'] = raw_input.replace('\\\\', '\\').replace('\\"', '"')
        # Handle special: replacements
        data['input'] = data['input'].replace('\\n', '\n').replace('\\t', '\t')
    
    # Extract filename_suggestion (optional)
    filename_match = re.search(r'"filename_suggestion"\s*:\s*"([^"]*)"', content)
    if filename_match:
        data['filename_suggestion'] = filename_match.group(1)
    
    # Extract output (the tricky one - it's very long)
    # Find "output" key and get everything until the next top-level key or }
    output_match = re.search(
        r'"output"\s*:\s*"((?:[^"\\]|\\.|(?<!\\\\)\\\\")*)",\s*(?:}|\n\})',
        content,
        re.DOTALL
    )
    
    if not output_match:
        # Try without the trailing context
        output_match = re.search(
            r'"output"\s*:\s*"((?:[^"\\]|\\.)*?)"\s*\}',
            content,
            re.DOTALL
        )
    
    if output_match:
        raw_output = output_match.group(1)
        # Unescape
        data['output'] = raw_output.replace('\\\\', '\\').replace('\\"', '"')
        data['output'] = data['output'].replace('\\n', '\n').replace('\\t', '\t')
    
    if 'input' not in data or 'output' not in data:
        raise ValueError("Could not extract required fields")
    
    return data

def convert_remaining_files(base_dir):
    """
    Convert the remaining 11 problematic files using regex extraction.
    """
    problem_files = [
        'p_rectilinear_motion_q10.json',
        'p_rectilinear_motion_q11.json',
        'p_rectilinear_motion_q13.json',
        'p_rectilinear_motion_q14.json',
        'p_rectilinear_motion_q20.json',
        'p_rectilinear_motion_q3.json',
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
                data = extract_json_fields_regex(filepath)
            except Exception as e:
                print(f'  ✗ Failed to extract: {e}')
                failed.append(file)
                continue
            
            # Remove filename_suggestion
            if 'filename_suggestion' in data:
                del data['filename_suggestion']
            
            old_output = data.get('output', '')
            input_text = data.get('input', '')
            
            if not old_output or not input_text:
                print(f'  ✗ Empty fields')
                failed.append(file)
                continue
            
            # Create thinking and output
            thinking = old_output.strip()
            
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
            
            # Build output
            if output_parts:
                new_output = '\n\n'.join(output_parts).strip()
            else:
                new_output = thinking.strip()
            
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
                print(f'  ✓ Converted')
                converted += 1
            except Exception as e:
                print(f'  ✗ Failed to write: {e}')
                failed.append(file)
    
    return converted, failed

if __name__ == '__main__':
    base_dir = r'd:\IPD\PHYSDICS'
    converted, failed = convert_remaining_files(base_dir)
    
    print(f'\n{"="*50}')
    print(f'✓ Converted: {converted} files')
    if failed:
        print(f'✗ Failed: {len(failed)} files')
    else:
        print('All files converted successfully!')
    print(f'{"="*50}')
