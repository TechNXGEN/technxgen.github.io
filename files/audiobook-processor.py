import argparse
import numbers
import subprocess
import math
import os
from pathlib import Path


def get_duration(input_file):
    """Get the duration of the audio file in seconds using ffprobe"""
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not result.stdout.rstrip() == "":
        print(f"Total duration: {result.stdout.rstrip()} seconds")
        return float(result.stdout.rstrip())
    if not result.stderr == "":
        print(f"Error: {result.stderr}")
    return 0


def process_audiobook(
        input_file: str,
        output_dir: str,
        chunk_duration: int = 10,
        speed_factor: float = 1.05,
        start_chunk: int = 1,
        max_chunks: int = None,
        audio_quality: int = "192",
        sample_rate: int = "44100",
) -> None:
    """
    Process an M4B audiobook file (or any other media supported by FFMpeg)
    
    Args:
        input_file: Path to input M4B file
        output_dir: Directory to save output files
        chunk_duration: Duration of each chunk in minutes
        speed_factor: Speed adjustment factor (1.0 = normal speed)
        start_chunk: First chunk to process (1-based indexing)
        max_chunks: Maximum number of chunks to process (None = process all)
        audio_quality: Output audio bitrate
        sample_rate: Output audio sample rate
    """

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get total duration
    total_duration = get_duration(input_file)
    if total_duration == 0:
        print(f"Cannot determine total audiobook duration, make sure the file is valid.\n\rFile: {input_file}")
        return

    chunk_seconds = chunk_duration * 60
    total_chunks = math.ceil(total_duration / chunk_seconds)

    if max_chunks is not None:
        total_chunks = min(total_chunks, start_chunk + max_chunks - 1)

    print(f"Total duration: {total_duration / 60:.1f} minutes")
    print(f"Processing chunks {start_chunk} to {total_chunks}")

    # Process each chunk
    for i in range(start_chunk - 1, total_chunks):
        start_time = i * chunk_seconds
        duration = min(chunk_seconds, total_duration - start_time)

        output_file = os.path.join(
            output_dir,
            f"{Path(input_file).stem}_{i + 1:03}.mp3"
        )

        # Build FFMpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if exists
            '-ss', str(start_time),  # Start time
            '-i', input_file,  # Input file
            '-t', str(duration),  # Duration to extract
        ]

        # Add speed adjustment filter if needed
        if (speed_factor <= 0.0) or ((1 / speed_factor % 2) <= 0.0):
            print(f"Speed factor is too small, operation aborted.")
            return

        if speed_factor != 1.0:
            # atempo filter is limited to 0.5 to 2.0 range
            # for larger changes, we need to chain multiple atempo filters
            if speed_factor > 2.0:
                tempo_chain = ','.join(['atempo=2.0'] * (math.floor(speed_factor / 2)) +
                                       [f'atempo={speed_factor % 2}'])
            elif speed_factor < 0.5:
                tempo_chain = ','.join(['atempo=0.5'] * (math.floor(2 / speed_factor)) +
                                       [f'atempo={1 / (1 / speed_factor % 2)}'])
            else:
                tempo_chain = f'atempo={speed_factor}'

            cmd.extend(['-filter:a', tempo_chain])

        # Add output options
        cmd.extend([
            '-b:a', f'{audio_quality}k',  # Audio bitrate
            '-map_metadata', '-1',  # Remove metadata
            '-map', 'a',            # Remove video
            '-ar', f'{sample_rate}',         # Sample Rate
            output_file
        ])

        # Execute FFMpeg command
        print(f"Processing chunk {i + 1}/{total_chunks}: {output_file}")
        try:
            print(f"\n\rCommand:\n\r{' '.join(cmd)}\n\r")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error processing chunk {i + 1}: {e}")
            continue


def main():
    parser = argparse.ArgumentParser(description="Split and speed up M4B audiobooks using FFMpeg")
    parser.add_argument("input_file", help="Input M4B file path")
    parser.add_argument("output_dir", help="Output directory path")
    parser.add_argument("--chunk-duration", type=int, default=10,
                        help="Duration of each chunk in minutes (default: 10)")
    parser.add_argument("--speed", type=float, default=1.00,
                        help="Playback speed factor (default: 1.05)")
    parser.add_argument("--start-chunk", type=int, default=1,
                        help="First chunk to process (default: 1)")
    parser.add_argument("--max-chunks", type=int,
                        help="Maximum number of chunks to process (default: all)")
    parser.add_argument("--quality", default="192",
                        help="Output audio bitrate (default: 192k)")
    parser.add_argument("--sample-rate", default="44100",
                        help="Output audio bitrate (default: 44100k)")
    
    args = parser.parse_args()

    process_audiobook(
        args.input_file,
        args.output_dir,
        args.chunk_duration,
        args.speed,
        args.start_chunk,
        args.max_chunks,
        args.quality,
        args.sample_rate
    )


if __name__ == "__main__":
    main()
