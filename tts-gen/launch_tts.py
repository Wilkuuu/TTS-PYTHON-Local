import os
import sys
import requests
import argparse
import subprocess
from datetime import datetime

def split_text_into_chunks(text, max_length):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def process_text_files(text_files_dir, output_dir, tts_url='http://localhost:8020',
                       speaker_wav='czubowna', language='pl', max_chunk_length=600, overwrite=False):
    # Convert relative paths to absolute paths
    text_files_dir = os.path.abspath(text_files_dir)
    output_dir = os.path.abspath(output_dir)
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Iterate through all text files in the directory
    for filename in os.listdir(text_files_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(text_files_dir, filename)
            base_name = os.path.splitext(filename)[0]
            final_output_name = f"{base_name}_{timestamp}.wav"
            final_output_path = os.path.join(output_dir, final_output_name)

            # Skip if the final file exists and overwrite is False
            if os.path.exists(final_output_path) and not overwrite:
                print(f"Skipping {final_output_name} (already exists)")
                continue

            # Read the content of the text file
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read().strip()

            # Split the text into chunks
            text_chunks = split_text_into_chunks(text, max_chunk_length)
            chunk_files = []

            # Process each chunk
            for i, chunk in enumerate(text_chunks, start=1):
                chunk_filename = f"{base_name}_{i}.wav"
                chunk_filepath = os.path.join(output_dir, chunk_filename)
                chunk_files.append(chunk_filepath)

                # Skip if the chunk file exists and overwrite is False
                if os.path.exists(chunk_filepath) and not overwrite:
                    print(f"Skipping {chunk_filename} (already exists)")
                    continue

                # Prepare the JSON payload
                data = {
                    "text": chunk,
                    "speaker_wav": speaker_wav,
                    "language": language
                }

                # Make the POST request to the TTS server
                response = requests.post(tts_url + '/tts_to_audio/', json=data, headers={'accept': 'application/json', 'Content-Type': 'application/json'})

                # Save the response content as a .wav file
                with open(chunk_filepath, 'wb') as audio_file:
                    audio_file.write(response.content)

                print(f"Processed {filename} -> {chunk_filename}")

            # Run glue script with the base name after all chunks are created
            # Only run glue if we have chunk files to merge
            merge_successful = False
            if chunk_files:
                print(f"Running glue script for {base_name} with {len(chunk_files)} files")
                merge_successful = run_glue_script(base_name, output_dir)

            # Delete chunk files only if merge was successful
            if merge_successful:
                for chunk_file in chunk_files:
                    try:
                        os.remove(chunk_file)
                        print(f"Deleted chunk file: {chunk_file}")
                    except Exception as e:
                        print(f"Error deleting chunk file {chunk_file}: {e}")
            else:
                print(f"Merge failed for {base_name}, keeping chunk files")

    print("All files processed successfully!")

def run_glue_script(filename, output_dir):
    try:
        # Get the path to the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        glue_script_path = os.path.join(script_dir, 'glue.py')
        
        # Use the same Python executable that's running this script
        python_executable = sys.executable
        
        # Run glue.py with the correct working directory and audio directory
        result = subprocess.run([python_executable, glue_script_path, os.path.splitext(filename)[0], output_dir], 
                               cwd=script_dir, check=True, capture_output=True, text=True)
        print("glue.py script ran successfully.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running glue.py: {e}")
        print(f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No stderr'}")
        return False

if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Process text files and convert them to audio using a TTS service.')

    # Add arguments with default values
    parser.add_argument('--text_files_dir', type=str, default='./texts', help='Directory containing the text files')
    parser.add_argument('--output_dir', type=str, default='./audio', help='Directory where audio files will be saved')
    parser.add_argument('--tts_url', type=str, default='http://localhost:8020', help='TTS server URL')
    parser.add_argument('--speaker_wav', type=str, default='magMasz', help='Speaker voice to use')
    parser.add_argument('--language', type=str, default='pl', help='Language for the TTS')
    parser.add_argument('--max_chunk_length', type=int, default=150, help='Maximum length of each text chunk in characters')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files')

    # Parse the arguments
    args = parser.parse_args()

    # Call the function with parsed arguments
    process_text_files(args.text_files_dir, args.output_dir, args.tts_url, args.speaker_wav, args.language, args.max_chunk_length, args.overwrite)
