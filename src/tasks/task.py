from celery import shared_task
from time import sleep
from src.models.main import db, Video, VideoStatus
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
import os

# Define the path for your image
IMAGE_PATH = 'static/logo.png' # <<< CHANGE THIS TO YOUR IMAGE PATH

@shared_task(name="long_task_worker")
def long_task_worker():
    sleep(10)
    return "Task completed"

@shared_task(name="process_video")
def process_video(video_id, unique_filename):
    input_path = f"uploads/{unique_filename}.mp4"
    output_path = f"processed/{unique_filename}.mp4"
    output_dir = os.path.dirname(output_path)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Ensure image exists
    if not os.path.exists(IMAGE_PATH):
        # Handle error: image not found. You might want to log this 
        # or update the video status to an error state.
        print(f"Error: Image not found at {IMAGE_PATH}") 
        # Optionally update video status to reflect the error
        video = db.session.get(Video, video_id)
        if video:
            video.status = VideoStatus.ERROR # Assuming you have an ERROR status
            db.session.commit()
        return f"Processing failed for video {video_id}: Image not found."


    clip = None
    start_image_clip = None
    end_image_clip = None
    final_clip = None

    try:
        clip = VideoFileClip(input_path)
        original_clip = clip # Keep a reference if cropping happens

        width, height = clip.size
        fps = clip.fps # Get frames per second
        desired_ratio = 16 / 9
        current_ratio = width / height

        # Cropping logic (remains the same)
        if current_ratio > desired_ratio:
            new_width = int(height * desired_ratio)
            x_center = width // 2
            x1 = x_center - new_width // 2
            x2 = x_center + new_width // 2
            clip = clip.crop(x1=x1, x2=x2)
        elif current_ratio < desired_ratio:
            new_height = int(width / desired_ratio)
            y_center = height // 2
            y1 = y_center - new_height // 2
            y2 = y_center + new_height // 2
            clip = clip.crop(y1=y1, y2=y2)

        # Get potentially new dimensions after cropping
        final_width, final_height = clip.size 

        # Create image clips
        # Ensure image clips have the same size and fps as the video
        start_image_clip = ImageClip(IMAGE_PATH)\
                            .set_duration(1)\
                            .set_fps(fps)\
                            .resize(newsize=(final_width, final_height))
                            
        end_image_clip = ImageClip(IMAGE_PATH)\
                          .set_duration(1)\
                          .set_fps(fps)\
                          .resize(newsize=(final_width, final_height))

        # Concatenate clips: start_image + video + end_image
        final_clip = concatenate_videoclips([start_image_clip, clip, end_image_clip])

        # Guardar video procesado final
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=fps) # Ensure consistent fps

        # Update database (remains the same)
        video = db.session.get(Video, video_id)
        video.status = VideoStatus.PROCESADO
        video.processed_url = output_path
        video.processed_at = db.func.now()
        db.session.commit()

        return f"Video {video_id} procesado correctamente con imágenes añadidas"

    except Exception as e:
        # Log the error e
        print(f"Error processing video {video_id}: {e}")
        # Optionally update video status to an error state
        video = db.session.get(Video, video_id)
        if video:
            video.status = VideoStatus.ERROR # Assuming you have an ERROR status
            db.session.commit()
        return f"Error processing video {video_id}"
    finally:
        # Close all clips to release resources
        if start_image_clip:
            start_image_clip.close()
        if end_image_clip:
            end_image_clip.close()
        if 'original_clip' in locals() and original_clip: # Close original if it exists
             original_clip.close()
        # If cropping happened, clip is a new object, close it too if it wasn't the original
        if clip and clip != locals().get('original_clip'): 
             clip.close()
        if final_clip:
            final_clip.close()