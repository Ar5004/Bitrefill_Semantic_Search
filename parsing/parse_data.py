import os
import re
from bs4 import BeautifulSoup

input_folder = "./parsing/bitrefill_scraped/be/"
output_folder = "./bitrefill_parsed/be/"
os.makedirs(output_folder, exist_ok=True)

# Iterate through files in input folder
for filename in os.listdir(input_folder):
    file_path = os.path.join(input_folder, filename)
    
    # Read file contents
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Parse HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all elements with class matching *container*hi4b7_1
    containers = soup.find_all(class_=re.compile(r'.*container.*hi4b7_1'))
    try:
        containers = containers[0]
        # Extract text from containers
        extracted_text = '\n'.join([container.get_text(strip=True) for container in containers])
        
        # Write to output file
        output_path = os.path.join(output_folder, filename)
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(extracted_text)
        
        print(f"Processed: {filename}")
    except:
        continue