import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# STREAMLIT & THEME SETUP
# ============================================================================
st.set_page_config(page_title="Still Mind Premium", page_icon="✝️", layout="wide")

COLORS = {
    "Still Mind (Green/Blue)": {
        "bg": [(10, 30, 50, 255), (20, 50, 80, 255)],
        "accent": (76, 175, 80, 255),
        "text": (255, 255, 255, 255),
        "glow": (76, 175, 80, 160)
    },
    "Midnight Deep": {
        "bg": [(5, 10, 20, 255), (10, 25, 45, 255)],
        "accent": (0, 255, 150, 255),
        "text": (255, 255, 255, 255),
        "glow": (0, 255, 150, 140)
    }
}

BIBLE_BOOKS = ["Psalm", "Matthew", "John", "Romans", "Ephesians", "Philippians", "James", "Proverbs", "Isaiah"]

# ============================================================================
# PREMIUM DECORATIONS (GLOW & BRACKETS)
# ============================================================================
def draw_premium_decorations(draw, x1, y1, x2, y2, accent_color, t=0):
    """Draws a semi-transparent box with glowing pulsing corner brackets."""
    # 1. Main Background Box
    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 180))
    
    # 2. Pulsing Logic (The 'Breathing' effect)
    pulse = 0.6 + 0.4 * abs(math.sin(t * 2.5)) 
    glow_color = accent_color[:3] + (int(130 * pulse),)
    
    b_len = 55   # Length of bracket arms
    b_width = 4  # Core thickness
    
    def draw_corner(cx, cy, dx, dy, width, color):
        # Horizontal arm
        draw.line([(cx, cy), (cx + dx, cy)], fill=color, width=width)
        # Vertical arm
        draw.line([(cx, cy), (cx, cy + dy)], fill=color, width=width)

    # 3. Layered Glow (Draw 3 layers for a soft neon look)
    for layer in range(3, 0, -1):
        # Outer layers are wider and use glow_color; inner layer is sharp accent_color
        current_w = b_width + (layer * 5)
        current_c = glow_color if layer > 1 else accent_color
        
        draw_corner(x1, y1, b_len, b_len, current_w, current_c)      # Top-Left
        draw_corner(x2, y1, -b_len, b_len, current_w, current_c)     # Top-Right
        draw_corner(x1, y2, b_len, -b_len, current_w, current_c)     # Bottom-Left
        draw_corner(x2, y2, -b_len, -b_len, current_w, current_c)    # Bottom-Right

    # 4. Thin Interior Decoration Line
    draw.rectangle([x1+15, y1+15, x2-15, y2-15], outline=accent_color[:3]+(45,), width=1)

# ============================================================================
# UTILITIES & TYPEWRITER LOGIC
# ============================================================================
@st.cache_data(ttl=3600)
def fetch_bible_verse(book, chapter, verse):
    """Fetches text from API based on user selection."""
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.json().get("text", "").strip().replace("\n", " ")
    except: pass
    return "The Lord is my shepherd; I shall not want."

def get_typewriter_substring(text, t, duration=3.5):
    """Calculates how much text to show based on time."""
    progress = min(1.0, t / duration)
    chars_to_show = int(len(text) * progress)
    return text[:chars_to_show]

def load_font_safe(size, bold=False):
    """Fallback font loader."""
    try:
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
        for p in paths:
            if os.path.exists(p): return ImageFont.truetype(p, size)
    except: pass
    return ImageFont.load_default()

def wrap_text_to_lines(text, font, max_w):
    """Helper to split text into lines for a specific font and width."""
    lines, current = [], ""
    for word in text.split():
        test = f"{current} {word}".strip()
        if font.getbbox(test)[2] - font.getbbox(test)[0] <= max_w:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

# ============================================================================
# MAIN COMPOSITION ENGINE
# ============================================================================
def create_studio_frame(w, h, book, chapter, verse, hook, colors, t=0, is_video=False):
    img = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(img)
    c1, c2 = colors["bg"]
    acc = colors["accent"]

    # 1. Background Gradient (Dynamic movement)
    for y in range(h):
        ratio = (y / h) + (math.sin(t * 0.4) * 0.05)
        ratio = max(0, min(1, ratio))
        draw.line([(0, y), (w, y)], fill=tuple(int((1-ratio)*c1[i] + ratio*c2[i]) for i in range(4)))

    # 2. Decoration: Drifting Particles
    for i in range(15):
        px = (w * (0.5 + 0.45 * math.sin(t * 0.2 + i)))
        py = (h * (0.5 + 0.45 * math.cos(t * 0.15 + i)))
        draw.ellipse([px-2, py-2, px+2, py+2], fill=acc[:3]+(90,))

    # 3. Content Retrieval
    full_verse_text = fetch_bible_verse(book, chapter, verse)
    
    # Pre-calculate Final Font Size (so the box size stays stable)
    # Target size 110 for better breathing room
    v_size = 110
    v_font = load_font_safe(v_size)
    # Check if text fits, if not, reduce
    while len(wrap_text_to_lines(full_verse_text, v_font, w-280)) * v_size * 1.5 > h * 0.5:
        v_size -= 5
        v_font = load_font_safe(v_size)

    # 4. Box Sizing
    final_lines = wrap_text_to_lines(full_verse_text, v_font, w-280)
    line_h = v_size * 1.5
    box_h = (len(final_lines) * line_h) + 140
    box_y = (h - box_h) // 2
    
    # 5. Draw Decorations
    draw_premium_decorations(draw, 100, box_y, w-100, box_y + box_h, acc, t)

    # 6. Typewriter Verse Text
    display_text = get_typewriter_substring(full_verse_text, t) if is_video else full_verse_text
    current_animated_lines = wrap_text_to_lines(display_text, v_font, w-280)
    
    curr_y = box_y + 80
    for line in current_animated_lines:
        tw = v_font.getbbox(line)[2] - v_font.getbbox(line)[0]
        # Text Glow/Shadow
        draw.text(((w-tw)//2+1, curr_y+1), line, font=v_font, fill=(0,0,0,100))
        draw.text(((w-tw)//2, curr_y), line, font=v_font, fill=(255,255,255))
        curr_y += line_h

    # 7. Hook and Reference
    h_font = load_font_safe(75, True)
    r_font = load_font_safe(45, True)
    
    if hook:
        hw = h_font.getbbox(hook)[2] - h_font.getbbox(hook)[0]
        draw.text(((w-hw)//2, box_y - 130), hook.upper(), font=h_font, fill=acc)
        
    ref_text = f"— {book} {chapter}:{verse} —"
    rw = r_font.getbbox(ref_text)[2] - r_font.getbbox(ref_text)[0]
    # Fade in reference after typewriter is 80% done
    ref_alpha = 255 if not is_video else int(max(0, min(1, (t-3.5)/0.8)) * 255)
    draw.text(((w-rw)//2, box_y + box_h + 40), ref_text, font=r_font, fill=acc[:3]+(ref_alpha,))

    return img

# ============================================================================
# STREAMLIT UI
# ============================================================================
with st.sidebar:
    st.title("Still Mind Studio")
    size_mode = st.selectbox("Resolution", ["TikTok (9:16)", "Square (1:1)"])
    theme_mode = st.selectbox("Color Palette", list(COLORS.keys()))
    hook_input = st.text_input("Top Header", "Peace Be Still")
    
    st.divider()
    st.subheader("Scripture Selection")
    sel_book = st.selectbox("Bible Book", BIBLE_BOOKS)
    col_c, col_v = st.columns(2)
    sel_chapter = col_c.number_input("Chapter", 1, 150, 46)
    sel_verse = col_v.number_input("Verse", 1, 176, 1)

W, H = (1080, 1920) if size_mode.startswith("TikTok") else (1080, 1080)
active_colors = COLORS[theme_mode]

# Instant Preview
st.subheader("Live Preview")
static_img = create_studio_frame(W, H, sel_book, sel_chapter, sel_verse, hook_input, active_colors, t=0, is_video=False)
st.image(static_img, use_container_width=True)

col_render, col_dl = st.columns(2)

with col_render:
    if st.button("🎬 Render Pulsing Video (6s)", use_container_width=True):
        with st.spinner("Applying Typewriter and Glow Layers..."):
            def make_frame(t):
                f = create_studio_frame(W, H, sel_book, sel_chapter, sel_verse, hook_input, active_colors, t, is_video=True)
                return np.array(f.convert("RGB"))
            
            clip = VideoClip(make_frame, duration=6).set_fps(15)
            clip.write_videofile("premium_output.mp4", codec="libx264", audio=False, logger=None)
            st.video("premium_output.mp4")

with col_dl:
    buf = io.BytesIO()
    static_img.save(buf, format='PNG')
    st.download_button("📥 Download Static Poster", buf.getvalue(), "still_mind_verse.png", use_container_width=True)

st.divider()
st.caption("Still Mind Full Studio Edition | Powered by Gemini 3 Flash")
