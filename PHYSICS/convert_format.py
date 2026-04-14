import os
import json
import re

def fix_and_parse_json(filepath):
    """
    Parse JSON file with robust handling of escape sequences and special characters.
    """
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
    
    # Try to decode as UTF-8 first
    try:
        content = raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        # Try with latin-1 as fallback
        content = raw_bytes.decode('latin-1')
    
    # Fix common escape sequence issues
    # Replace problematic backslash sequences while preserving valid ones
    content = re.sub(r'\\(?=[^"\\/bfnrtu])', r'\\\\', content)
    
    # Also handle potential control characters by escaping them
    # Replace actual control characters (except newline, tab, carriage return)
    cleaned = []
    for char in content:
        if ord(char) < 32 and char not in '\n\t\r':
            # Replace control character with escaped version
            cleaned.append(f'\\u{ord(char):04x}')
        else:
            cleaned.append(char)
    content = ''.join(cleaned)
    
    return json.loads(content)

def convert_physics_json_format(base_dir):
    """
    Convert physics JSON files from old format to match chemistry format:
    - input: problem statement
    - thinking: full detailed reasoning with all sections
    - output: concise step-by-step solution with final answer
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
                data = fix_and_parse_json(filepath)
                
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
                print(f'Skipped {file}: no valid output')
                skipped_count += 1
                continue
            
            # Generate thinking: keep all the detailed sections
            thinking = old_output.strip()
            
            # Generate concise output: extract EXECUTE and FINAL ANSWER sections
            output_parts = []
            
            # Extract EXECUTE THE SOLUTION section
            exec_match = re.search(
                r'## EXECUTE THE SOLUTION:\s*(.*?)(?=##\s*VERIFY|##\s*FINAL|$)',
                old_output,
                re.DOTALL | re.IGNORECASE
            )
            
            if exec_match:
                exec_text = exec_match.group(1).strip()
                # Clean up the text
                exec_text = re.sub(r'^\s*---\s*\n?', '', exec_text, flags=re.MULTILINE)
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
                # Clean up
                final_text = re.sub(r'^\s*---\s*\n?', '', final_text, flags=re.MULTILINE)
                if not final_text.startswith('**'):
                    output_parts.append('**Answer:** ' + final_text)
                else:
                    output_parts.append(final_text)
            
            # If we have output parts, join them; otherwise use the execution section
            if output_parts:
                new_output = '\n\n'.join(output_parts).strip()
            else:
                # Fallback
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
            except Exception as e:
                print(f'Failed to write: {file} - {e}')
                failed_count += 1
    
    return converted_count, failed_count, skipped_count, failed_files

if __name__ == '__main__':
    base_dir = r'd:\IPD\PHYSDICS'
    converted, failed, skipped, failed_files = convert_physics_json_format(base_dir)
    
    print(f'\n✓ Successfully converted: {converted} files')
    print(f'✗ Failed: {failed} files')
    if failed_files:
        print(f'  Failed files: {failed_files}')
    print(f'⊘ Already in correct format or skipped: {skipped} files')
    print(f'\nTotal: {converted + failed + skipped} files processed')
