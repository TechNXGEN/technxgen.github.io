import os
import mimetypes
import pathlib
from typing import List, Set

def is_text_file(filepath: str, text_extensions: Set[str]) -> bool:
    """
    Determine if a file is a text file based on its extension and mime type.
    """
    # Check if extension is in our allowed list
    ext = pathlib.Path(filepath).suffix.lower()
    if ext in text_extensions:
        return True
    
    # Use mime type as fallback
    mime_type, _ = mimetypes.guess_type(filepath)
    return mime_type is not None and mime_type.startswith('text/')

def collect_files(directory: str, text_extensions: Set[str]) -> List[str]:
    """
    Recursively collect all text files in the given directory.
    """
    text_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_text_file(filepath, text_extensions):
                text_files.append(filepath)

    # Sort for consistent output
    return sorted(text_files)

def create_combined_file(files: List[str], output_file: str):
    """
    Create a single file containing the content of all input files with proper formatting.
    """
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    # Write file header
                    outfile.write(f"// Filepath: {filepath}\n\n\n")
                    outfile.write("```\n")
                    
                    # Write file content
                    outfile.write(infile.read())
                    
                    # Write file footer
                    outfile.write("\n```\n\n\n")
            except UnicodeDecodeError:
                print(f"Warning: Could not read {filepath} as text. Skipping.")
            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")

def main():
    # Define the extensions you want to include
    text_extensions = {
        '.h', '.cpp', '.cs', '.py', '.json', '.xml', '.txt', '.md', 
        '.ini', '.config', '.yaml', '.yml', '.uplugin', '.build',
        '.html', '.css', '.js', '.java', '.swift', '.m', '.mm',
        '.sh', '.bat', '.cmd', '.ps1', '.gradle', '.properties'
    }
    
    # Get directory from command line argument or use current directory
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_file = 'combined_source_code.txt'
    
    # Collect and process files
    print(f"Scanning directory: {directory}")
    files = collect_files(directory, text_extensions)
    print(f"Found {len(files)} text files")
    
    # Create combined file
    create_combined_file(files, output_file)
    print(f"Created combined file: {output_file}")

if __name__ == '__main__':
    main()