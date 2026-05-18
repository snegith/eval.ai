import streamlit as st
import av
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

st.set_page_config(page_title="Webcam Test", layout="centered")
st.title("📷 Webcam Sanity Check")

class WebcamProcessor(VideoProcessorBase):
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Simple visual proof that frames are processed
        h, w, _ = img.shape
        cv_color = (0, 255, 0)
        thickness = 2
        img = img.copy()
        img[h//4:3*h//4, w//4:w//4+2] = cv_color  # vertical line

        return av.VideoFrame.from_ndarray(img, format="bgr24")

webrtc_streamer(
    key="webcam-test",
    video_processor_factory=WebcamProcessor,
    media_stream_constraints={"video": True, "audio": False},
)
