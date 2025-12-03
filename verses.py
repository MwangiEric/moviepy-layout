import streamlit as st
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import textwrap, io, os, requests, random, math

# Config
W, H = 1080, 1080
MARGIN_OUT, PADDING = 120, 60
TEXT_COLOUR = "#ffffff"
FONT_SIZE_HOOK, FONT_SIZE_VERSE, FONT_SIZE_REF = 80, 110, 42
COMPRESS_LVL, PARTICLE_COUNT = 9, 40

# Color palettes for variation (anti-spam)
COLOR_PALETTES = [
    ("#ff5f6d", "#ffc371"), ("#4ecdc4", "#ffeaa7"), ("#a8edea", "#fed6e3"),
    ("#ff9a9e", "#fecfef"), ("#a1c4fd", "#c2e9fb"), ("#667eea", "#764ba2")
]

@st.cache_data
def download_font():
    path = "Poppins-Bold.ttf"
    if not os.path.exists(path):
        url = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
        with open(path, "wb") as f:
            f.write(requests.get(url, timeout=15).content)
    return path

@st.cache_data
def fetch_verse(ref: str) -> str:
    try:
        r = requests.get("https://getbible.net/json", params={"passage": ref.replace(" ", "")}, timeout=5)
        return r.json()[0]["text"]
    except:
        return "God is our refuge and strength (Psalm 46:1)"

def text_size(draw, txt, font):
    bbox = draw.textbbox((0, 0), txt, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def duotone_gradient(w, h, left_hex, right_hex):
    left_rgb = tuple(int(left_hex[i:i+2], 16) for i in (1,3,5))
    right_rgb = tuple(int(right_hex[i:i+2], 16) for i in (1,3,5))
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for x in range(w):
        ratio = x / w
        r = int((1-ratio)*left_rgb[0] + ratio*right_rgb[0])
        g = int((1-ratio)*left_rgb[1] + ratio*right_rgb[1])
        b = int((1-ratio)*left_rgb[2] + ratio*right_rgb[2])
        draw.line([(x,0), (x,h)], fill=(r,g,b))
    return img

def fit_textbox(draw, text, max_w, max_h, start_size=110):
    size = start_size
    while size > 20:
        try:
            font = ImageFont.truetype(download_font(), size)
        except:
            font = ImageFont.load_default()
        wrapper = textwrap.TextWrapper(width=int(max_w/(size*0.6)))
        lines = wrapper.wrap(text)
        block = "
".join(lines)
        w, h = text_size(draw, block, font)
        if w <= max_w and h <= max_h:
            return font, lines
        size -= 4
    return ImageFont.load_default(), [text[:35]]

def draw_frame(particles, grad_colors, hook, verse, ref):
    # Create base gradient (RGB)
    img = duotone_gradient(W, H, *grad_colors)
    draw = ImageDraw.Draw(img)

    # Layout
    box_w = W - 2*MARGIN_OUT - 2*PADDING
    y_hook, y_verse, y_ref = int(H*0.25), int(H*0.50), int(H*0.75)

    # Fonts & measurements
    hook_font = ImageFont.truetype(download_font(), FONT_SIZE_HOOK)
    hook_w, hook_h = text_size(draw, hook, hook_font)
    
    verse_font, verse_lines = fit_textbox(draw, f""{verse}"", box_w, 200, FONT_SIZE_VERSE)
    verse_block = "
".join(verse_lines)
    v_w, v_h = text_size(draw, verse_block, verse_font)
    ref_w, ref_h = text_size(draw, ref, ImageFont.truetype(download_font(), FONT_SIZE_REF))

    # Rotating border
    if particles:
        center_x, center_y = W//2, y_verse
        text_h_tot = hook_h + v_h + ref_h + 120
        angle = particles[0]["angle"]
        pts = []
        for a in range(0, 360, 10):
            rad = math.radians(a + angle)
            x = center_x + math.cos(rad) * (text_h_tot//2 + 50)
            y = center_y + math.sin(rad) * (text_h_tot//2 + 50)
            pts.append((x, y))
        draw.polygon(pts, outline=(255,255,255), width=3)

    # Particles
    for p in particles:
        x, y, r, alpha = int(p["x"]), int(p["y"]), p["radius"], int(p["alpha"])
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255,255,255,alpha))

    # Text
    draw.text((W//2 - hook_w//2, y_hook - hook_h//2), hook, font=hook_font, fill=TEXT_COLOUR)
    draw.multiline_text((W//2 - v_w//2, y_verse - v_h//2), verse_block, font=verse_font, 
                       fill=TEXT_COLOUR, spacing=12)
    draw.text((W-MARGIN_OUT-PADDING-ref_w, y_ref-ref_h//2), ref, 
             font=ImageFont.truetype(download_font(), FONT_SIZE_REF), fill=TEXT_COLOUR)

    # FIXED: Noise layer - create same size/mode as main image
    noise = Image.effect_noise((W, H), 8).convert("RGB")  # RGB, not RGBA
    img = Image.blend(img, noise, 0.02)  # Now modes match!
    return img

# UI
st.set_page_config(page_title="✨ Verse Poster", layout="centered")
st.title("✨ Bible Verse Poster Generator")

# Session state
if "ref" not in st.session_state:
    st.session_state.ref = "Psalm 46:1"
    st.session_state.hook = "Need strength today?"

col1, col2 = st.columns([1,3])
with col2:
    ref = st.text_input("📖 Verse", value=st.session_state.ref)
    hook = st.text_input("💭 Hook", value=st.session_state.hook)
    
    # Options
    st.session_state.contrast = st.toggle("High contrast", value=getattr(st.session_state, 'contrast', False))
    particles_on = st.checkbox("✨ Particles + border", value=True)
    
    if ref:
        with st.spinner("Generating preview..."):
            verse = fetch_verse(ref)
            colors = random.choice(COLOR_PALETTES)
            particles = [{"x": random.randint(50,W-50), "y": random.randint(50,H-50),
                         "radius": random.randint(2,6), "alpha": random.randint(100,200),
                         "angle": random.randint(0,360)} for _ in range(PARTICLE_COUNT)] if particles_on else []
            
            preview = draw_frame(particles, colors, hook, verse, ref)
            st.image(preview, use_column_width=True)
            
            # Timing info
            words = len(verse.split())
            duration = round((words/130)*60 + 1.5, 1)
            st.success(f"🎬 Perfect {duration}s reel length • {words} words")

    # Download
    if st.button("⬇️ Download PNG", type="primary") and ref:
        verse = fetch_verse(ref)
        colors = random.choice(COLOR_PALETTES)
        particles = [{"x": random.randint(50,W-50), "y": random.randint(50,H-50),
                     "radius": random.randint(2,6), "alpha": random.randint(100,200),
                     "angle": random.randint(0,360)} for _ in range(PARTICLE_COUNT)] if particles_on else []
        
        final = draw_frame(particles, colors, hook, verse, ref)
        buf = io.BytesIO()
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Verse", ref)
        final.save(buf, "PNG", optimize=True, compress_level=COMPRESS_LVL, pnginfo=meta)
        
        st.download_button("💾 Save PNG", buf.getvalue(), f"verse_{ref.replace(' ','_')}.png", "image/png")
        
        caption = f"{hook}

"{verse}"

{ref}

Type AMEN 🙏 #BibleVerse #DailyDevotion"
        st.text_area("📝 Copy this caption:", caption, height=100)