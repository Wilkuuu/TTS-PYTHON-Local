import os
import librosa
import soundfile as sf
import numpy as np

# Function to load audio from a file
def load_wav(file_path):
    y, sr = librosa.load(file_path, sr=None)  # Load with original sample rate
    return y, sr

# Function to merge audio files with a specific naming convention
def merge_wav_files(files_directory, output_file):
    wav_files = []
    
    # Get all wav files in the directory that match the pattern *_iterationNumber.wav
    for file_name in os.listdir(files_directory):
        if file_name.endswith(".wav") and "_" in file_name:
            wav_files.append(file_name)
    
    # Sort files based on the iteration number at the end of the filename
    try:
        wav_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        print("Files sorted successfully.")
    except Exception as e:
        print(f"Error sorting files: {e}")
        return
    
    # Initialize list for audio data
    audio_data = []
    sample_rate = None

    # Load each wav file and append its audio data
    for wav_file in wav_files:
        file_path = os.path.join(files_directory, wav_file)
        y, sr = load_wav(file_path)
        if sample_rate is None:
            sample_rate = sr  # Use the sample rate from the first file
        elif sr != sample_rate:
            print(f"Warning: Sample rate mismatch in {wav_file}. Skipping file.")
            continue
        audio_data.append(y)
    
    if not audio_data:
        print("No valid audio data to merge!")
        return
    
    # Concatenate all audio data
    merged_audio = np.concatenate(audio_data)
    
    # Save the concatenated audio to output file
    sf.write(output_file, merged_audio, sample_rate)
    print(f"Merged audio saved to {output_file}")

# Usage
files_directory = './audio'  # Directory containing the wav files (current folder)
output_file = 'output.wav'  # Output file name

# Merge all wav files in the directory and save to output.wav
merge_wav_files(files_directory, output_file)

