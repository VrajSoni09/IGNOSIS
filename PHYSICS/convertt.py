import os
import json
import re

base_dir = r'd:\\IPD\\PHYSDICS'
missing_exec = []
missing_final = []

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.json'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Escaping invalid backslashes for JSON parse
            content = re.sub(r'\\(?=[^"\\/bfnrtu])', r'\\\\', content)
            
            try:
                data = json.loads(content)
            except Exception as e:
                print('Failed to parse:', file, e)
                continue

            if 'thinking' in data and 'output' in data and 'input' in data and len(data) == 3:
                continue
                
            old_output = data.get('output', '')
            if not isinstance(old_output, str):
                continue
            
            # Generate new thinking
            thinking = old_output
            thinking = re.sub(r'^##\s*', '', thinking, flags=re.MULTILINE)
            thinking = re.sub(r'^\s*---\s*\n?', '', thinking, flags=re.MULTILINE)
            thinking = re.sub(r'^(FINAL ANSWERS?:|FINAL ANSWER)\s*', '**Answer:** ', thinking, flags=re.MULTILINE)
            thinking = re.sub(r'\n{3,}', '\n\n', thinking)

            # Generate new output
            exec_match = re.search(r'## EXECUTE THE SOLUTION:\s*(.*?)\s*(?=## VERIFY)', old_output, re.DOTALL)
            final_match = re.search(r'## FINAL ANSWERS?:\s*(.*)', old_output, re.DOTALL)

            new_output_parts = []
            if exec_match:
                part = exec_match.group(1).strip()
                part = re.sub(r'^\s*---\s*\n?', '', part, flags=re.MULTILINE)
                new_output_parts.append(part)
            if final_match:
                part = final_match.group(1).strip()
                part = re.sub(r'^\s*---\s*\n?', '', part, flags=re.MULTILINE)
                new_output_parts.append('**Answer:**\n' + part)

            new_output_text = '\n\n'.join(new_output_parts)
            
            if not exec_match:
                missing_exec.append(file)
            if not final_match:
                missing_final.append(file)

            if not new_output_text.strip():
                # fallback just in case both didn't match, maybe the structure is different
                new_output_text = thinking

            new_data = {
                'input': data.get('input', ''),
                'thinking': thinking.strip(),
                'output': new_output_text.strip()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)

print('Missing EXECUTE THE SOLUTION:', len(missing_exec))
if missing_exec: print(missing_exec[:5])
print('Missing FINAL ANSWER:', len(missing_final))
if missing_final: print(missing_final[:5])
print('Done!')
