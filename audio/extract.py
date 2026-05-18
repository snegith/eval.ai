from moviepy.editor import VideoFileClip

def extract_audio(video_path, audio_path="data/temp_audio.wav"):
    """
    Extract audio from a video file and write it to a WAV file.

    Args:
        video_path: path to input video
        audio_path: output wav path (defaults to data/temp_audio.wav)
    """
    video = VideoFileClip(video_path)
    try:
        video.audio.write_audiofile(audio_path, logger=None)
    finally:
        video.close()
    return audio_path
