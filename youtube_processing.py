import os
import yt_dlp
import tempfile
from prompt import client, generate
from moviepy.editor import AudioFileClip
from response_model import ResponseModel, ContentModel

FILENAME = "temp_audio"
CLIPPED_AUDIO_FILENAME = "temp_audio_clipped"

def process_youtube_links(video_url : str):

    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            # 'username' : "oauth2",
            # 'password' : "",
            'format': 'm4a/bestaudio/best',
            'outtmpl' : os.path.join(temp_dir, f'{FILENAME}.%(ext)s'),
            'verbose' : True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([video_url])
        except Exception as e:
            error_message = f"Error downloading audio : {e}"
            print(error_message)
            return ResponseModel(status=False, message = "Failed to fetch or extract text from the URL", url=video_url)
        
        audio_file_path = os.path.join(temp_dir, f'{FILENAME}.m4a')

        audio_file = AudioFileClip(audio_file_path)

        if audio_file.duration > 240:
                audio_file = audio_file.subclip(0, 240)

        clipped_audio_file_path = os.path.join(temp_dir, f"{CLIPPED_AUDIO_FILENAME}.m4a")
        audio_file.write_audiofile(clipped_audio_file_path, codec='aac')

        audio_file.close()

        with open(clipped_audio_file_path, "rb") as audio_file:
                # Transcribe audio using Whisper model
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,  
                )
        
        text_content = transcription.text
        categories = generate(text_content)
        return ResponseModel(status=True, message = "Categories extracted successfully", url=video_url, content= ContentModel(category_report= categories))