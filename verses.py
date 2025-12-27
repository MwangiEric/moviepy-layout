import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time
from moviepy.editor import VideoClip, CompositeVideoClip, AudioFileClip, VideoFileClip, vfx
import numpy as np

# =============================================================================
# STREAMLIT CONFIG
# =============================================================================
st.set_page_config(page_title="💎 Verse Studio Premium", page_icon="✝️", layout="wide")

# =============================================================================
# CONSTANTS
# =============================================================================
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble."
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
LOGO_SIZE = 120

# =============================================================================
# BIBLE SLUG FIX (CRITICAL)
# =============================================================================
BOOK_SLUGS = {
    "Psalm": "psalms",
    "Song of Solomon": "song-of-solomon",
    "1 Samuel": "1-samuel",
    "2 Samuel": "2-samuel",
}

# =============================================================================
# DESIGN CONFIG
# =============================================================================
DESIGN_CONFIG = {
    "palettes": {
        "Galilee Morning (Light)": {"bg": ["#faf9f6", "#e0e4d5"], "accent": "#c4891f", "text_primary": "#183028", "text_secondary": "#5a5a5a"},
        "Mount Zion Dusk (Light)": {"bg": ["#f4ebde", "#d6c7a9"], "accent": "#987919", "text_primary": "#292929", "text_secondary": "#555555"},
        "Deep Slate (Dark)": {"bg": ["#0f1e1e", "#254141"], "accent": "#fcbf49", "text_primary": "#f0f0f0", "text_secondary": "#cccccc"},
    },
    "aspect_ratios": {
        "Reel / Story (9:16)": (1080, 1920),
        "Square Post (1:1)": (1080, 1080),
    },
    "gradient_directions": ["Vertical", "Horizontal", "Diagonal"],
    "video_qualities": {
        "Draft (6s / 12 FPS)": (6, 12),
        "Standard (6s / 24 FPS)": (6, 24),
    }
}

# =============================================================================
# FONT LOADER (ONLINE GITHUB – CACHED)
# =============================================================================
@st.cache_data(ttl=86400)
def load_font(url, size):
    name = url.split("/")[-1]
    if not os.path.exists(name):
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(name, "wb") as f:
            f.write(r.content)
    return ImageFont.truetype(name, size)

HOOK_FONT = load_font(
    "https://github.com/google/fonts/raw/main/ofl/inter/Inter-SemiBold.ttf", 70
)
VERSE_FONT = load_font(
    "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf", 150
)
REF_FONT = load_font(
    "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf", 40
)

# =============================================================================
# HELPERS
# =============================================================================
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_text_size(font, text):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def smart_wrap_text(text, font, max_w):
    words, lines, cur = text.split(), [], []
    for w in words:
        test = " ".join(cur + [w])
        if get_text_size(font, test)[0] <= max_w:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

@st.cache_data
def create_gradient(w, h, c1, c2, direction):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    c1, c2 = hex_to_rgb(c1), hex_to_rgb(c2)

    for x in range(w):
        for y in range(h):
            if direction == "Vertical":
                r = y / h
            elif direction == "Horizontal":
                r = x / w
            else:
                r = (x + y) / (w + h)
            col = tuple(int((1-r)*c1[i] + r*c2[i]) for i in range(3))
            d.point((x, y), fill=col)
    return img

# =============================================================================
# BIBLE FETCH (FIXED)
# =============================================================================
@st.cache_data(ttl=3600)
def fetch_verse(book, chapter, verse):
    slug = BOOK_SLUGS.get(book, book.lower().replace(" ", "-"))
    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv/books/{slug}/chapters/{chapter}/verses/{verse}.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json().get("text", "").strip() or DEFAULT_VERSE_TEXT
    except:
        return DEFAULT_VERSE_TEXT

# =============================================================================
# LOGO LOADER (SHARP)
# =============================================================================
@st.cache_data(ttl=3600)
def load_logo():
    img = Image.open(io.BytesIO(requests.get(LOGO_URL).content)).convert("RGBA")
    img = img.filter(ImageFilter.SHARPEN)
    return img.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)

# =============================================================================
# IMAGE GENERATION
# =============================================================================
def generate_image(aspect, palette_name, book, chapter, verse, hook, gradient_dir, logo_pos):
    W, H = DESIGN_CONFIG["aspect_ratios"][aspect]
    pal = DESIGN_CONFIG["palettes"][palette_name]

    bg = create_gradient(W, H, pal["bg"][0], pal["bg"][1], gradient_dir)
    draw = ImageDraw.Draw(bg)

    verse_text = fetch_verse(book, chapter, verse)
    ref = f"{book} {chapter}:{verse}"

    max_w = W - MARGIN * 2
    y = int(H * 0.28)

    for line in smart_wrap_text(hook, HOOK_FONT, max_w):
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, y), line, font=HOOK_FONT, fill=hex_to_rgb(pal["accent"]))
        y += h + 24

    y += 40
    for line in smart_wrap_text(verse_text, VERSE_FONT, max_w):
        w, h = get_text_size(VERSE_FONT, line)
        draw.text(((W - w)//2, y), line, font=VERSE_FONT, fill=hex_to_rgb(pal["text_primary"]))
        y += h + 30

    w, h = get_text_size(REF_FONT, ref)
    draw.text(((W - w)//2, y + 30), ref, font=REF_FONT, fill=hex_to_rgb(pal["text_secondary"]))

    if logo_pos != "Hidden":
        logo = load_logo()
        x, y = W - LOGO_SIZE - 40, H - LOGO_SIZE - 40
        mask = Image.new("L", (LOGO_SIZE, LOGO_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, LOGO_SIZE, LOGO_SIZE), fill=255)
        bg.paste(logo, (x, y), mask)

    return bg

# =============================================================================
# UI (UNCHANGED BEHAVIOR)
# =============================================================================
st.title("💎 Verse Studio Premium")

aspect = st.selectbox("Aspect Ratio", DESIGN_CONFIG["aspect_ratios"])
palette = st.selectbox("Color Theme", DESIGN_CONFIG["palettes"])
gradient = st.selectbox("Gradient Direction", DESIGN_CONFIG["gradient_directions"])
book = st.selectbox("Book", list(BOOK_SLUGS.keys()) + ["Proverbs", "John"])
chapter = st.number_input("Chapter", 1, 150, 46)
verse = st.number_input("Verse", 1, 176, 1)
hook = st.text_input("Hook", "Need strength today?")
logo = st.selectbox("Logo", ["Bottom Right", "Hidden"])

img = generate_image(aspect, palette, book, chapter, verse, hook, gradient, logo)
st.image(img, use_column_width=True)

buf = io.BytesIO()
img.save(buf, "PNG")
st.download_button("⬇️ Download PNG", buf.getvalue(), "verse.png")