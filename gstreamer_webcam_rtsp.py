import gi
import argparse

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gst, GstVideo, GLib

# Initialize GStreamer
Gst.init(None)

class VideoViewer:
    def __init__(self, source):
        self.source = source  # Can be RTSP URL or camera index (e.g., 0, /dev/video0)
        self.pipeline = None

    def create_pipeline(self):
        # Determine if the source is an RTSP stream or a camera device
        if self.source.startswith("rtsp://"):
            # RTSP Pipeline
            pipeline_str = (
                f"rtspsrc location={self.source} latency=0 ! "
                "rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false"
            )
        else:
            # Camera Device Pipeline (e.g., /dev/video0)
            # Convert numeric index to device path (e.g., 0 -> /dev/video0)
            if self.source.isdigit():
                device = f"/dev/video{self.source}"
            else:
                device = self.source
            pipeline_str = (
                f"v4l2src device={device} ! "
                "video/x-raw,format=YUY2,width=640,height=480 ! "
                "videoconvert ! autovideosink sync=false"
            )

        self.pipeline = Gst.parse_launch(pipeline_str)

        # Link the pipeline to a bus to listen for messages
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message, None)

    def on_message(self, bus, message, user_data):
        msg_type = message.type
        if msg_type == Gst.MessageType.EOS:
            print("End of stream")
            self.cleanup()
        elif msg_type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, Debug: {debug}")
            self.cleanup()
        elif msg_type == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, pending_state = message.parse_state_changed()
                print(f"State changed: {old_state} -> {new_state}")

    def start(self):
        self.create_pipeline()
        self.pipeline.set_state(Gst.State.PLAYING)
        print("Pipeline started")

    def cleanup(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            print("Pipeline stopped")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Stream from a camera or RTSP URL")
    parser.add_argument("--source", type=str, required=True,
                       help="Camera device (e.g., 0, /dev/video0) or RTSP URL")
    args = parser.parse_args()

    viewer = VideoViewer(args.source)
    viewer.start()

    # Run the main loop
    try:
        main_loop = GLib.MainLoop()
        main_loop.run()
    except KeyboardInterrupt:
        viewer.cleanup()