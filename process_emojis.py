import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import re

def get_emoji_range(start_emoji, end_emoji):
    """Get all emojis between two emojis"""
    start_code = ord(start_emoji)
    end_code = ord(end_emoji)
    if start_code <= end_code:
        return [chr(code) for code in range(start_code, end_code + 1)]
    return []

def parse_emoji_list(emoji_str):
    """Parse emoji list string and return a list of individual emojis"""
    # Remove brackets
    emoji_str = emoji_str.strip('[]')
    emojis = set()  # Use a set to remove duplicates
    
    # Split into possible multiple ranges or single emojis
    segments = emoji_str.split('-')
    
    for i, segment in enumerate(segments):
        # Extract content within braces
        bracket_contents = []
        current_content = ''
        in_bracket = False
        segment_emojis = []
        
        for char in segment:
            if char == '{':
                in_bracket = True
                current_content = ''
            elif char == '}':
                in_bracket = False
                if current_content:
                    bracket_contents.append(current_content)
                current_content = ''
            elif in_bracket:
                current_content += char
            elif char.strip():  # Handle emojis not enclosed in braces
                segment_emojis.append(char)
        
        # Add all content within braces
        for content in bracket_contents:
            if content.strip():
                segment_emojis.append(content)
        
        # Handle ranges
        if i > 0 and segments[i-1].strip() and segment_emojis:
            # Get the last emoji of the previous segment
            prev_segment = segments[i-1].strip('{}').strip()
            prev_emoji = prev_segment[-1] if prev_segment else None
            # Get the first emoji of the current segment
            current_emoji = segment_emojis[0]
            
            if prev_emoji and current_emoji:
                # Add all emojis within the range
                range_emojis = get_emoji_range(prev_emoji, current_emoji)
                emojis.update(range_emojis)
        
        # Add all emojis of the current segment
        emojis.update(segment_emojis)
    
    return list(emojis)

def read_labels(labels_path):
    """Read labels.txt file and return a mapping of emojis to categories"""
    emoji_categories = {}
    if not os.path.exists(labels_path):
        print(f"Warning: File not found {labels_path}")
        return emoji_categories
        
    with open(labels_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Ignore comment lines and empty lines
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Split the line
            if ';' in line:
                parts = [p.strip() for p in line.split(';')]
                if len(parts) >= 2:
                    emoji_list_str = parts[0]
                    category = parts[1]
                    
                    # Skip Flags category
                    if category == 'Flags':
                        continue
                    
                    # Parse emoji list
                    emojis = parse_emoji_list(emoji_list_str)
                    
                    # Map each emoji to category, skip emojis containing \u200d
                    for emoji in emojis:
                        if emoji and '\u200d' not in emoji:  # Ensure emoji is not empty and does not contain \u200d
                            emoji_categories[emoji] = category
    
    return emoji_categories

def generate_shortcode(name):
    """Generate shortcode: replace spaces and symbols with underscores and add colons"""
    if not name:
        return ""
    # Use regex to replace all spaces and symbols with underscores
    # \W matches any non-word character (equivalent to [^a-zA-Z0-9_])
    # + matches the preceding pattern one or more times
    shortcode = re.sub(r'[\W]+', '_', name.lower())
    # Remove leading and trailing underscores
    shortcode = shortcode.strip('_')
    # Add colons
    return f":{shortcode}:"

def process_annotations(input_folder, output_folder, labels_path):
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Read labels.txt to get the mapping of emojis to categories
    emoji_categories = read_labels(labels_path)
    
    # First process en.xml to get the shortcodes mapping
    emoji_shortcodes = {}
    en_file = os.path.join(input_folder, 'en.xml')
    if os.path.exists(en_file):
        try:
            tree = ET.parse(en_file)
            root = tree.getroot()
            
            for elem in root.findall('.//'):
                cp = elem.get('cp')
                if cp is None or cp not in emoji_categories:
                    continue
                
                if elem.get('type') == 'tts':
                    name = elem.text.strip() if elem.text else ""
                    shortcode = generate_shortcode(name)
                    if shortcode:
                        emoji_shortcodes[cp] = [shortcode]
        except Exception as e:
            print(f"Error processing en.xml: {str(e)}")
    else:
        print("Warning: en.xml file not found")
    
    # Process all xml files
    for filename in os.listdir(input_folder):
        if not filename.endswith('.xml'):
            continue
            
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename.replace('.xml', '.json'))
        
        processed_data = defaultdict(lambda: {"name": "", "keywords": [], "category": ""})
        
        try:
            # Parse the XML file
            tree = ET.parse(input_path)
            root = tree.getroot()
            
            # Process each XML element
            for elem in root.findall('.//'):
                cp = elem.get('cp')
                if cp is None:
                    continue
                    
                # Skip emojis not in labels.txt
                if cp not in emoji_categories:
                    continue
                    
                if elem.get('type') == 'tts':
                    name = elem.text.strip() if elem.text else ""
                    processed_data[cp]["name"] = name
                    # Use shortcodes from en.xml
                    processed_data[cp]["shortcodes"] = emoji_shortcodes.get(cp, [])
                    processed_data[cp]["category"] = emoji_categories[cp]
                else:
                    if elem.text:
                        keywords = [kw.strip() for kw in elem.text.strip().split('|')]
                        processed_data[cp]["keywords"].extend(keywords)
                        processed_data[cp]["category"] = emoji_categories[cp]
            
            # Convert to final output format
            output_data = []
            for cp, data in processed_data.items():
                # Remove duplicate keywords
                data["keywords"] = list(dict.fromkeys(data["keywords"]))
                # Create an ordered dictionary
                ordered_data = {
                    "category": data["category"],
                    "codepoints": cp,
                    "keywords": data["keywords"],
                    "name": data["name"],
                    "shortcodes": emoji_shortcodes.get(cp, [])
                }
                output_data.append(ordered_data)
            
            # Write to JSON file, ensuring keys are sorted
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, sort_keys=True)
            
            print(f"Processing completed: {output_path}")
            
        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")

if __name__ == "__main__":
    input_folder = "annotations"
    output_folder = "output"
    labels_path = "properties/labels.txt"
    process_annotations(input_folder, output_folder, labels_path)