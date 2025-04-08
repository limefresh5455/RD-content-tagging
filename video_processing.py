import os
import tempfile
from pytube import YouTube
import moviepy.editor as mp
from prompt import generate, client
from response_model import ResponseModel
from fastapi import UploadFile, HTTPException, status

# Function to handle video to text conversion
def video_to_text(file: UploadFile):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_video_file = os.path.join(temp_dir, "temp_video.mp4")
            temp_audio_file = os.path.join(temp_dir, "temp_audio.mp3")
            
            with open(temp_video_file, "wb") as temp_video:
                if isinstance(file, str):  # If file is a string, assume it's a file path
                    try:
                        with open(file, "rb") as f:
                            temp_video.write(f.read())
                    except FileNotFoundError:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
                else:
                    temp_video.write(file.file.read())
            
            # Extract audio from video
            try:
                video_clip = mp.VideoFileClip(temp_video_file)
                video_duration = video_clip.duration
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing video file: {str(e)}")
            
            if video_duration >= 240:
                video_clip = video_clip.subclip(0, 240)
            
            try:
                audio_clip = video_clip.audio
                audio_clip.write_audiofile(temp_audio_file)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error extracting audio: {str(e)}")
            finally:
                audio_clip.close()
                video_clip.close()
            
            try:
                with open(temp_audio_file, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file,  
                    )
                text_content = transcription.text
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during transcription: {str(e)}")
            
            try:
                report = generate(text_content)
                return ResponseModel(status=True, message="Categories extracted successfully", filename=file.filename, content=report)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating report: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

def video_extraction_gemini(file: UploadFile):
    pass

# Function to handle YouTube video link
def youtube_video_to_text(video_url: str):
    try:
        yt = YouTube(video_url)
        video_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
        if not video_stream:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No valid video stream found")
        
        output_directory = "Temporary_Video"
        os.makedirs(output_directory, exist_ok=True)
        video_file_path = os.path.join(output_directory, "temp_video.mp4")
        file = video_stream.download(output_path=output_directory, filename="temp_video.mp4")
        
        return video_to_text(file)
    
    except HTTPException as e:
        raise e  # Re-raise FastAPI-specific exceptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing YouTube video: {str(e)}")
