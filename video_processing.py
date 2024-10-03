import os
import tempfile
from pytube import YouTube
import moviepy.editor as mp
from prompt import generate, client
from response_model import ResponseModel
from fastapi import UploadFile
# _________________________________Function to handle video to text conversion_________________________________________________

def video_to_text(file : UploadFile):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_video_file = os.path.join(temp_dir, "temp_video.mp4")
            temp_audio_file = os.path.join(temp_dir, "temp_audio.mp3")
            with open(temp_video_file, "wb") as temp_video:
                if isinstance(file, str):  # Check if file is a string
                    # If it's a string, assume it's the file path and open it for reading
                    with open(file, "rb") as f:
                        temp_video.write(f.read())
                else:
                    # If it's not a string, assume it's a file object and directly read from it
                    temp_video.write(file.file.read())  
            # Extract audio from video
            video_clip = mp.VideoFileClip(temp_video_file)
            video_duration = video_clip.duration
            # print(video_duration)
            if video_duration <240:
                pass
            else:
                video_clip = video_clip.subclip(0,240)

            audio_clip = video_clip.audio
            audio_clip.write_audiofile(temp_audio_file)
            audio_clip.close()
            video_clip.close()
            with open(temp_audio_file, "rb") as audio_file:
        # Transcribe audio using Whisper model
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,  
                )
            # print(transcription.text)
            text_content = transcription.text
            # print(text_content)
            report=generate(text_content)
            # return report
            return ResponseModel(status=True, message = "Categories extracted successfully", filename = file.filename, content=report)
    except Exception as e:
        # return {"error": str(e)}
        return ResponseModel(status= False, message=f" Error {e}", filename = file.filename, content = "")
    
# __________________________________________Function to handle YouTube video link______________________________________________

def youtube_video_to_text(video_url : str):
    try:
        yt = YouTube(video_url)
        video_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
        output_directory = "Temporary_Video"
        os.makedirs(output_directory, exist_ok=True)
        video_file_path = os.path.join(output_directory, "temp_video.mp4")
        file = video_stream.download(output_path=output_directory, filename="temp_video.mp4")
        return video_to_text(file)
       
    except Exception as e:
        # return {"error": str(e)}
        return ResponseModel(status= False, message=f" Error {e}", url = video_url, content = "")