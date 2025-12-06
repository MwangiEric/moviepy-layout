import streamlit as st
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import io, os, requests, random, math, time, textwrap
try:
    from moviepy.editor import VideoClip
    import numpy as np
    MOVIEPY_AVAILABLE = True
except ImportError:
    # Set a flag if moviepy is not installed
    MOVIEPY_AVAILABLE = False


# Streamlit page config (called once)
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

# --- Configuration Constants ---
W, H = 1080, 1920  # Canvas size (vertical reels/stories)
MARGIN = 100

# Helper function to convert hex string to RGB tuple
def hex_to_rgb(hex_color):
    """Converts #RRGGBB hex string to (R, G, B) tuple."""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# --- Constants and Color Palettes (RGB only) ---
PALETTES = {
    "light": [
        {"bg": ["#faf9f6", "#e0e4d5"], "accent": "#c4891f", "text": "#183028"},
        {"bg": ["#f4ebde", "#d6c7a9"], "accent": "#987919", "text": "#292929"}
    ],
    "dark": [
        {"bg": ["#0f1e1e", "#254141"], "accent": "#fcbf49", "text": "#f0f0f0"},
        {"bg": ["#202020", "#363636"], "accent": "#f7c59f", "text": "#f1fafb"}
    ]
}
TEMPLATES = ["Minimal Elegance", "Golden Hour"]

# --- Font and Verse Functions ---

@st.cache_data(ttl=3600)
def download_font():
    path = "Poppins-Bold.ttf"
    if not os.path.exists(path):
        url = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
    return path

FONT_PATH = download_font()

def load_fonts():
    try:
        return (
            ImageFont.truetype(FONT_PATH, 80),
            ImageFont.truetype(FONT_PATH, 110),
            ImageFont.truetype(FONT_PATH, 48),
        )
    except Exception:
        return (ImageFont.load_default(),)*3

HOOK_FONT, VERSE_FONT, REF_FONT = load_fonts()

@st.cache_data(ttl=1800)
def fetch_verse(ref: str) -> str:
    """Uses bible-api.com for reliability."""
    try:
        url = f"https://bible-api.com/{ref.replace(' ', '').replace(':', '')}"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        verse_text = data.get("text", "Verse unavailable")
        return verse_text.replace('\n', ' ').strip()
        
    except Exception:
        return "Verse unavailable. Please check the reference format."

def get_text_size(font, text):
    """Helper to get text width and height using the recommended getbbox()."""
    if not text:
        return 0, 0
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

# --- Drawing Helpers ---

def create_gradient(w, h, c1_hex, c2_hex):
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    c1_rgb = hex_to_rgb(c1_hex)
    c2_rgb = hex_to_rgb(c2_hex)
    
    for x in range(w):
        ratio = x / w
        r = int((1-ratio)*c1_rgb[0] + ratio*c2_rgb[0])
        g = int((1-ratio)*c1_rgb[1] + ratio*c2_rgb[1])
        b = int((1-ratio)*c1_rgb[2] + ratio*c2_rgb[2])
        draw.line([(x, 0), (x, h)], fill=(r, g, b))
    
    return img.convert("RGBA")


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        w, _ = get_text_size(font, test_line)
        
        if w < max_width:
            current_line.append(word)
        else:
            if not current_line:
                lines.append(word)
            else:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines


def draw_cross(draw, cx, cy, size=100, phase=0):
    pulse = 1 + 0.1 * math.sin(phase)
    lw = int(15 * pulse)
    fill_color = (255, 255, 255, 180) 
    draw.line([(cx, cy - size//2), (cx, cy + size//2)], fill=fill_color, width=lw)
    draw.line([(cx - size//2, cy), (cx + size//2, cy)], fill=fill_color, width=lw)


def generate_poster(template, palette_mode, ref, hook, animation_phase=None):
    """Generates a single poster frame."""
    
    # Use st.cache_data for fetching the verse text
    verse_text = fetch_verse(ref)
        
    pal = random.choice(PALETTES[palette_mode])
    
    base = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    draw = ImageDraw.Draw(base)

    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2

    # Draw Text Background Box (Black/White with transparency)
    box_color = (0, 0, 0, 180) if palette_mode == "dark" else (255, 255, 255, 200)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=40, fill=box_color)

    # Text wrapping
    max_text_width = box_w - 100
    hook_lines = wrap_text(hook, HOOK_FONT, max_text_width)
    verse_lines = wrap_text(f"“{verse_text}”", VERSE_FONT, max_text_width)
    ref_lines = wrap_text(ref, REF_FONT, max_text_width)

    # Calculate total height (using baseline height for consistent vertical spacing)
    hook_h_line = HOOK_FONT.getbbox("A")[3] + 10 
    verse_h_line = VERSE_FONT.getbbox("A")[3] + 8 
    ref_h_line = REF_FONT.getbbox("A")[3] + 6   
    
    total_height = (len(hook_lines) * hook_h_line) + \
                   (len(verse_lines) * verse_h_line) + \
                   (len(ref_lines) * ref_h_line) + 40

    current_y = box_y + (box_h - total_height) // 2

    # Draw hook text 
    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += HOOK_FONT.getbbox("A")[3] + 10

    # Draw glowing verse text
    verse_fill = (255, 255, 255, 255) 
    glow_fill = (100, 149, 237, 150)
    
    for line in verse_lines:
        w, h = get_text_size(VERSE_FONT, line)
        for offset in (1, 0, -1):
            draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
        draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
        current_y += VERSE_FONT.getbbox("A")[3] + 8

    # Draw reference text
    for line in ref_lines:
        w, h = get_text_size(REF_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=REF_FONT, fill=hook_color)
        current_y += REF_FONT.getbbox("A")[3] + 6

    # Animated crosses for golden template
    if template == "Golden Hour":
        # Use animation_phase if provided, otherwise use current time (static preview)
        phase = animation_phase if animation_phase is not None else time.time() % (2 * math.pi)
        draw_cross(draw, W//4, H//3, 120, phase * 1.5)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase * 1.5 + math.pi)

    # Convert to RGB array for MoviePy compatibility if animating
    return np.array(base.convert('RGB')) if animation_phase is not None else base, verse_text

# --- Video Generator (MoviePy) ---

def generate_mp4(template, palette_mode, ref, hook, duration=6, fps=30):
    """
    Generates an MP4 video using MoviePy.
    Duration is set to 6 seconds for resource efficiency.
    """
    
    def make_frame(t):
        """Called by MoviePy to generate each frame based on time (t)."""
        # t is the current time in seconds, which we use as the animation phase
        # Note: generate_poster returns a NumPy array when animation_phase is set
        return generate_poster(template, palette_mode, ref, hook, animation_phase=t)[0]

    # Create the MoviePy clip
    clip = VideoClip(make_frame, duration=duration)
    
    # Write the video to a temporary file
    temp_filename = f"temp_video_{time.time()}.mp4"
    
    # Use st.cache_data to remember the last generated video if the inputs haven't changed
    # (Though we skip this here due to potential memory/cleanup issues in Streamlit deployment)
    
    # Writing the file: use a small, efficient codec like libx264
    clip.write_videofile(
        temp_filename, 
        fps=fps, 
        codec='libx264', # Common video codec
        audio=False,     # No audio stream
        verbose=False, 
        logger=None
    )
    
    # Read the file bytes
    with open(temp_filename, "rb") as f:
        video_bytes = f.read()
        
    # Clean up the temporary file
    os.remove(temp_filename)
    
    return video_bytes

# --- UI controls ---
st.title("✝️ Verse Studio Premium")
palette_mode = st.selectbox("Palette Mode", ["light", "dark"])
template = st.selectbox("Template Style", TEMPLATES)
ref = st.text_input("Bible Verse Reference", "Psalm 46:1")
hook = st.text_input("Engagement Hook", "Need strength today?")

# Generate the static poster preview
poster_img, verse_text = generate_poster(template, palette_mode, ref, hook)
st.image(poster_img, caption=f"{template} • {palette_mode} Mode", use_column_width=True)

st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")

# 1. Static PNG Download
buf = io.BytesIO()
poster_img.save(buf, format="PNG")
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{ref.replace(' ', '_')}.png", mime="image/png")

# 2. Animated Video Feature (MP4)
st.subheader("🎬 Animated Video (MP4)")

if not MOVIEPY_AVAILABLE:
    st.error("🚨 **MoviePy is required for video generation.**")
    st.code("pip install moviepy numpy")
    st.warning("Please install the dependencies and restart Streamlit.")
elif template == "Golden Hour":
    
    if st.button("✨ Generate Short MP4 Video (6s)"):
        with st.spinner("Rendering 6-second MP4 video with MoviePy (This can take 30-90 seconds)..."):
            try:
                # Video duration is now 6 seconds
                mp4_bytes = generate_mp4(template, palette_mode, ref, hook, duration=6)
                
                st.video(mp4_bytes, format="video/mp4")
                st.download_button("⬇️ Download Animated MP4", data=mp4_bytes, file_name=f"verse_animated_{ref.replace(' ', '_')}.mp4", mime="video/mp4")
            except Exception as e:
                st.error(f"Video generation failed. Ensure FFmpeg is correctly installed. Error: {e}")
else:
    st.info("Select 'Golden Hour' template to enable MP4 video generation.")

st.markdown("---")
st.text_area("Copy Caption for Social Media", "Reflections", height=150)

st.info("📓 Journaling feature coming next!")
