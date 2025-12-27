import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time
from moviepy.editor import VideoClip, CompositeVideoClip, VideoFileClip, vfx
import numpy as np

# ============================================================================
# STREAMLIT CONFIG
# ============================================================================
st.set_page_config(page_title="Verse Studio", page_icon="✝️", layout="wide")

# ============================================================================
# DESIGN CONFIGURATION
# ============================================================================
DESIGN_CONFIG = {
    "palettes": {
        "Galilee Morning": {
            "bg": ["#faf9f6", "#e0e4d5"],
            "accent": "#c4891f",
            "text_primary": "#183028",
            "text_secondary": "#5a5a5a"
        },
        "Mount Zion Dusk": {
            "bg": ["#f4ebde", "#d6c7a9"],
            "accent": "#987919",
            "text_primary": "#292929",
            "text_secondary": "#555555"
        }
    },

    "aspect_ratios": {
        "Reel / Story (9:16)": (1080, 1920),
        "Square Post (1:1)": (1080, 1080)
    },

    "font_sizes": {
        "hook": 72,
        "verse": 120,
        "reference": 40
    },

    "video_duration": 6,
    "video_fps": 12,

    "gradient_directions": ["Vertical", "Horizontal", "Diagonal"]
}

RESOURCE_CONFIG = {
    "logo_url": "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037",
    "video_backgrounds": {
        "None": None,
        "Ocean Waves": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4"
    },
    "bible_api": "https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv"
}

BOOK_SLUGS = {
    "Psalm": "psalms",
    "Song of Solomon": "song-of-solomon"
}

# ============================================================================
# HELPERS
# ============================================================================
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

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
            else:  # Diagonal
                r = (x + y) / (w + h)

            col = tuple(int((1-r)*c1[i] + r*c2[i]) for i in range(3))
            d.point((x, y), fill=col)

    return img

@st.cache_data(ttl=86400)
def load_font(url, size):
    name = url.split("/")[-1]
    if not os.path.exists(name):
        r = requests.get(url, timeout=10)
        with open(name, "wb") as f:
            f.write(r.content)
    return ImageFont.truetype(name, size)

@st.cache_data(ttl=3600)
def fetch_verse(book, chapter, verse):
    try:
        slug = BOOK_SLUGS.get(book, book.lower().replace(" ", "-"))
        url = f"{RESOURCE_CONFIG['bible_api']}/books/{slug}/chapters/{chapter}/verses/{verse}.json"
        return requests.get(url, timeout=5).json().get("text", "").strip()
    except:
        return "God is our refuge and strength, an ever-present help in trouble."

@st.cache_data(ttl=3600)
def download_logo(url):
    img = Image.open(io.BytesIO(requests.get(url).content)).convert("RGBA")
    return img.filter(ImageFilter.SHARPEN)

def wrap_text(text, font, max_w):
    words, lines, cur = text.split(), [], []
    for w in words:
        test = " ".join(cur + [w])
        if font.getbbox(test)[2] <= max_w:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

# ============================================================================
# IMAGE GENERATION
# ============================================================================
def generate_image(aspect, palette_name, book, chapter, verse, hook, gradient_dir, logo_pos):
    w, h = DESIGN_CONFIG["aspect_ratios"][aspect]
    p = DESIGN_CONFIG["palettes"][palette_name]

    img = create_gradient(w, h, p["bg"][0], p["bg"][1], gradient_dir)
    d = ImageDraw.Draw(img)

    hook_font = load_font(
        "https://github.com/google/fonts/raw/main/ofl/inter/Inter-SemiBold.ttf",
        DESIGN_CONFIG["font_sizes"]["hook"]
    )
    verse_font = load_font(
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf",
        DESIGN_CONFIG["font_sizes"]["verse"]
    )
    ref_font = load_font(
        "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf",
        DESIGN_CONFIG["font_sizes"]["reference"]
    )

    verse_text = fetch_verse(book, chapter, verse)
    ref = f"{book} {chapter}:{verse}"

    margin = 120
    max_w = w - margin * 2

    hook_lines = wrap_text(hook, hook_font, max_w)
    verse_lines = wrap_text(verse_text, verse_font, max_w)

    y = int(h * 0.28)

    for line in hook_lines:
        tw, th = hook_font.getbbox(line)[2:]
        d.text(((w - tw)//2, y), line, font=hook_font, fill=hex_to_rgb(p["accent"]))
        y += th + 24

    y += 40
    for line in verse_lines:
        tw, th = verse_font.getbbox(line)[2:]
        d.text(((w - tw)//2, y), line, font=verse_font, fill=hex_to_rgb(p["text_primary"]))
        y += th + 30

    tw, th = ref_font.getbbox(ref)[2:]
    d.text(((w - tw)//2, y + 30), ref, font=ref_font, fill=hex_to_rgb(p["text_secondary"]))

    if logo_pos != "Hidden":
        logo = download_logo(RESOURCE_CONFIG["logo_url"])
        size = 120
        logo = logo.resize((size, size), Image.LANCZOS)

        x = w - size - 40
        y = h - size - 40
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0,0,size,size), fill=255)
        img.paste(logo, (x, y), mask)

    return img

# ============================================================================
# VIDEO GENERATION (PERFORMANCE SAFE)
# ============================================================================
def generate_video(*args):
    static_img = generate_image(*args[:-1])
    static_np = np.array(static_img)

    def frame(t):
        return static_np

    clip = VideoClip(frame, duration=DESIGN_CONFIG["video_duration"])
    clip = clip.set_fps(DESIGN_CONFIG["video_fps"])

    name = f"verse_{int(time.time())}.mp4"
    clip.write_videofile(name, fps=DESIGN_CONFIG["video_fps"], codec="libx264", verbose=False, logger=None)

    with open(name, "rb") as f:
        data = f.read()
    os.remove(name)
    return data

# ============================================================================
# UI
# ============================================================================
st.title("💎 Verse Studio")

with st.sidebar:
    aspect = st.selectbox("Aspect Ratio", DESIGN_CONFIG["aspect_ratios"])
    palette = st.selectbox("Color Theme", DESIGN_CONFIG["palettes"])
    gradient = st.selectbox("Gradient Direction", DESIGN_CONFIG["gradient_directions"])

    book = st.selectbox("Book", list(BOOK_SLUGS.keys()) + ["Proverbs", "Isaiah", "John"])
    chapter = st.number_input("Chapter", 1, 150, 46)
    verse = st.number_input("Verse", 1, 176, 1)
    hook = st.text_input("Hook", "Need strength today?")
    logo = st.selectbox("Logo", ["Bottom Right", "Hidden"])

img = generate_image(aspect, palette, book, chapter, verse, hook, gradient, logo)
st.image(img, use_column_width=True)

buf = io.BytesIO()
img.save(buf, "PNG")
st.download_button("📥 Download PNG", buf.getvalue(), "verse.png")

if st.button("🎬 Generate Video"):
    st.video(generate_video(aspect, palette, book, chapter, verse, hook, gradient, logo))