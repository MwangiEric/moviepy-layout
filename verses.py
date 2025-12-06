import streamlit as st
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import io, os, requests, random, math, time, textwrap
from moviepy.editor import VideoClip 
import numpy as np
import pythonbible # NEW: Library for local verse fetching

# --- CONFIGURATION & CONSTANTS ---
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

W, H = 1080, 1920 
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble." 
DEFAULT_REF = "Psalm 46:1"

# Aspect Ratio Mapping
ASPECT_RATIOS = {
    "Reel / Story (9:16)": (1080, 1920),
    "Square Post (1:1)": (1080, 1080)
}

# Video Quality Mapping
VIDEO_QUALITIES = {
    "Draft (6s / 12 FPS)": (6, 12),
    "Standard (6s / 12 FPS)": (6, 12),
    "High Quality (6s / 24 FPS)": (6, 24)
}

# Helper function to convert hex string to RGB tuple
def hex_to_rgb(hex_color):
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# --- COLOR PALETTES (Named for Selection) ---
PALETTES = {
    "Faint Beige (Light)": {"bg": ["#faf9f6", "#e0e4d5"], "accent": "#c4891f", "text": "#183028"},
    "Warm Sunset (Light)": {"bg": ["#f4ebde", "#d6c7a9"], "accent": "#987919", "text": "#292929"},
    "Deep Slate (Dark)": {"bg": ["#0f1e1e", "#254141"], "accent": "#fcbf49", "text": "#f0f0f0"},
    "Urban Night (Dark)": {"bg": ["#202020", "#363636"], "accent": "#f7c59f", "text": "#f1fafb"}
}
PALETTE_NAMES = list(PALETTES.keys())

TEMPLATES = ["Modern Box Layout"] 
TEXT_ANIMATIONS = ["None", "Glow Pulse"]
# Updated BG Animations
BG_ANIMATIONS = ["None", "Cross Orbit (Geometric)", "Wave Flow (Abstract)", "Floating Circles (Abstract)"] 

# BIBLE DATA (Simplified for Selection)
# We need to map our names to pythonbible's format for fetching
BOOK_NAMES_MAP = {
    "Psalms": pythonbible.Book.PSALMS, 
    "John": pythonbible.Book.JOHN,
    "Romans": pythonbible.Book.ROMANS
}
BIBLE_STRUCTURE = {
    "Psalm": {1: 6, 46: 11, 121: 8}, 
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
}
BOOK_NAMES = list(BIBLE_STRUCTURE.keys())

# --- FONT & CACHING FUNCTIONS ---

@st.cache_data(ttl=3600)
def download_font():
    # ... (Font download logic remains the same) ...
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
def fetch_verse(book_name: str, chapter: int, verse_num: int) -> str:
    """
    NEW: Uses pythonbible for reliable local verse lookup.
    """
    try:
        book_enum = BOOK_NAMES_MAP[book_name]
        
        # pythonbible requires a list of verses
        verse_id = int(f"{book_enum.value}{chapter:03d}{verse_num:03d}")
verse_text = pythonbible.get_verse_text(verse_id)
        
        # Fetch the text for the verse ID (using King James Version, the default for pythonbible)
        verse_text = pythonbible.get_verse_text(verse_id[0])
        
        if verse_text:
            # We also append the Book/Chapter/Verse to the reference string later in the main function
            return verse_text.strip()
        else:
            return DEFAULT_VERSE_TEXT
        
    except Exception as e:
        # Fallback if any error occurs (e.g., Book/Chapter/Verse combo is invalid)
        return DEFAULT_VERSE_TEXT

# --- DRAWING HELPERS ---

def get_text_size(font, text):
    if not text: return 0, 0
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

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

def draw_cross(draw, cx, cy, size=100, phase=0):
    pulse = 1 + 0.1 * math.sin(phase)
    lw = int(15 * pulse)
    fill_color = (255, 255, 255, 180) 
    draw.line([(cx, cy - size//2), (cx, cy + size//2)], fill=fill_color, width=lw)
    draw.line([(cx - size//2, cy), (cx + size//2, cy)], fill=fill_color, width=lw)

def draw_waving_gradient(draw, pal, phase, w, h):
    """Draws a subtle animated 'Wave Flow' abstract background."""
    # Use a transparent accent color for a subtle wave effect
    accent_rgb = hex_to_rgb(pal["accent"])
    wave_color = accent_rgb + (40,) # Low opacity accent
    
    num_waves = 8
    amplitude = h / 20
    
    for y in range(h):
        # Calculate X offset based on sine wave, shifted by Y and time (phase)
        offset = amplitude * math.sin(y * num_waves * math.pi / h + phase)
        
        # Draw a horizontal line using the accent color, slightly shifted
        draw.line([(0 + offset, y), (w, y)], fill=wave_color, width=1)

def draw_floating_circles(draw, pal, phase, w, h):
    """Draws multiple animated 'Floating Circles' abstract background."""
    accent_rgb = hex_to_rgb(pal["accent"])
    circle_color = accent_rgb + (60,) # Low opacity accent
    
    num_circles = 8
    
    for i in range(num_circles):
        # Use i and phase to create unique and continuous movement
        size = 50 + (i * 10)
        
        # Circular motion based on time (phase) and index (i)
        angle = phase + (i * 0.5)
        
        # Center of motion for this circle
        cx_base = w * (i % 3 + 1) / 4
        cy_base = h * (i % 2 + 1) / 3

        # Current position (offset from base position)
        cx = int(cx_base + w/8 * math.cos(angle))
        cy = int(cy_base + h/8 * math.sin(angle))
        
        # Draw the circle (ellipse bounding box)
        draw.ellipse([cx - size, cy - size, cx + size, cy + size], outline=circle_color, width=3)


def draw_rotating_rectangle(base, draw, box_xy, angle, color_hex):
    """Draws a subtle rotating rectangle 30px outside the main text box."""
    x1, y1, x2, y2 = box_xy
    pad = 30
    rect_x1, rect_y1 = x1 - pad, y1 - pad
    rect_x2, rect_y2 = x2 + pad, y2 + pad
    
    # Calculate offset based on phase (t)
    offset_x = 5 * math.cos(angle)
    offset_y = 5 * math.sin(angle)
    
    draw.rectangle([
        rect_x1 + offset_x, rect_y1 + offset_y, 
        rect_x2 + offset_x, rect_y2 + offset_y
    ], outline=hex_to_rgb(color_hex) + (80,), width=8)


# --- CORE DRAWING FUNCTION ---

def generate_poster(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, animation_phase=None):
    """Generates a single poster frame applying the selected animation styles."""
    
    # Set dynamic W and H based on selection
    global W, H
    W, H = ASPECT_RATIOS[aspect_ratio_name]
    final_ref = f"{book} {chapter}:{verse_num}"
    
    # NEW: Fetch verse using native pythonbible function
    verse_text = fetch_verse(book, chapter, verse_num)
    
    pal = PALETTES[palette_name]
    base = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    draw = ImageDraw.Draw(base)

    # Calculate Coordinates
    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2
    box_xy = (box_x, box_y, box_x + box_w, box_y + box_h)
    phase = animation_phase if animation_phase is not None else time.time() % (2 * math.pi)

    # 1. Subtle Rotating Rectangle (Always On)
    draw_rotating_rectangle(base, draw, box_xy, phase * 0.2, pal["accent"])
    
    # 2. Background Animation Layer
    if bg_anim == "Cross Orbit (Geometric)":
        draw_cross(draw, W//4, H//3, 120, phase * 1.5)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase * 1.5 + math.pi)
    elif bg_anim == "Wave Flow (Abstract)":
        draw_waving_gradient(draw, pal, phase, W, H)
    elif bg_anim == "Floating Circles (Abstract)":
        draw_floating_circles(draw, pal, phase, W, H)

    # 3. Text Box and Static Text Layout
    box_color = (0, 0, 0, 180) if "Dark" in palette_name else (255, 255, 255, 200)
    draw.rounded_rectangle(box_xy, radius=40, fill=box_color)

    # Layout calculation (remains static)
    max_text_width = box_w - 100
    hook_lines = textwrap.wrap(hook, width=30) 
    verse_lines = textwrap.wrap(f"“{verse_text}”", width=25) 
    ref_lines = textwrap.wrap(final_ref, width=30) # Use the constructed reference

    line_h_hook = HOOK_FONT.getbbox("A")[3] + 10 
    line_h_verse = VERSE_FONT.getbbox("A")[3] + 8 
    line_h_ref = REF_FONT.getbbox("A")[3] + 6   
    
    total_height = (len(hook_lines) * line_h_hook) + (len(verse_lines) * line_h_verse) + (len(ref_lines) * line_h_ref) + 40
    current_y = box_y + (box_h - total_height) // 2

    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    verse_fill = (255, 255, 255, 255) 
    glow_fill = (100, 149, 237, 150)
    
    # 4. Text Animation Layer
    
    # Draw Hook Text
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += line_h_hook

    # Draw Glowing Verse Text (Affected by Text Animation)
    if txt_anim == "Glow Pulse":
        pulse_alpha = 150 + 50 * math.sin(phase * 4 if animation_phase is not None else time.time() * 4)
        animated_glow_fill = (100, 149, 237, int(max(100, pulse_alpha)))
        
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            for offset in (1, 0, -1):
                draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=animated_glow_fill)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse
    else: # Default/None Text Animation
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            for offset in (1, 0, -1):
                draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse

    # Draw Reference Text
    for line in ref_lines:
        w, h = get_text_size(REF_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=REF_FONT, fill=hook_color)
        current_y += line_h_ref

    return np.array(base.convert('RGB')) if animation_phase is not None else base, verse_text, final_ref

# --- VIDEO GENERATOR (MoviePy) ---

def generate_mp4(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, quality_name):
    
    duration, fps = VIDEO_QUALITIES[quality_name]
    
    def make_frame(t):
        return generate_poster(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, animation_phase=t)[0]

    clip = VideoClip(make_frame, duration=duration)
    temp_filename = f"temp_video_{time.time()}.mp4"
    
    clip.write_videofile(
        temp_filename, 
        fps=fps, 
        codec='libx264', 
        audio=False,     
        verbose=False, 
        logger=None
    )
    
    with open(temp_filename, "rb") as f:
        video_bytes = f.read()
        
    os.remove(temp_filename)
    return video_bytes

# --- STREAMLIT UI ---

st.title("✝️ Verse Studio Premium")

# --- UI CONTROLS ---

# Global Aspect Ratio Control
aspect_ratio_name = st.selectbox("🎥 Output Aspect Ratio", list(ASPECT_RATIOS.keys()))
W, H = ASPECT_RATIOS[aspect_ratio_name] # Update global W, H immediately

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🎨 Design & Animation")
    color_theme = st.selectbox("Color Theme", PALETTE_NAMES)
    
    st.markdown("---")
    
    # Animation Controls
    bg_anim = st.selectbox("Background Animation", BG_ANIMATIONS, index=1)
    txt_anim = st.selectbox("Text Animation", TEXT_ANIMATIONS, index=1)
    
    # Output Quality Control
    quality_name = st.selectbox("Video Quality", list(VIDEO_QUALITIES.keys()), index=1)
    
with col2:
    st.subheader("📖 Verse Selection")
    
    # --- Interactive Verse Selection ---
    book = st.selectbox("Book", BOOK_NAMES, index=BOOK_NAMES.index("Psalm"))
    
    available_chapters = list(BIBLE_STRUCTURE.get(book, {}).keys())
    default_chapter_index = available_chapters.index(46) if 46 in available_chapters else 0
    chapter = st.selectbox("Chapter", available_chapters, index=default_chapter_index)

    max_verses = BIBLE_STRUCTURE.get(book, {}).get(chapter, 1)
    available_verses = list(range(1, max_verses + 1))
    default_verse_index = available_verses.index(1) if 1 in available_verses else 0
    verse_num = st.selectbox("Verse", available_verses, index=default_verse_index)
    
    hook = st.text_input("Engagement Hook", "Need strength today?")

st.markdown("---")

# --- Poster Generation and Display ---

poster_img, verse_text, final_ref = generate_poster(aspect_ratio_name, color_theme, book, chapter, verse_num, hook, bg_anim, txt_anim)
st.image(poster_img, caption=f"{color_theme} | {aspect_ratio_name} | Ref: {final_ref}", use_column_width=True)

st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")

# 1. Static PNG Download
buf = io.BytesIO()
poster_img.save(buf, format="PNG")
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{final_ref.replace(' ', '_').replace(':', '')}.png", mime="image/png")

# 2. Animated Video Feature (MP4)
st.subheader("🎬 Animated Video")

# Video button uses the selected quality
if st.button(f"✨ Generate {quality_name} Video"):
    with st.spinner(f"Rendering 6-second MP4 video..."):
        try:
            mp4_bytes = generate_mp4(aspect_ratio_name, color_theme, book, chapter, verse_num, hook, bg_anim, txt_anim, quality_name)
            st.video(mp4_bytes, format="video/mp4")
            st.download_button("⬇️ Download Animated MP4", data=mp4_bytes, file_name=f"verse_animated_{final_ref.replace(' ', '_').replace(':', '')}.mp4", mime="video/mp4")
        except Exception as e:
            st.error(f"Video generation failed. Error: {e}")

st.markdown("---")
st.text_area("Copy Caption for Social Media", f"{hook} Read {final_ref} today. #dailyverse #faith", height=150)

st.info("📓 Dynamic hook and journaling features are next!")
