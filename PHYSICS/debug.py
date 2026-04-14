import re

def debug_file():
    filepath = r'd:\IPD\PHYSDICS\chap 3\p_rectilinear_motion_q20.json'
    
    with open(filepath, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace')
    
    print(f'File size: {len(content)} chars')
    print(f'Quote count: {content.count(chr(34))}')
    
    # Find the keys
    input_idx = content.find('"input"')
    output_idx = content.find('"output"')
    
    print(f'input key at: {input_idx}')
    print(f'output key at: {output_idx}')
    
    # Show a sample around these
    if input_idx > 0:
        end_idx = min(input_idx + 200, len(content))
        print(f'\nAround input key ({input_idx}-{end_idx}):')
        print(repr(content[input_idx:end_idx]))
    
    if output_idx > 0:
        start = max(0, output_idx)
        end_idx = min(output_idx + 200, len(content))
        print(f'\nAround output key ({start}-):{end_idx}):')
        print(repr(content[start:end_idx]))
    
    # Try simpler regex
    print('\n\nTrying simpler extraction...')
    # Find everything between "input" : " and the next "
    match = re.search(r'"input"\s*:\s*"([^"]*)"', content)
    if match:
        print('Input match OK (simple)')
        input_val = match.group(1)[:100]
        print(f'Input preview: {repr(input_val)}')
    else:
        print('Input match FAILED')
        
if __name__ == '__main__':
    debug_file()
