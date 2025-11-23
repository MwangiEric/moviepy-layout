import streamlit as st
from moviepy.editor import ImageClip
from moviepy_layout import Layout, Gradient

# Streamlit App Title
st.title("🎥 MoviePy Layout Creator")

# User Input for Gradient Background
st.header("Customize Your Gradient Background")
start_color = st.color_picker("Start Color", "#FF0000")
end_color = st.color_picker("End Color", "#0000FF")
direction = st.selectbox("Gradient Direction", [
    "top_to_bottom", "bottom_to_top", 
    "left_to_right", "right_to_left"
])

# Gradient Background
gradient = Gradient(
    direction=direction,
    stops=[
        ((int(start_color[1:3], 16), int(start_color[3:5], 16), int(start_color[5:7], 16), 255), 0.0),
        ((int(end_color[1:3], 16), int(end_color[3:5], 16), int(end_color[5:7], 16), 255), 1.0),
    ]
)

# Video Dimensions
width = 720
height = 1280

# Render the Gradient
bg_image = ImageClip(gradient.render((width, height)), ismask=False)

# Resize the Clip
clip = Layout.asset(bg_image, width=720, height=1280, mode="cover")

# Input for Text
st.header("Add Text Overlay")
text_input = st.text_input("Enter Text:", "Hello, World!")
font_size = st.slider("Font Size", 16, 100, 40)

# Create Text Clip
text_clip = Layout.text(
    text=text_input,
    font_size=font_size,
    font="Arial",
    width=500,
    font_color=(255, 255, 255, 255),
    text_align="center",
    text_wrap=True,
    shadow={"color": (0, 0, 0, 128), "offset": (2, 2), "blur": 5},
    duration=5.0
)

# Create Final Layout
final_layout = Layout.stack(
    children=[(clip, 0), (text_clip, 1)], 
    size=(720, 1280), 
    duration=5.0
)

# Show Preview
st.header("Preview Your Video")
if st.button("Preview Video"):
    st.video(final_layout.preview())  # assuming preview() renders directly

# Download Button (optional)
if st.button("Download Layout as Video"):
    video_path = "output_video.mp4"
    final_layout.write_videofile(video_path, fps=24)
    st.success("Video saved!")

# Display the layout
st.image(clip.preview(), caption="Generated Layout Preview", use_column_width=True)
