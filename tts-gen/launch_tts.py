import os
import requests
import argparse
import subprocess

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
                       speaker_wav='czubowna', language='pl', max_chunk_length=600):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all text files in the directory
    for filename in os.listdir(text_files_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(text_files_dir, filename)

            # Read the content of the text file
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read().strip()

            # Split the text into chunks
            text_chunks = split_text_into_chunks(text, max_chunk_length)

            # Process each chunk
            for i, chunk in enumerate(text_chunks, start=1):
                output_filename = f"{os.path.splitext(filename)[0]}_{i}.wav"
                output_filepath = os.path.join(output_dir, output_filename)

                # Skip if the audio file already exists
                if os.path.exists(output_filepath):
                    print(f"Skipping {output_filename} (already exists)")
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
                with open(output_filepath, 'wb') as audio_file:
                    audio_file.write(response.content)

                print(f"Processed {filename} -> {output_filename}")

    print("All files processed successfully!")
    run_glue_script()

def run_glue_script():
    try:
        # Assuming glue.py is in the same directory or provide the full path
        subprocess.run(['python3', 'glue.py'], check=True)
        print("glue_file.py script ran successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running glue_file.py: {e}")

if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Process text files and convert them to audio using a TTS service.')

    # Add arguments with default values
    parser.add_argument('--text_files_dir', type=str, default='./texts', help='Directory containing the text files')
    parser.add_argument('--output_dir', type=str, default='./audio', help='Directory where audio files will be saved')
    parser.add_argument('--tts_url', type=str, default='http://localhost:8020', help='TTS server URL')
    parser.add_argument('--speaker_wav', type=str, default='czubowna', help='Speaker voice to use')
    parser.add_argument('--language', type=str, default='pl', help='Language for the TTS')
    parser.add_argument('--max_chunk_length', type=int, default=600, help='Maximum length of each text chunk in characters')

    # Parse the arguments
    args = parser.parse_args()

    # Call the function with parsed arguments
    process_text_files(args.text_files_dir, args.output_dir, args.tts_url, args.speaker_wav, args.language, args.max_chunk_length)
