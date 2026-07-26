import http.server
import socketserver
import json
import os
import shutil
import cgi
import urllib.request
import webbrowser
import threading
import time
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from proglog import ProgressBarLogger

PORT = 8000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, 'temp_uploads')
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

progress_data = {"percent": 0, "action": "Initializing..."}
last_heartbeat = time.time()

class MyBarLogger(ProgressBarLogger):
    def bars_callback(self, bar, attr, value, old_value):
        total = self.bars[bar]['total']
        if total > 0:
            progress_data["percent"] = int((value / total) * 100)
            if bar == 'chunk':
                progress_data["action"] = "Mixing Audio..."
            elif bar == 't':
                progress_data["action"] = "Rendering Video..."
            else:
                progress_data["action"] = "Processing..."

class VideoMakerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_heartbeat
        if self.path == '/heartbeat':
            # Receive ping from the browser
            last_heartbeat = time.time()
            self.send_response(200)
            self.end_headers()
        elif self.path == '/audio-list':
            files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode('utf-8'))
        elif self.path == '/progress':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(progress_data).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/generate':
            global progress_data
            progress_data = {"percent": 0, "action": "Downloading & Preparing files..."}
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
            )

            duration = float(form.getvalue('duration', 4.0))
            fade_duration = float(form.getvalue('fade', 0.5))

            audio_path = None
            if 'custom_audio' in form and form['custom_audio'].filename:
                audio_file = form['custom_audio']
                audio_path = os.path.join(TEMP_DIR, audio_file.filename)
                with open(audio_path, 'wb') as f:
                    f.write(audio_file.file.read())
            else:
                preset_name = form.getvalue('preset_audio')
                if preset_name:
                    audio_path = os.path.join(AUDIO_DIR, preset_name)

            if not audio_path or not os.path.exists(audio_path):
                self.send_error(400, "Error: Audio file not found or selected.")
                return

            image_paths = []
            total_items = int(form.getvalue('total_items', 0))
            
            for i in range(total_items):
                file_key = f"item_{i}_file"
                url_key = f"item_{i}_url"
                
                if file_key in form and form[file_key].filename:
                    img = form[file_key]
                    img_path = os.path.join(TEMP_DIR, f"img_{i}_{img.filename}")
                    with open(img_path, 'wb') as f:
                        f.write(img.file.read())
                    image_paths.append(img_path)
                elif url_key in form:
                    url = form.getvalue(url_key)
                    if url:
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req) as response:
                                img_path = os.path.join(TEMP_DIR, f"img_web_{i}.jpg")
                                with open(img_path, 'wb') as f:
                                    f.write(response.read())
                                image_paths.append(img_path)
                        except Exception as e:
                            print(f"Failed to download image {url}: {e}")

            if not image_paths:
                self.send_error(400, "Error: No images were successfully loaded.")
                return

            target_w, target_h = 1080, 1920
            clips = []
            img_clips_to_close = []

            for path in image_paths:
                bg = ColorClip(size=(target_w, target_h), color=(128, 128, 128), duration=duration)
                img_clip = ImageClip(path)
                img_clips_to_close.append(img_clip) 
                
                if img_clip.h / img_clip.w > target_h / target_w:
                    img_clip = img_clip.resized(height=target_h)
                else:
                    img_clip = img_clip.resized(width=target_w)

                if img_clip.w > target_w: img_clip = img_clip.resized(width=target_w)
                if img_clip.h > target_h: img_clip = img_clip.resized(height=target_h)

                img_clip = img_clip.with_position('center').with_duration(duration)
                composite = CompositeVideoClip([bg, img_clip]).with_effects([
                    CrossFadeIn(fade_duration), CrossFadeOut(fade_duration)
                ])
                clips.append(composite)

            progress_data = {"percent": 0, "action": "Assembling clips..."}
            final_clip = concatenate_videoclips(clips, padding=-fade_duration, method="compose")
            
            output_filename = "output_reel.mp4"
            output_path = os.path.join(BASE_DIR, output_filename)
            
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration > final_clip.duration:
                audio_clip = audio_clip.subclipped(0, final_clip.duration)
            
            final_clip = final_clip.with_audio(audio_clip)

            logger = MyBarLogger()
            final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=logger)

            final_clip.close()
            audio_clip.close()
            for c in clips: c.close()
            for ic in img_clips_to_close: ic.close()

            try:
                shutil.rmtree(TEMP_DIR)
            except Exception:
                pass

            progress_data = {"percent": 100, "action": "Complete (sent to Downloads)"}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "file": output_filename}).encode('utf-8'))


def monitor_heartbeat(server):
    """Background thread that kills the server if the browser tab is closed."""
    global last_heartbeat
    time.sleep(5) # Give the browser time to open initially
    while True:
        # If no ping received for 5 seconds, assume tab is closed
        if time.time() - last_heartbeat > 5.0:
            print("\nBrowser tab closed. Shutting down server...")
            os._exit(0) # Forcefully kill the python process
        time.sleep(1)


with socketserver.TCPServer(("", PORT), VideoMakerHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    
    # Start the watchdog thread
    threading.Thread(target=monitor_heartbeat, args=(httpd,), daemon=True).start()
    
    # Automatically open the browser
    webbrowser.open(f'http://localhost:{PORT}')
    
    # Start serving
    httpd.serve_forever()