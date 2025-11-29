import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import tempfile
import os
import math
import requests
import gc
import time
from moviepy.editor import VideoFileClip

# --------------------------------------------------------
# CONFIGURATION (CRITICAL FIXES)
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 6
TEXT_BG_COLOR = (0, 0, 0, 180)

# FIXED: Increased font size range for mobile readability
FONT_SIZE_MIN = 80  # Was 60
FONT_SIZE_MAX = 220  # Was 130
DEFAULT_FONT_SIZE = 120  # Was 85

# Royalty-free backgrounds
BACKGROUND_VIDEOS = {
    "Ocean Waves": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4",
    "Floating Clouds": "https://cdn.pixabay.com/video/2023/06/15/164555-806155701_large.mp4",
    "Misty Forest": "https://cdn.pixabay.com/video/2022/01/27/105839-710637991_large.mp4",
    "Gentle Fire": "https://cdn.pixabay.com/video/2022/02/15/110845-717522810_large.mp4",
    "Waterfall": "https://cdn.pixabay.com/video/2023/05/01/162303-799296582_large.mp4",
    "Starry Sky": "https://cdn.pixabay.com/video/2022/07/26/115453-752008984_large.mp4",
}
TEMPLATES = ["Glass Morphism", "Neon Pulse", "Minimal Zen", "Golden Waves", "Modern Grid"]

# --------------------------------------------------------
# CACHED LOADERS (IMPROVED)
# --------------------------------------------------------
@st.cache_resource
def load_font():
    """Load font with fallbacks for mobile readability"""
    try:
        resp = requests.get("https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf", timeout=10)
        if resp.status_code == 200:
            return io.BytesIO(resp.content)
    except:
        pass
    
    # FIXED: Added larger default font
    try:
        return ImageFont.truetype("arialbd.ttf", 150)
    except:
        pass
    
    return ImageFont.load_default()

def get_font(size):
    """Ensure minimum readable size"""
    size = max(80, size)  # CRITICAL: Enforce minimum size
    font_io = load_font()
    if font_io:
        try:
            return ImageFont.truetype(font_io, size)
        except:
            pass
    return ImageFont.truetype("arialbd.ttf", size) if size > 80 else ImageFont.load_default()

# --------------------------------------------------------
# TEXT RENDERING (COMPLETELY REWRITTEN)
# --------------------------------------------------------
def get_optimal_font_size(quote, max_width, max_lines=3):
    """
    Calculate optimal font size based on quote length and screen space
    Ensures text fits in max_lines with readable size
    """
    words = quote.split()
    if not words:
        return 120
    
    # Calculate ideal font size based on word count
    base_size = 140
    if len(words) <= 6:
        base_size = 180
    elif len(words) <= 12:
        base_size = 140
    else:
        base_size = 100
    
    # Find maximum size that fits within constraints
    for size in range(base_size, 80, -5):
        font = get_font(size)
        lines = []
        current = []
        for word in words:
            test = ' '.join(current + [word])
            if font.getbbox(test)[2] <= max_width:
                current.append(word)
            else:
                if current: lines.append(' '.join(current))
                current = [word]
        if current: lines.append(' '.join(current))
        
        # Check constraints
        if len(lines) <= max_lines and all(font.getbbox(line)[2] <= max_width for line in lines):
            return size
    
    return 80  # Minimum readable size

def render_text_layer(quote, author, font_size, y_offset, show_bg):
    """Create text layer with proper sizing and positioning"""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # FIXED: Use larger minimum font
    font_size = max(80, font_size)
    font_q = get_font(font_size)
    font_a = get_font(max(50, int(font_size * 0.5)))
    
    # FIXED: Better line splitting logic
    words = quote.split()
    lines = []
    current = []
    max_line_width = WIDTH - 200
    
    for word in words:
        test = ' '.join(current + [word])
        if font_q.getbbox(test)[2] <= max_line_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    
    # Ensure we don't exceed 3 lines (mobile-friendly)
    if len(lines) > 3:
        # Try larger font with more aggressive splitting
        lines = []
        current = []
        for word in words:
            test = ' '.join(current + [word])
            if font_q.getbbox(test)[2] <= max_line_width * 0.9:
                current.append(word)
            else:
                if current:
                    lines.append(' '.join(current))
                current = [word]
        if current:
            lines.append(' '.join(current))
        # If still too many lines, truncate
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] += "..."
    
    # Calculate vertical spacing
    line_h = int(font_q.size * 1.4)
    total_height = len(lines) * line_h
    
    # Draw background for readability
    if show_bg:
        for i, line in enumerate(lines):
            y = y_offset + i * line_h
            left, top, right, bottom = font_q.getbbox(line)
            w, h = right - left, bottom - top
            x = WIDTH // 2 - w // 2
            draw.rectangle(
                [x - 30, y - h - 15, x + w + 30, y + h + 10],
                fill=TEXT_BG_COLOR,
                outline="#00F0FF",
                width=2
            )
    
    # Draw quote text
    for i, line in enumerate(lines):
        y = y_offset + i * line_h
        draw.text((WIDTH // 2, y), line, fill="#FFFFFF", font=font_q, anchor="mm")
    
    # Draw author
    if author:
        author_y = y_offset + total_height + 60
        draw.text(
            (WIDTH // 2, author_y),
            author,
            fill="#00F0FF",
            font=font_a,
            anchor="mm"
        )
    
    # Draw CTA
    draw.text(
        (WIDTH // 2, HEIGHT - 180),
        "Save this wisdom ✨",
        fill="#00F0FF",
        font=get_font(55),
        anchor="mm"
    )
    
    return img

# --------------------------------------------------------
# RENDER ENGINE (SIMPLIFIED & FIXED)
# --------------------------------------------------------
def render_frame(quote, author, font_size, y_offset, show_bg, bg_array, logo):
    """Render final frame with proper text sizing"""
    # Create background layer
    bg = Image.fromarray(bg_array)
    
    # Add logo
    if logo:
        bg.paste(logo, (70, 60), logo)
    
    # Create and composite text layer
    text_layer = render_text_layer(quote, author, font_size, y_offset, show_bg)
    bg.paste(text_layer, (0, 0), text_layer)
    
    return np.array(bg)

# --------------------------------------------------------
# UI
# --------------------------------------------------------
st.set_page_config(page_title="WYSIWYG Quote Studio", layout="wide")
with st.sidebar:
    st.image("https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037", width=120)
    st.title("✨ WYSIWYG Studio")
    
    quote = st.text_area("Your Quote", "Breathe. It's just a bad day, not a bad life.", height=100)
    author = st.text_input("Author", "— Anonymous")
    
    st.markdown("### 🎨 Text Style")
    # FIXED: Much larger default size
    font_size = st.slider("Font Size", FONT_SIZE_MIN, FONT_SIZE_MAX, DEFAULT_FONT_SIZE, step=5)
    
    # Show actual size
    st.markdown(f"<div style='background:#222; color:#00F0FF; padding:8px; border-radius:6px; text-align:center; font-weight:bold;'>Font Size: {font_size}</div>", 
                unsafe_allow_html=True)
    
    # FIXED: Better vertical positioning
    y_offset = st.slider("Vertical Position", 350, 850, 520, step=10)
    show_bg = st.checkbox("Text Background", value=True)
    
    st.markdown("### 🖼️ Background")
    bg_mode = st.radio("Type", ["Online Video", "Animated Template"])
    if bg_mode == "Online Video":
        bg_name = st.selectbox("Video", list(BACKGROUND_VIDEOS.keys()))
        video_url = BACKGROUND_VIDEOS[bg_name]
    else:
        template = st.selectbox("Template", TEMPLATES)
        video_url = None
    
    export = st.button("🚀 Export 6s Video", type="primary", use_container_width=True)

# --------------------------------------------------------
# TRUE WYSIWYG PREVIEW (FIXED)
# --------------------------------------------------------
logo = load_logo()

# Get background frame
if bg_mode == "Online Video":
    vid_path = download_asset(video_url, ".mp4") if 'download_asset' in globals() else None
    if vid_path:
        try:
            with VideoFileClip(vid_path) as clip:
                bg_frame = clip.get_frame(0.0)
                bg_frame = Image.fromarray(bg_frame).convert("RGB")
                # Resize to 1080x1920
                bg_frame = bg_frame.resize((WIDTH, HEIGHT), Image.LANCZOS)
                bg_array = np.array(bg_frame)
        except:
            bg_array = create_animated_bg("Minimal Zen", 0.0)
    else:
        bg_array = create_animated_bg("Minimal Zen", 0.0)
else:
    bg_array = create_animated_bg(template, 0.0)

# FIXED: Use the new text rendering system
preview_frame = render_frame(
    quote=quote,
    author=author,
    font_size=font_size,
    y_offset=y_offset,
    show_bg=show_bg,
    bg_array=bg_array,
    logo=logo
)

st.title("✨ WYSIWYG Quote Studio")
st.caption("Preview = First frame of your video. Text is now properly sized for mobile.")
st.image(preview_frame, channels="RGB", width=360, caption="✅ Exact frame 0 of your video")

# --------------------------------------------------------
# EXPORT (USE THE NEW RENDERING SYSTEM)
# --------------------------------------------------------
if export:
    if not quote.strip():
        st.error("Add a quote!")
    else:
        with st.spinner(".Rendering video (30-50 sec)..."):
            # Prepare background
            video_clip = None
            if bg_mode == "Online Video" and vid_path:
                try:
                    video_clip = VideoFileClip(vid_path)
                    if video_clip.duration < DURATION:
                        video_clip = video_clip.loop(duration=DURATION)
                    else:
                        video_clip = video_clip.subclip(0, DURATION)
                except:
                    video_clip = None
            
            # Render all frames
            frames = []
            total = FPS * DURATION
            for i in range(total):
                t = i / FPS
                if video_clip is not None:
                    try:
                        bg_frame = video_clip.get_frame(t)
                        bg_frame = Image.fromarray(bg_frame).convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
                        bg_array = np.array(bg_frame)
                    except:
                        bg_array = create_animated_bg("Minimal Zen", t)
                else:
                    bg_array = create_animated_bg(template, t)
                
                frame = render_frame(
                    quote=quote,
                    author=author,
                    font_size=font_size,
                    y_offset=y_offset,
                    show_bg=show_bg,
                    bg_array=bg_array,
                    logo=logo
                )
                frames.append(frame)
            
            # Save
            out = os.path.join(tempfile.gettempdir(), f"quote_{int(time.time())}.mp4")
            audio = download_asset("https://ik.imagekit.io/ericmwangi/ambient-piano-112970.mp3?updatedAt=1764101548797", ".mp3") if 'download_asset' in globals() else None
            from moviepy.editor import ImageSequenceClip, AudioFileClip
            clip = ImageSequenceClip(frames, fps=FPS)
            if audio:
                try:
                    aclip = AudioFileClip(audio).subclip(0, clip.duration)
                    clip = clip.set_audio(aclip)
                except:
                    pass
            clip.write_videofile(out, codec="libx264", audio_codec="aac", logger=None, threads=4)
            
            st.success("✅ Done!")
            with open(out, "rb") as f:
                st.download_button("⬇️ Download", f, "WYSIWYG_Quote.mp4", use_container_width=True)
            st.video(out)
            
            clip.close()
            if video_clip: video_clip.close()
            del frames
            gc.collect()