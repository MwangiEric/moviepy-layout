import streamlit as st
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import io, os, requests, random, math, time, textwrap
try:
    from moviepy.editor import VideoClip
    import numpy as np
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


# --- STREAMLIT CONFIG & CONSTANTS ---
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

W, H = 1080, 1920
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble." # Psalm 46:1
DEFAULT_REF = "Psalm 46:1"

# Helper function to convert hex string to RGB tuple
def hex_to_rgb(hex_color):
    """Converts #RRGGBB hex string to (R, G, B) tuple."""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Color Palettes and Template Definitions remain the same
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
TEXT_ANIMATIONS = ["None", "Typewriter Effect (Soon)", "Fade In (Soon)"] # New Selection
BG_ANIMATIONS = ["None", "Floating Particles (Soon)", "Waving Gradient (Soon)"] # New Selection

# --- BIBLE DATA (Simplified for Selection) ---
# A simplified dictionary for demonstration purposes
BIBLE_STRUCTURE = {
    "Psalm": {1: 6, 46: 11, 121: 8}, # Book: {Chapter: Num_Verses}
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
}
BOOK_NAMES = list(BIBLE_STRUCTURE.keys())

# --- FONT & CACHING FUNCTIONS ---

@st.cache_data(ttl=3600)
def download_font():
    path = "Poppins-Bold.ttf"
    # ... (Font download logic remains the same) ...
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
    """
    FIXED: Uses bible-api.com and implements a default fallback verse.
    """
    cleaned_ref = ref.replace(' ', '').replace(':', '')
    try:
        url = f"https://bible-api.com/{cleaned_ref}"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        # Check for error message in the response (common API failure check)
        if 'error' in data:
            st.error(f"API Error: {data['error']}")
            return DEFAULT_VERSE_TEXT
            
        verse_text = data.get("text")
        
        if verse_text:
            return verse_text.replace('\n', ' ').strip()
        else:
            return DEFAULT_VERSE_TEXT
        
    except Exception as e:
        st.error(f"Verse fetch failed ({e}). Using default verse.")
        return DEFAULT_VERSE_TEXT

# --- DRAWING HELPERS (Remains the same) ---

def get_text_size(font, text):
    if not text:
        return 0, 0
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
            if not current_line: lines.append(word)
            else: lines.append(" ".join(current_line))
            current_line = [word]
    if current_line: lines.append(" ".join(current_line))
    return lines

def draw_cross(draw, cx, cy, size=100, phase=0):
    pulse = 1 + 0.1 * math.sin(phase)
    lw = int(15 * pulse)
    fill_color = (255, 255, 255, 180) 
    draw.line([(cx, cy - size//2), (cx, cy + size//2)], fill=fill_color, width=lw)
    draw.line([(cx - size//2, cy), (cx + size//2, cy)], fill=fill_color, width=lw)


def generate_poster(template, palette_mode, ref, hook, animation_phase=None):
    """Generates a single poster frame."""
    
    verse_text = fetch_verse(ref)
    pal = random.choice(PALETTES[palette_mode])
    base = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    draw = ImageDraw.Draw(base)

    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2
    box_color = (0, 0, 0, 180) if palette_mode == "dark" else (255, 255, 255, 200)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=40, fill=box_color)

    max_text_width = box_w - 100
    hook_lines = wrap_text(hook, HOOK_FONT, max_text_width)
    verse_lines = wrap_text(f"“{verse_text}”", VERSE_FONT, max_text_width)
    ref_lines = wrap_text(ref, REF_FONT, max_text_width)

    hook_h_line = HOOK_FONT.getbbox("A")[3] + 10 
    verse_h_line = VERSE_FONT.getbbox("A")[3] + 8 
    ref_h_line = REF_FONT.getbbox("A")[3] + 6   
    
    total_height = (len(hook_lines) * hook_h_line) + (len(verse_lines) * verse_h_line) + (len(ref_lines) * ref_h_line) + 40
    current_y = box_y + (box_h - total_height) // 2

    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += HOOK_FONT.getbbox("A")[3] + 10

    verse_fill = (255, 255, 255, 255) 
    glow_fill = (100, 149, 237, 150)
    
    for line in verse_lines:
        w, h = get_text_size(VERSE_FONT, line)
        for offset in (1, 0, -1):
            draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
        draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
        current_y += VERSE_FONT.getbbox("A")[3] + 8

    for line in ref_lines:
        w, h = get_text_size(REF_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=REF_FONT, fill=hook_color)
        current_y += REF_FONT.getbbox("A")[3] + 6

    if template == "Golden Hour":
        phase = animation_phase if animation_phase is not None else time.time() % (2 * math.pi)
        draw_cross(draw, W//4, H//3, 120, phase * 1.5)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase * 1.5 + math.pi)

    return np.array(base.convert('RGB')) if animation_phase is not None else base, verse_text

# --- VIDEO GENERATOR (MoviePy remains the same) ---

def generate_mp4(template, palette_mode, ref, hook, duration=6, fps=30):
    if not MOVIEPY_AVAILABLE: return None
    
    def make_frame(t):
        return generate_poster(template, palette_mode, ref, hook, animation_phase=t)[0]

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

# --- Design Customization Column ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🎨 Design Settings")
    palette_mode = st.selectbox("Palette Mode", ["light", "dark"])
    template = st.selectbox("Base Template Style", TEMPLATES)
    
    st.markdown("---")
    st.subheader("✨ Animation Settings")
    # New Creative Selections
    bg_anim = st.selectbox("Background Animation", BG_ANIMATIONS, index=0)
    txt_anim = st.selectbox("Text Animation", TEXT_ANIMATIONS, index=0)
    
with col2:
    st.subheader("📖 Verse Selection")
    
    # --- New Interactive Verse Selection ---
    book = st.selectbox("Book", BOOK_NAMES, index=BOOK_NAMES.index("Psalm"))
    
    # Get available chapters for the selected book
    available_chapters = list(BIBLE_STRUCTURE.get(book, {}).keys())
    # Find the chapter index (default to 46 if available, or first chapter)
    default_chapter_index = available_chapters.index(46) if 46 in available_chapters else 0
    chapter = st.selectbox("Chapter", available_chapters, index=default_chapter_index)

    # Get available verses for the selected chapter
    max_verses = BIBLE_STRUCTURE.get(book, {}).get(chapter, 1) # Default to 1
    available_verses = list(range(1, max_verses + 1))
    # Find the verse index (default to 1 if available)
    default_verse_index = available_verses.index(1) if 1 in available_verses else 0
    verse_num = st.selectbox("Verse", available_verses, index=default_verse_index)
    
    # Construct the final reference string
    final_ref = f"{book} {chapter}:{verse_num}"
    st.markdown(f"**Selected Verse:** `{final_ref}`")

    st.markdown("---")
    hook = st.text_input("Engagement Hook", "Need strength today?")

st.markdown("---")

# --- Poster Generation and Display ---
# Use the constructed reference
poster_img, verse_text = generate_poster(template, palette_mode, final_ref, hook)
st.image(poster_img, caption=f"{template} • {palette_mode} Mode | Ref: {final_ref}", use_column_width=True)

st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")

# 1. Static PNG Download
buf = io.BytesIO()
poster_img.save(buf, format="PNG")
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{final_ref.replace(' ', '_')}.png", mime="image/png")

# 2. Animated Video Feature (MP4)
st.subheader("🎬 Animated Video (MP4)")

if not MOVIEPY_AVAILABLE:
    st.error("🚨 **MoviePy is required for video generation.**")
    st.code("pip install moviepy numpy")
    st.warning("Please install the dependencies and restart Streamlit.")
elif template == "Golden Hour":
    if st.button("✨ Generate Short MP4 Video (6s)"):
        with st.spinner("Rendering 6-second MP4 video..."):
            try:
                # Video duration is 6 seconds
                mp4_bytes = generate_mp4(template, palette_mode, final_ref, hook, duration=6)
                st.video(mp4_bytes, format="video/mp4")
                st.download_button("⬇️ Download Animated MP4", data=mp4_bytes, file_name=f"verse_animated_{final_ref.replace(' ', '_')}.mp4", mime="video/mp4")
            except Exception as e:
                st.error(f"Video generation failed. Error: {e}")
else:
    st.info("Select 'Golden Hour' template to enable MP4 video generation.")

st.markdown("---")
st.text_area("Copy Caption for Social Media", "Reflections", height=150)

st.info("📓 Journaling feature coming next!")
