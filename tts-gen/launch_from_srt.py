import os
import sys
import requests
import argparse
import re

def parse_srt_file(srt_path):
    """
    Parse an SRT file and return a list of subtitle segments.
    Each segment is a dict with: index, start_time, end_time, text
    """
    with open(srt_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split content by double newlines (standard SRT separator)
    # Then parse each block
    blocks = re.split(r'\n\s*\n', content.strip())
    
    segments = []
    # Pattern to match timestamp line: HH:MM:SS,mmm --> HH:MM:SS,mmm
    time_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
    
    for block in blocks:
        if not block.strip():
            continue
            
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        
        # First line should be the index
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue
        
        # Second line should be the timestamp
        time_match = re.search(time_pattern, lines[1])
        if not time_match:
            continue
        
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        
        # Remaining lines are the text (can be multiline)
        text = '\n'.join(lines[2:]).strip()
        
        # Clean up text (normalize whitespace but preserve intentional line breaks)
        # Replace multiple spaces with single space, but keep newlines
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)  # Remove empty lines within text
        
        if text:  # Only add non-empty segments
            segments.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'text': text
            })
    
    return segments

def time_to_filename(time_str):
    """
    Convert SRT time format (00:00:03,700) to filename-safe format (00-00-03-700)
    """
    return time_str.replace(':', '-').replace(',', '-')

def process_srt_files(srt_files_dir, output_base_dir, tts_url='http://localhost:8020',
                      speaker_wav='czubowna', language='pl', overwrite=False):
    """
    Process SRT files and generate separate audio files for each segment.
    Each SRT file gets its own directory with numbered audio files.
    """
    # Convert relative paths to absolute paths
    srt_files_dir = os.path.abspath(srt_files_dir)
    output_base_dir = os.path.abspath(output_base_dir)
    
    # Ensure the output base directory exists
    os.makedirs(output_base_dir, exist_ok=True)
    
    # Iterate through all SRT files in the directory
    for filename in os.listdir(srt_files_dir):
        if filename.endswith('.srt'):
            filepath = os.path.join(srt_files_dir, filename)
            base_name = os.path.splitext(filename)[0]
            
            # Create a directory for this SRT file
            srt_output_dir = os.path.join(output_base_dir, base_name)
            os.makedirs(srt_output_dir, exist_ok=True)
            
            print(f"\nProcessing SRT file: {filename}")
            print(f"Output directory: {srt_output_dir}")
            
            # Parse the SRT file
            try:
                segments = parse_srt_file(filepath)
                print(f"Found {len(segments)} subtitle segments")
            except Exception as e:
                print(f"Error parsing SRT file {filename}: {e}")
                continue
            
            # Process each segment
            for order, segment in enumerate(segments, start=1):
                # Format filename with zero-padded order (01-99) and start timestamp
                # Format: 01_00-00-03-700.wav
                order_str = f"{order:02d}"
                time_str = time_to_filename(segment['start_time'])
                audio_filename = f"{order_str}_{time_str}.wav"
                audio_filepath = os.path.join(srt_output_dir, audio_filename)
                
                # Skip if file exists and overwrite is False
                if os.path.exists(audio_filepath) and not overwrite:
                    print(f"  Skipping {audio_filename} (already exists)")
                    continue
                
                # Prepare the JSON payload
                data = {
                    "text": segment['text'],
                    "speaker_wav": speaker_wav,
                    "language": language
                }
                
                # Make the POST request to the TTS server
                try:
                    response = requests.post(
                        tts_url + '/tts_to_audio/',
                        json=data,
                        headers={'accept': 'application/json', 'Content-Type': 'application/json'}
                    )
                    response.raise_for_status()
                    
                    # Save the response content as a .wav file
                    with open(audio_filepath, 'wb') as audio_file:
                        audio_file.write(response.content)
                    
                    print(f"  Generated: {audio_filename} (Segment {order}: {segment['start_time']} -> {segment['end_time']})")
                    print(f"    Text: {segment['text'][:50]}{'...' if len(segment['text']) > 50 else ''}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"  Error generating audio for segment {order}: {e}")
                    continue
    
    print("\nAll SRT files processed successfully!")

if __name__ == '__main__':
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Process SRT subtitle files and convert each segment to separate audio files using a TTS service.'
    )
    
    # Add arguments with default values
    parser.add_argument('--srt_files_dir', type=str, default='./texts',
                       help='Directory containing the SRT files')
    parser.add_argument('--output_dir', type=str, default='./audio',
                       help='Base directory where audio files will be saved (each SRT gets its own subdirectory)')
    parser.add_argument('--tts_url', type=str, default='http://localhost:8020',
                       help='TTS server URL')
    parser.add_argument('--speaker_wav', type=str, default='km',
                       help='Speaker voice to use')
    parser.add_argument('--language', type=str, default='pl',
                       help='Language for the TTS')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing files')
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with parsed arguments
    process_srt_files(
        args.srt_files_dir,
        args.output_dir,
        args.tts_url,
        args.speaker_wav,
        args.language,
        args.overwrite
    )

