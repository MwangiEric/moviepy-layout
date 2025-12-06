import streamlit as st
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import io, os, requests, random, math, time, textwrap

# Streamlit page config (called once)
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

# Constants and color palettes
W, H = 1080, 1920  # Canvas size (vertical reels/stories)
MARGIN = 100
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

def create_gradient(w, h, c1, c2):
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for x in range(w):
        ratio = x / w
        r = int((1-ratio)*int(c1[1:3],16) + ratio*int(c2[1:3],16))
        g = int((1-ratio)*int(c1[3:5],16) + ratio*int(c2[3:5],16))
        b = int((1-ratio)*int(c1[5:7],16) + ratio*int(c2[5:7],16))
        draw.line([(x, 0), (x, h)], fill=(r, g, b))
    return img.convert("RGBA")

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    while words:
        line_words = []
        while words:
            line_words.append(words.pop(0))
            w, _ = font.getsize(" ".join(line_words + words[:1]))
            if w > max_width:
                break
        lines.append(" ".join(line_words))
    return lines

def draw_rounded_rect(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

def draw_glow_text(draw, pos, text, font, fill, glow_color):
    x, y = pos
    for offset in range(4, 0, -1):
        draw.text((x + offset, y + offset), text, font=font, fill=glow_color+(50,))
    draw.text(pos, text, font=font, fill=fill)

def draw_cross(draw, cx, cy, size=100, phase=0):
    pulse = 1 + 0.1 * math.sin(phase)
    lw = int(15 * pulse)
    draw.line([(cx, cy - size//2), (cx, cy + size//2)], fill=(255, 255, 255, 180), width=lw)
    draw.line([(cx - size//2, cy), (cx + size//2, cy)], fill=(255,255,255,180), width=lw)

def generate_poster(template, palette_mode, ref, hook):
    verse_text = fetch_verse(ref)
    pal = random.choice(PALETTES[palette_mode])
    base = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    base = base.convert("RGBA")
    draw = ImageDraw.Draw(base)

    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2

    draw_rounded_rect(draw, [box_x, box_y, box_x + box_w, box_y + box_h], 40, fill=(0,0,0,180) if palette_mode == "dark" else (255,255,255,200))

    # Text wrapping inside box with margin
    max_text_width = box_w - 100
    hook_lines = wrap_text(hook, HOOK_FONT, max_text_width)
    verse_lines = wrap_text(f"“{verse_text}”", VERSE_FONT, max_text_width)
    ref_lines = wrap_text(ref, REF_FONT, max_text_width)

    # Calculate total height
    hook_h_total = len(hook_lines) * HOOK_FONT.getsize("A")[1] + (len(hook_lines)-1)*10
    verse_h_total = len(verse_lines) * VERSE_FONT.getsize("A")[1] + (len(verse_lines)-1)*8
    ref_h_total = len(ref_lines) * REF_FONT.getsize("A")[1] + (len(ref_lines)-1)*6
    total_height = hook_h_total + verse_h_total + ref_h_total + 40

    current_y = box_y + (box_h - total_height) // 2

    # Draw hook text
    hook_color = tuple(int(pal["accent"].lstrip("#")[i:i+2], 16) for i in (0,2,4)) + (255,)
    for line in hook_lines:
        w, h = HOOK_FONT.getsize(line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += h + 10

    # Draw glowing verse text
    verse_fill = (255,255,255,255)
    glow_fill = (100,149,237,150)
    for line in verse_lines:
        w, h = VERSE_FONT.getsize(line)
        for offset in (1,0,-1):
            draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
        draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
        current_y += h + 8

    # Draw reference text
    for line in ref_lines:
        w, h = REF_FONT.getsize(line)
        draw.text(((W-w)//2, current_y), line, font=REF_FONT, fill=hook_color)
        current_y += h + 6

    # Animated crosses for golden template
    if template == "Golden Hour":
        phase = time.time() % (2 * math.pi)
        draw_cross(draw, W//4, H//3, 120, phase)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase + math.pi)

    return base, verse_text

# UI controls
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

# Placeholder for future video output
st.info("🎥 Video output with animations coming soon!")