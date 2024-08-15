import os
import requests
import argparse

def process_text_files(text_files_dir, output_dir, tts_url='http://localhost:8020/tts_to_audio/',
                       speaker_wav='czubowna', language='pl'):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all text files in the directory
    for filename in os.listdir(text_files_dir):
        if filename.endswith('.txt'):
            # Determine the output filename and check if it already exists
            output_filename = f"{os.path.splitext(filename)[0]}.wav"
            output_filepath = os.path.join(output_dir, output_filename)

            # Skip if the audio file already exists
            if os.path.exists(output_filepath):
                print(f"Skipping {filename} -> {output_filename} (already exists)")
                continue

            filepath = os.path.join(text_files_dir, filename)

            # Read the content of the text file
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read().strip()

            # Prepare the JSON payload
            data = {
                "text": text,
                "speaker_wav": speaker_wav,
                "language": language
            }

            # Make the POST request to the TTS server
            response = requests.post(tts_url, json=data, headers={'accept': 'application/json', 'Content-Type': 'application/json'})

            # Save the response content as a .wav file
            with open(output_filepath, 'wb') as audio_file:
                audio_file.write(response.content)

            print(f"Processed {filename} -> {output_filename}")

    print("All files processed successfully!")

if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Process text files and convert them to audio using a TTS service.')

    # Add optional arguments with default values
    parser.add_argument('--text_files_dir', type=str, default='./texts', help='Directory containing the text files')
    parser.add_argument('--output_dir', type=str, default='./audio', help='Directory where audio files will be saved')
    parser.add_argument('--tts_url', type=str, default='http://localhost:8020/tts_to_audio/', help='TTS server URL')
    parser.add_argument('--speaker_wav', type=str, default='czubowna', help='Speaker voice to use')
    parser.add_argument('--language', type=str, default='pl', help='Language for the TTS')

    # Parse the arguments
    args = parser.parse_args()

    # Call the function with parsed arguments
    process_text_files(args.text_files_dir, args.output_dir, args.tts_url, args.speaker_wav, args.language)
