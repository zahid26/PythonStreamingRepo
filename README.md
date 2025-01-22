# GStreamer Installation and Streaming Setup

## Introduction to GStreamer
GStreamer is an open-source multimedia framework used for building applications that handle audio, video, and other multimedia data. It provides a comprehensive set of tools to create streaming pipelines for real-time media processing, making it suitable for video playback, recording, streaming, and more.

This guide explains how to install GStreamer on a Linux Ubuntu 22.04 system, verify the installation, and run a Python-based script to stream video using GStreamer.

## Installation Steps

### Update Package Manager
Run the following command to update the package manager:
```bash
sudo apt update
```

### Install GStreamer and Required Plugins
Install GStreamer and its plugins using the following command:
```bash
sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base \
gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa \
gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio \
python3-gst-1.0
```

### Verify Installation
After the installation, verify that GStreamer is correctly installed by running the following command:
```bash
gst-launch-1.0 --version
```
This should output the installed version of GStreamer.
Somewhat like this, might be different according to the version.
```bash
gst-launch-1.0 version 1.20.3
GStreamer 1.20.3
https://launchpad.net/distros/ubuntu/+source/gstreamer1.0
```
### Clone the repo.
Start building cool things.
```bash
git clone https://github.com/zahid26/PythonStreamingRepo.git
```

## Running a Python Script for Streaming
You can stream video from your webcam or an RTSP source using a Python script with GStreamer. Ensure you have Python 3 installed on your system.

### Running the Script
Use the following command to run the script:
This is a smiple script to show the stream.
```bash
python3 gstreamer_webcam_rtsp.py --source 0
```
In this script i have added flask functionlities to Gstreamer with pause and play options- you can run the script and play along.
```bash
python3 flask_gstream_localvideo.py --source 0
```

Replace `--source 0` with the appropriate RTSP link or device ID if needed.

### Notes
- `--source 0` specifies the default webcam on your system.
- RTSP links can be used as the video source for remote streaming.

## Troubleshooting
- Ensure all required dependencies are installed.
- Check for camera or RTSP access permissions if streaming does not work.

By following the steps above, you should have GStreamer set up and ready for multimedia streaming tasks on Ubuntu 22.04. For more details on creating custom pipelines, refer to the [GStreamer documentation](https://gstreamer.freedesktop.org/documentation/).

