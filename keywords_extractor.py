import os
import subprocess

# Path to the directory containing documents
input_dir = "./bitrefill_parsed/gb/"
output_dir = "./bitrefill_keywords/gb/"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Iterate through all text files
for filename in os.listdir(input_dir):
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, f"{filename}")

    # Read the document
    with open(input_path, "r") as file:
        text = file.read()
        text = file.name.split('/')[-1] + " " + text

    # Define the Ollama CLI command
    command = f"""ollama run llama3.2 "ADVANCED KEYWORD EXTRACTION PROTOCOL

    ABSOLUTE REQUIREMENTS:
    - Generate EXACTLY 20 (NOT LESS NOT MORE) unique keywords/key phrases
    - KEYWORDS are counted as ENTIRE PHRASES, not individual words
    - Output MUST be a strictly comma-separated list
    - NO additional text, explanations, or commentary

    CRITICAL INSTRUCTION:
    - Keywords must be what real words events and activities that users would think about around a product
    - Analyze text for UNDERLYING CONCEPTS AND SOCIETAL EVENTS AND ACTIVITIES, not just surface words
    - IMMEDIATELY output ONLY the comma-separated list
    - NO additional text before or after keywords
    - Keywords must always be small sentences of between 3 and 5 words
    - Keywords must always be in english

    TEXT TO ANALYZE:
    {text}

    GENERATE EXACTLY 20 (NOT LESS NOT MORE) SOCIETAL KEYWORDS NOW:"
    """

    # Run Ollama and get output
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        
        # Save the keywords to a file
        with open(output_path, "w") as outfile:
            outfile.write(result.stdout)
        
        print(f"Processed keywords for {filename}")
    
    except subprocess.CalledProcessError as e:
        print(f"Error processing {filename}: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")