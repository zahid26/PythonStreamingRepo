import gi
import argparse
import os
import threading
import numpy as np
import cv2
from flask import Flask, Response, render_template_string

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GstVideo, GLib

Gst.init(None)

app = Flask(__name__)

class VideoPlayer:
    def __init__(self, source):
        self.source = source
        self.pipeline = None
        self.is_playing = False
        self.lock = threading.Lock()
        self.main_loop = None
        self.sink = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        if self.is_file_source() and not self.source.startswith("file://"):
            if not os.path.isfile(self.source):
                raise FileNotFoundError(f"File not found: {self.source}")

    def is_file_source(self):
        return self.source.startswith("file://") or os.path.isfile(self.source)

    def create_pipeline(self):
        pipeline_str = ""
        
        if self.is_file_source():
            file_path = os.path.abspath(self.source.replace("file://", ""))
            uri = GLib.filename_to_uri(file_path)
            # Removed autovideosink to prevent local display
            pipeline_str = (
                f"uridecodebin uri={uri} ! "
                "videoconvert ! "
                "videoscale ! video/x-raw,width=640,height=480 ! "
                "videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
            )

        self.pipeline = Gst.parse_launch(pipeline_str)
        self.sink = self.pipeline.get_by_name("sink")
        self.sink.set_property("emit-signals", True)
        self.sink.connect("new-sample", self.on_new_sample)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message, None)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            struct = caps.get_structure(0)
            width = struct.get_value("width")
            height = struct.get_value("height")
            
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                frame = np.ndarray(
                    shape=(height, width, 3),
                    dtype=np.uint8,
                    buffer=map_info.data
                )
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                ret, jpeg = cv2.imencode('.jpg', frame_bgr)
                if ret:
                    with self.frame_lock:
                        self.current_frame = jpeg.tobytes()
                buffer.unmap(map_info)
                
        return Gst.FlowReturn.OK

    def on_message(self, bus, message, user_data):
        msg_type = message.type
        if msg_type == Gst.MessageType.EOS:
            print("End of stream")
            self.stop()
        elif msg_type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, Debug: {debug}")
            self.stop()
        elif msg_type == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, _ = message.parse_state_changed()
                print(f"State changed: {old_state.value_nick} → {new_state.value_nick}")
                self.is_playing = new_state == Gst.State.PLAYING
        return True

    def play(self):
        def _play():
            with self.lock:
                if self.pipeline:
                    self.pipeline.set_state(Gst.State.PLAYING)
        GLib.idle_add(_play)

    def pause(self):
        def _pause():
            with self.lock:
                if self.pipeline and self.is_playing:
                    self.pipeline.set_state(Gst.State.PAUSED)
        GLib.idle_add(_pause)

    def stop(self):
        def _stop():
            with self.lock:
                if self.pipeline:
                    self.pipeline.set_state(Gst.State.NULL)
                if self.main_loop:
                    self.main_loop.quit()
        GLib.idle_add(_stop)

@app.route('/')
def index():
    return render_template_string('''
        <html>
            <head><title>Video Stream</title></head>
            <body>
                <h1>Video Stream</h1>
                <img src="/video_feed">
                <div>
                    <button onclick="fetch('/video_feed/play')">Play</button>
                    <button onclick="fetch('/video_feed/pause')">Pause</button>
                </div>
            </body>
        </html>
    ''')

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            with player.frame_lock:
                frame = player.current_frame
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                yield b' '

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/play')
def play_video():
    player.play()
    return "Playback started", 200

@app.route('/video_feed/pause')
def pause_video():
    player.pause()
    return "Playback paused", 200

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Streaming Media Player")
    parser.add_argument("--source", type=str, required=True,
                       help="File path, RTSP URL, or camera device")
    args = parser.parse_args()

    player = VideoPlayer(args.source)
    player.create_pipeline()

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False, 
        use_reloader=False,
        threaded=True
    ))
    flask_thread.daemon = True
    flask_thread.start()

    player.main_loop = GLib.MainLoop()
    
    try:
        player.play()
        player.main_loop.run()
    except KeyboardInterrupt:
        player.stop()
    
    print("Player exited cleanly")

