# main.py

def capitalize_words_in_file(file_path):
    try:
        # Open the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Capitalize each word in the file
        capitalized_lines = []
        for line in lines:
            # Strip leading/trailing whitespace and capitalize each word
            capitalized_line = ' '.join(word.capitalize() for word in line.split())
            capitalized_lines.append(capitalized_line)
        
        # Write the capitalized content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('\n'.join(capitalized_lines))
        
        print(f"Successfully capitalized words in {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Specify the file to process
    file_path = "cuvinte.txt"
    capitalize_words_in_file(file_path)