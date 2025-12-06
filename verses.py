import streamlit as st
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import io, os, requests, random, math, time, textwrap

# --- Configuration Constants ---
W, H = 1080, 1920  # Canvas size (vertical reels/stories)
MARGIN = 100

# Helper function to convert hex string to RGB tuple
def hex_to_rgb(hex_color):
    """Converts #RRGGBB hex string to (R, G, B) tuple."""
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

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

# --- Streamlit Setup ---
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

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
    except:
        return (ImageFont.load_default(),)*3

HOOK_FONT, VERSE_FONT, REF_FONT = load_fonts()

@st.cache_data(ttl=1800)
def fetch_verse(ref: str) -> str:
    try:
        r = requests.get("https://getbible.net/json", params={"passage": ref.replace(" ", "")}, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data[0].get("text", "Verse unavailable") if data else "Verse unavailable"
    except:
        return "Verse unavailable"

# --- Drawing Helpers ---

def get_text_size(font, text):
    """
    Helper to get text width and height using the non-deprecated getbbox().
    Returns (width, height)
    """
    # getbbox returns (left, top, right, bottom)
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
    
    # Convert to RGBA for drawing layers on top later
    return img.convert("RGBA")


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    
    while words:
        # Check current line + next word
        test_line = " ".join(current_line + [words[0]])
        w, _ = get_text_size(font, test_line)
        
        if w < max_width:
            current_line.append(words.pop(0))
        else:
            # Current line is full. If it's empty, we have a word that's too wide.
            if not current_line:
                # Force wrap the single word (or use textwrap.wrap for safety)
                lines.append(words.pop(0))
            else:
                lines.append(" ".join(current_line))
                current_line = []
    
    if current_line:
        lines.append(" ".join(current_line))
        
    return lines


def draw_cross(draw, cx, cy, size=100, phase=0):
    pulse = 1 + 0.1 * math.sin(phase)
    lw = int(15 * pulse)
    # White cross with 180 alpha (semi-transparent)
    fill_color = (255, 255, 255, 180) 
    draw.line([(cx, cy - size//2), (cx, cy + size//2)], fill=fill_color, width=lw)
    draw.line([(cx - size//2, cy), (cx + size//2, cy)], fill=fill_color, width=lw)


def generate_poster(template, palette_mode, ref, hook):
    verse_text = fetch_verse(ref)
    pal = random.choice(PALETTES[palette_mode])
    
    # Base is RGB, converted to RGBA
    base = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    draw = ImageDraw.Draw(base)

    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2

    # Draw Text Background Box (Black/White with transparency)
    box_color = (0, 0, 0, 180) if palette_mode == "dark" else (255, 255, 255, 200)
    draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=40, fill=box_color)

    # Text wrapping inside box with margin
    max_text_width = box_w - 100
    hook_lines = wrap_text(hook, HOOK_FONT, max_text_width)
    verse_lines = wrap_text(f"“{verse_text}”", VERSE_FONT, max_text_width)
    ref_lines = wrap_text(ref, REF_FONT, max_text_width)

    # Calculate total height (Using a placeholder height for spacing calculations)
    hook_h_line = HOOK_FONT.getbbox("A")[3] + 10 # height + 10 margin
    verse_h_line = VERSE_FONT.getbbox("A")[3] + 8 # height + 8 margin
    ref_h_line = REF_FONT.getbbox("A")[3] + 6   # height + 6 margin
    
    total_height = (len(hook_lines) * hook_h_line) + \
                   (len(verse_lines) * verse_h_line) + \
                   (len(ref_lines) * ref_h_line) + 40 # Padding offset

    current_y = box_y + (box_h - total_height) // 2

    # Draw hook text (Accent color, no transparency needed)
    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += HOOK_FONT.getbbox("A")[3] + 10 # Use baseline height for step

    # Draw glowing verse text
    verse_fill = (255, 255, 255, 255) # White text
    glow_fill = (100, 149, 237, 150)  # Light Blue/Cornflower Blue for glow with 150 alpha
    
    for line in verse_lines:
        w, h = get_text_size(VERSE_FONT, line)
        # Simple glow effect: draw transparent glow first
        for offset in (1, 0, -1):
            draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
        # Draw opaque text on top
        draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
        current_y += VERSE_FONT.getbbox("A")[3] + 8 # Use baseline height for step

    # Draw reference text
    for line in ref_lines:
        w, h = get_text_size(REF_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=REF_FONT, fill=hook_color)
        current_y += REF_FONT.getbbox("A")[3] + 6 # Use baseline height for step

    # Animated crosses for golden template
    if template == "Golden Hour":
        phase = time.time() % (2 * math.pi)
        draw_cross(draw, W//4, H//3, 120, phase)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase + math.pi)

    return base, verse_text

# --- UI controls ---
st.title("✝️ Verse Studio Premium")
palette_mode = st.selectbox("Palette Mode", ["light", "dark"])
template = st.selectbox("Template Style", TEMPLATES)
ref = st.text_input("Bible Verse Reference", "Psalm 46:1")
hook = st.text_input("Engagement Hook", "Need strength today?")

poster_img, verse_text = generate_poster(template, palette_mode, ref, hook)
st.image(poster_img, caption=f"{template} • {palette_mode} Mode", use_column_width=True)

# Download button
buf = io.BytesIO()
poster_img.save(buf, format="PNG")
st.download_button("⬇️ Download Poster PNG", data=buf.getvalue(), file_name=f"verse_{ref.replace(' ', '_')}.png", mime="image/png")

st.text_area("Copy Caption for Social Media", "Reflections", height=150)

st.info("🎥 Video output with animations coming soon! (The Golden Hour crosses animate on every refresh.)")
