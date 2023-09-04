from flask import Flask, render_template, request, flash, send_from_directory, abort
import os
import requests
from moviepy.editor import VideoFileClip
# import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '69922257c78abf4e388533026b89120b9ce205518c2ae9c6'

TEMP_DIRECTORY = "static"

if not os.path.exists(TEMP_DIRECTORY):
    os.makedirs(TEMP_DIRECTORY)


def append_video_details(movie_file):
    # check if file exists, if not, create it and write headers
    if not os.path.isfile('video_details.txt'):
        with open('video_details.txt', 'w') as f:
            f.write('ID,MovieFile\n')
    
    # get existing video details
    video_details = get_video_details()
    
    # determine next id
    if video_details:
        next_id = str(int(max(video_details.keys())) + 1)
    else:
        next_id = '1'
    
    # append new video details
    with open('video_details.txt', 'a') as f:
        f.write(f'{next_id},{movie_file}\n')

    return next_id

def get_video_details(id=None):
    if not os.path.isfile('video_details.txt'):
        return {} if id is None else None
    with open('video_details.txt', 'r') as f:
        lines = f.readlines()[1:]  # skip header
    video_details = {}
    for line in lines:
        id_, movie_file = line.strip().split(',')
        video_details[id_] = {'movie_file': movie_file}
    if id:
        return video_details.get(id)
    return video_details


def download_video(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, 'wb') as out_file:
        for chunk in response.iter_content(chunk_size=8192):
            out_file.write(chunk)


def get_filename_without_extension(url_or_filepath):
    base_name = os.path.basename(url_or_filepath)
    return os.path.splitext(base_name)[0]


def cut_video(filename, url, square_crop=False):
    """Cuts the video and saves with desired filename."""
    clip = VideoFileClip(filename)

    square_prexif = ""

    if square_crop:
        # Get video dimensions
        width, height = clip.size

        # Determine size and position for the square cut
        new_dimension = min(width, height)
        x_center = width / 2
        y_center = height / 2

        # Apply the crop to get a square centered video
        clip = clip.crop(x_center=x_center, y_center=y_center, width=new_dimension, height=new_dimension)

        square_prexif = "sq_"

    duration = clip.duration

    print("Duration: "+str(duration))

    # We're cutting [duration-15:duration-5] from the video.
    subclip = clip.subclip(duration-25, duration-10)
    
    output_filename = os.path.join(TEMP_DIRECTORY, square_prexif+get_filename_without_extension(url) + '_cut.mp4')
    subclip.write_videofile(output_filename, codec='libx264')

    print("File: " + output_filename)

    clip.close()
    subclip.close()

    return output_filename


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        
        video_url = request.form['url']

        if not video_url:
            flash('URL is required!')

            return render_template('video-input.html')
        
        else:     

            temp_filename = os.path.join(TEMP_DIRECTORY, "temp_video.mp4")
            download_video(video_url, temp_filename)

            output_filename = cut_video(temp_filename, video_url)
            
            # Optionally delete the original downloaded file
            os.remove(temp_filename)

            append_video_details(output_filename)

            return render_template('video.html', video_url=output_filename, video_id=1)

    else:

        return render_template('video-input.html')


@app.route('/square', methods=('GET', 'POST'))
def square():
    if request.method == 'POST':
        
        video_url = request.form['url']

        if not video_url:
            flash('URL is required!')

            return render_template('video-input.html')
        
        else:     

            temp_filename = os.path.join(TEMP_DIRECTORY, "temp_video.mp4")
            download_video(video_url, temp_filename)

            output_filename = cut_video(temp_filename, video_url, True)
            
            # Optionally delete the original downloaded file
            os.remove(temp_filename)
            
            append_video_details(output_filename)
    
            return render_template('video.html', video_url=output_filename, video_id=1)

    else:

        return render_template('video-input.html')


@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        
        video_url = request.form['url']

        if not video_url:
            flash('URL is required!')

            return render_template('video-input.html')
        
        else:     

            temp_filename = os.path.join(TEMP_DIRECTORY, "temp_video.mp4")
            download_video(video_url, temp_filename)

            output_filename = cut_video(temp_filename, video_url)
            
            # Optionally delete the original downloaded file
            os.remove(temp_filename)

            append_video_details(output_filename)
            
            directory, filename = os.path.split(output_filename)
            return send_from_directory(directory, filename, as_attachment=True)

            #return render_template('video.html', video_url=output_filename, video_id=1)

    else:

        return render_template('video-input.html')
    

@app.route('/square-download', methods=['GET', 'POST'])
def square_download():
    if request.method == 'POST':
        
        video_url = request.form['url']

        if not video_url:
            flash('URL is required!')

            return render_template('video-input.html')
        
        else:     

            temp_filename = os.path.join(TEMP_DIRECTORY, "temp_video.mp4")
            download_video(video_url, temp_filename)

            output_filename = cut_video(temp_filename, video_url, True)
            
            # Optionally delete the original downloaded file
            os.remove(temp_filename)

            append_video_details(output_filename)
            
            directory, filename = os.path.split(output_filename)
            return send_from_directory(directory, filename, as_attachment=True)

            #return render_template('video.html', video_url=output_filename, video_id=1)

    else:

        return render_template('video-input.html')


@app.route('/video/<id>')
def watch_video(id):
    video_details = get_video_details(id)
    if not video_details:
        abort(404)
    
    video_url = video_details['movie_file']

    return render_template('video.html', video_url=video_url, video_id=id)


@app.route('/videos')
def videos():
    video_details = get_video_details()
    return render_template('videos.html', video_details=video_details)

    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
