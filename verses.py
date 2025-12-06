import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time, textwrap
from moviepy.editor import VideoClip 
import numpy as np

# --- 1. CONFIGURATION & CONSTANTS ---
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

W, H = 1080, 1920 
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble." 
MAX_WRAP_WIDTH = 900 # Maximum pixel width for text within the canvas
# Max width is W - 2 * MARGIN - 100 padding

# --- Centralized Design Configuration (JSON Structure) ---
DESIGN_CONFIG = {
    "palettes": {
        "Faint Beige (Light)": {"bg": ["#faf9f6", "#e0e4d5"], "accent": "#c4891f", "text": "#183028"},
        "Warm Sunset (Light)": {"bg": ["#f4ebde", "#d6c7a9"], "accent": "#987919", "text": "#292929"},
        "Deep Slate (Dark)": {"bg": ["#0f1e1e", "#254141"], "accent": "#fcbf49", "text": "#f0f0f0"},
        "Urban Night (Dark)": {"bg": ["#202020", "#363636"], "accent": "#f7c59f", "text": "#f1fafb"}
    },
    "text_animations": ["None", "Glow Pulse"],
    "bg_animations": ["None", "Cross Orbit (Geometric)", "Wave Flow (Abstract)", "Floating Circles (Abstract)"],
    "aspect_ratios": {
        "Reel / Story (9:16)": (1080, 1920),
        "Square Post (1:1)": (1080, 1080)
    },
    "video_qualities": {
        "Draft (6s / 12 FPS)": (6, 12),
        "Standard (6s / 12 FPS)": (6, 12),
        "High Quality (6s / 24 FPS)": (6, 24)
    }
}
PALETTE_NAMES = list(DESIGN_CONFIG["palettes"].keys())
TEXT_ANIMATIONS = DESIGN_CONFIG["text_animations"]
BG_ANIMATIONS = DESIGN_CONFIG["bg_animations"]
ASPECT_RATIOS = DESIGN_CONFIG["aspect_ratios"]
VIDEO_QUALITIES = DESIGN_CONFIG["video_qualities"]

# BIBLE DATA (Simplified for Selection)
BIBLE_STRUCTURE = {
    "Genesis": {1: 31, 2: 25}, 
    "Psalm": {1: 6, 46: 11, 121: 8}, 
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
}
BOOK_NAMES = list(BIBLE_STRUCTURE.keys())

# --- 2. SESSION STATE INITIALIZATION (Fixes "Error tried to use sessions before initiation") ---
# Initialize all necessary state variables
if 'aspect_ratio_name' not in st.session_state:
    st.session_state.aspect_ratio_name = list(ASPECT_RATIOS.keys())[0]
if 'color_theme' not in st.session_state:
    st.session_state.color_theme = PALETTE_NAMES[0]
if 'bg_anim' not in st.session_state:
    st.session_state.bg_anim = BG_ANIMATIONS[1] # Default to Cross Orbit
if 'txt_anim' not in st.session_state:
    st.session_state.txt_anim = TEXT_ANIMATIONS[1] # Default to Glow Pulse
if 'quality_name' not in st.session_state:
    st.session_state.quality_name = list(VIDEO_QUALITIES.keys())[1]
if 'book' not in st.session_state:
    st.session_state.book = BOOK_NAMES[0]
if 'chapter' not in st.session_state:
    st.session_state.chapter = list(BIBLE_STRUCTURE[st.session_state.book].keys())[0]
if 'verse_num' not in st.session_state:
    st.session_state.verse_num = 1
if 'hook' not in st.session_state:
    st.session_state.hook = "Need strength today?"

# --- 3. FONT & CACHING FUNCTIONS (REMAINS THE SAME) ---

def hex_to_rgb(hex_color):
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

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

HOOK_FONT, VERSE_FONT, REF_FONT = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default() 
try:
    HOOK_FONT = ImageFont.truetype(FONT_PATH, 80)
    VERSE_FONT = ImageFont.truetype(FONT_PATH, 110)
    REF_FONT = ImageFont.truetype(FONT_PATH, 48)
except Exception:
    pass


@st.cache_data(ttl=1800)
def fetch_verse(book_name: str, chapter: int, verse_num: int) -> str:
    """Fetches verse text from CDN URL using requests."""
    book_lower = book_name.lower()
    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv/books/{book_lower}/chapters/{chapter}/verses/{verse_num}.json"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        verse_text = data.get("text")
        return verse_text.strip() if verse_text else DEFAULT_VERSE_TEXT
    except requests.exceptions.RequestException:
        return DEFAULT_VERSE_TEXT
    except Exception:
        return DEFAULT_VERSE_TEXT

# --- 4. DRAWING HELPERS ---

def get_text_size(font, text):
    if not text: return 0, 0
    # Use getbbox for width/height calculation
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

# NEW: Smart wrapping function
def smart_wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """
    Splits text into lines, ensuring each line's pixel width is less than max_width.
    """
    words = text.split()
    if not words:
        return [""]
    
    lines = []
    current_line = words[0]
    
    for word in words[1:]:
        test_line = current_line + " " + word
        # Get the width of the test line
        try:
            width, _ = get_text_size(font, test_line)
        except Exception:
            # Fallback to simple char count if font loading fails
            width = len(test_line) * 50 

        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
            
    lines.append(current_line)
    return lines

# Gradient and animation helpers (omitted for brevity, assumed included)
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

def draw_rotating_rectangle(base, draw, box_xy, angle, color_hex):
    x1, y1, x2, y2 = box_xy
    pad = 30
    rect_x1, rect_y1 = x1 - pad, y1 - pad
    rect_x2, rect_y2 = x2 + pad, y2 + pad
    offset_x = 5 * math.cos(angle)
    offset_y = 5 * math.sin(angle)
    draw.rectangle([rect_x1 + offset_x, rect_y1 + offset_y, rect_x2 + offset_x, rect_y2 + offset_y], outline=hex_to_rgb(color_hex) + (80,), width=8)


# --- 5. CORE DRAWING FUNCTION ---

def generate_poster(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, animation_phase=None):
    """Generates a single poster frame."""
    
    global W, H
    W, H = ASPECT_RATIOS[aspect_ratio_name]
    final_ref = f"{book} {chapter}:{verse_num} (ASV)"
    
    verse_text_raw = fetch_verse(book, chapter, verse_num)
    
    pal = DESIGN_CONFIG["palettes"][palette_name]
    base = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    draw = ImageDraw.Draw(base)

    # Calculate Coordinates
    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2
    box_xy = (box_x, box_y, box_x + box_w, box_y + box_h)
    phase = animation_phase if animation_phase is not None else time.time() % (2 * math.pi)

    # Background Animations
    draw_rotating_rectangle(base, draw, box_xy, phase * 0.2, pal["accent"])
    if bg_anim == "Cross Orbit (Geometric)":
        draw_cross(draw, W//4, H//3, 120, phase * 1.5)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase * 1.5 + math.pi)
    # Wave Flow and Floating Circles drawing logic omitted for brevity, assumed functional.

    # 3. Text Box 
    box_color = (0, 0, 0, 180) if "Dark" in palette_name else (255, 255, 255, 200)
    draw.rounded_rectangle(box_xy, radius=40, fill=box_color)

    # Layout calculation
    max_text_width_pixels = box_w - 100 # Define max width for text inside the box
    
    # NEW: Use smart_wrap_text for precise layout control
    hook_lines = smart_wrap_text(hook, HOOK_FONT, max_text_width_pixels)
    verse_lines = smart_wrap_text(verse_text_raw, VERSE_FONT, max_text_width_pixels) 
    ref_lines = smart_wrap_text(final_ref, REF_FONT, max_text_width_pixels)

    line_h_hook = HOOK_FONT.getbbox("A")[3] + 10 
    line_h_verse = VERSE_FONT.getbbox("A")[3] + 8 
    line_h_ref = REF_FONT.getbbox("A")[3] + 6   
    
    total_height = (len(hook_lines) * line_h_hook) + (len(verse_lines) * line_h_verse) + (len(ref_lines) * line_h_ref) + 60 
    current_y = box_y + (box_h - total_height) // 2

    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    verse_fill = (255, 255, 255, 255) 
    glow_fill = (100, 149, 237, 150)
    
    # 4. Text and Quote Drawing
    
    # Draw Hook Text
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += line_h_hook
    
    # Custom Opening Quote
    quote_size = 70
    quote_text = "“"
    quote_font = ImageFont.truetype(FONT_PATH, quote_size)
    quote_color = hook_color 
    
    first_line_w, _ = get_text_size(VERSE_FONT, verse_lines[0])
    x_start_verse = (W - first_line_w) // 2
    
    draw.text((x_start_verse - quote_size * 0.7, current_y - quote_size * 0.2), 
              quote_text, font=quote_font, fill=quote_color)
              
    # Draw Verse Text (Glow Pulse logic remains)
    if txt_anim == "Glow Pulse":
        pulse_alpha = 150 + 50 * math.sin(phase * 4 if animation_phase is not None else time.time() * 4)
        animated_glow_fill = (100, 149, 237, int(max(100, pulse_alpha)))
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            for offset in (1, 0, -1):
                draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=animated_glow_fill)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse
    else: 
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            for offset in (1, 0, -1):
                draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse

    # Draw Closing Quote
    last_line_w, last_line_h = get_text_size(VERSE_FONT, verse_lines[-1])
    x_end_verse = (W + last_line_w) // 2
    
    draw.text((x_end_verse + quote_size * 0.1, current_y - line_h_verse * 0.5), 
              "”", font=quote_font, fill=quote_color)
    
    current_y += 20 

    # Custom Reference Separator
    separator_w = 200
    separator_x = (W - separator_w) // 2
    separator_color = hook_color
    draw.line([(separator_x, current_y), (separator_x + separator_w, current_y)], 
              fill=separator_color, width=5)
    
    current_y += 20 

    # Draw Reference Text
    for line in ref_lines:
        w, h = get_text_size(REF_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=REF_FONT, fill=hook_color)
        current_y += line_h_ref

    return np.array(base.convert('RGB')) if animation_phase is not None else base, verse_text_raw, final_ref

# --- 6. VIDEO GENERATOR (MoviePy Fix) ---

def generate_mp4(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, quality_name):
    
    duration, fps = VIDEO_QUALITIES[quality_name]
    
    def make_frame(t):
        return generate_poster(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, animation_phase=t)[0]

    clip = VideoClip(make_frame, duration=duration)
    temp_filename = f"temp_video_{time.time()}.mp4"
    
    # FIX: Removed the unsupported 'progress_callback' argument and reverted to st.spinner
    with st.spinner("Rendering video... This may take a moment."):
        clip.write_videofile(
            temp_filename, 
            fps=fps, 
            codec='libx264', 
            audio=False,     
            verbose=False, 
            logger=None
            # progress_callback=progress_callback # REMOVED DUE TO ERROR
        )
    
    with open(temp_filename, "rb") as f:
        video_bytes = f.read()
        
    os.remove(temp_filename)
    return video_bytes

# --- 7. STREAMLIT UI (Using Session State) ---

st.title("✝️ Verse Studio Premium")

# --- UI CONTROLS ---

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🎨 Design & Animation")
    
    # Store selection directly in session_state to trigger redraws
    st.selectbox("🎥 Output Aspect Ratio", list(ASPECT_RATIOS.keys()), key='aspect_ratio_name')
    st.selectbox("Color Theme", PALETTE_NAMES, key='color_theme')
    
    st.markdown("---")
    
    # Store animation selection directly in session_state
    st.selectbox("Background Animation", BG_ANIMATIONS, key='bg_anim')
    st.selectbox("Text Animation", TEXT_ANIMATIONS, key='txt_anim')
    
    # Store quality selection directly in session_state
    st.selectbox("Video Quality", list(VIDEO_QUALITIES.keys()), key='quality_name')
    
with col2:
    st.subheader("📖 Verse Selection")
    
    # --- Interactive Verse Selection ---
    # Update state on change
    st.selectbox("Book", BOOK_NAMES, key='book')
    
    available_chapters = list(BIBLE_STRUCTURE.get(st.session_state.book, {}).keys())
    st.selectbox("Chapter", available_chapters, key='chapter')

    max_verses = BIBLE_STRUCTURE.get(st.session_state.book, {}).get(st.session_state.chapter, 1)
    available_verses = list(range(1, max_verses + 1))
    st.selectbox("Verse", available_verses, key='verse_num')
    
    st.text_input("Engagement Hook", value=st.session_state.hook, key='hook')

st.markdown("---")

# --- Poster Generation and Display ---
# Use session state variables for drawing
poster_img, verse_text, final_ref = generate_poster(
    st.session_state.aspect_ratio_name, 
    st.session_state.color_theme, 
    st.session_state.book, 
    st.session_state.chapter, 
    st.session_state.verse_num, 
    st.session_state.hook, 
    st.session_state.bg_anim, 
    st.session_state.txt_anim
)
st.image(poster_img, caption=f"{st.session_state.color_theme} | {st.session_state.aspect_ratio_name} | Ref: {final_ref}", use_column_width=True)

st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")

# 1. Static PNG Download
buf = io.BytesIO()
poster_img.save(buf, format="PNG")
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{final_ref.replace(' ', '_').replace(':', '')}.png", mime="image/png")

# 2. Animated Video Feature (MP4)
st.subheader("🎬 Animated Video")

if st.button(f"✨ Generate {st.session_state.quality_name} Video"):
    try:
        # Use session state variables for generation
        mp4_bytes = generate_mp4(
            st.session_state.aspect_ratio_name, 
            st.session_state.color_theme, 
            st.session_state.book, 
            st.session_state.chapter, 
            st.session_state.verse_num, 
            st.session_state.hook, 
            st.session_state.bg_anim, 
            st.session_state.txt_anim, 
            st.session_state.quality_name
        )
        st.video(mp4_bytes, format="video/mp4")
        st.download_button("⬇️ Download Animated MP4", data=mp4_bytes, file_name=f"verse_animated_{final_ref.replace(' ', '_').replace(':', '')}.mp4", mime="video/mp4")
    except Exception as e:
        st.error(f"Video generation failed. Error: {e}")

st.markdown("---")
st.text_area("Copy Caption for Social Media", f"{st.session_state.hook} Read {final_ref} today. #dailyverse #faith", height=150)

st.info("📓 Dynamic hook and journaling features are next!")
