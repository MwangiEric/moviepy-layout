import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, PngImagePlugin
import textwrap, io, os, requests, random, math

# Config
W, H = 1080, 1080
MARGIN_OUT = 120
BORDER = 10
PADDING = 60
COLOUR_BRIGHT = ("#ff5f6d", "#ffc371")
COLOUR_ACCESS = ("#222222", "#555555")
TEXT_COLOUR = "#ffffff"
FONT_SIZE_HOOK = 80
FONT_SIZE_VERSE = 110
FONT_SIZE_REF = 42
COMPRESS_LVL = 9
PARTICLE_COUNT = 40

@st.cache_data(show_spinner=False)
def download_font():
    path = "Poppins-Bold.ttf"
    if not os.path.exists(path):
        url = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
    return path

FONT_HOOK = ImageFont.truetype(download_font(), FONT_SIZE_HOOK)
FONT_REF = ImageFont.truetype(download_font(), FONT_SIZE_REF)

@st.cache_data(show_spinner=False)
def fetch_verse(ref: str) -> str:
    try:
        r = requests.get("https://getbible.net/json", params={"passage": ref.replace(" ", "")}, timeout=5)
        return r.json()[0]["text"]
    except Exception as e:
        return f"Verse not found ({e})"

def text_size(draw, txt, font):
    l, t, r, b = draw.textbbox((0, 0), txt, font=font)
    return r - l, b - t

def duotone_gradient(w, h, left_hex, right_hex):
    left_rgb = tuple(int(left_hex[i:i + 2], 16) for i in (1, 3, 5))
    right_rgb = tuple(int(right_hex[i:i + 2], 16) for i in (1, 3, 5))
    img = Image.new("RGB", (w, h))
    for x in range(w):
        ratio = x / w
        r = int((1 - ratio) * left_rgb[0] + ratio * right_rgb[0])
        g = int((1 - ratio) * left_rgb[1] + ratio * right_rgb[1])
        b = int((1 - ratio) * left_rgb[2] + ratio * right_rgb[2])
        img.paste((r, g, b), (x, 0, x + 1, h))
    return img

def fit_textbox(draw, text, max_w, max_h, start=110):
    size = start
    while size > 20:
        font = ImageFont.truetype(download_font(), size) if size > 50 else ImageFont.load_default()
        wrapper = textwrap.TextWrapper(width=int(max_w / (size * 0.6)))
        lines = wrapper.wrap(text)
        block = "
".join(lines)
        l, t, r, b = draw.textbbox((0, 0), block, font=font)
        w, h = r - l, b - t
        if w <= max_w and h <= max_h:
            return font, lines
        size -= 4
    return ImageFont.load_default(), textwrap.wrap(text, 35)

def draw_frame(particles, grad_colours, hook, verse, ref, high_contrast):
    img = duotone_gradient(W, H, *grad_colours)
    draw = ImageDraw.Draw(img, "RGBA")

    box_w = W - 2 * MARGIN_OUT - 2 * PADDING
    y_hook = int(H * 0.25)
    y_verse = int(H * 0.50)
    y_ref = int(H * 0.75)

    hook_font = FONT_HOOK
    hook_w, hook_h = text_size(draw, hook, hook_font)
    verse_font, verse_lines = fit_textbox(draw, f"“{verse}”", box_w, y_ref - y_verse - 60, start=FONT_SIZE_VERSE)
    verse_block = "
".join(verse_lines)
    l, t, r, b = draw.textbbox((0, 0), verse_block, verse_font)
    v_w, v_h = r - l, b - t
    ref_w, ref_h = text_size(draw, ref, FONT_REF)

    center_x = W // 2
    center_y = y_verse
    text_h_tot = hook_h + v_h + ref_h + 120
    angle = particles[0]["angle"] if particles else 0
    pts = []
    for a in range(0, 360, 10):
        x = center_x + math.cos(math.radians(a + angle)) * (text_h_tot // 2 + 50)
        y = center_y + math.sin(math.radians(a + angle)) * (text_h_tot // 2 + 50)
        pts.append((x, y))
    draw.polygon(pts, outline=(255, 255, 255, 180), width=3)

    for p in particles:
        x = int(p["x"])
        y = int(p["y"])
        r = p["radius"]
        alpha = int(p["alpha"])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, alpha))

    draw.text((W // 2 - hook_w // 2, y_hook - hook_h // 2), hook, font=hook_font, fill=TEXT_COLOUR)
    draw.multiline_text((W // 2 - v_w // 2, y_verse - v_h // 2), verse_block, font=verse_font, fill=TEXT_COLOUR, spacing=12)
    draw.text((W - MARGIN_OUT - PADDING - ref_w, y_ref - ref_h // 2), ref, font=FONT_REF, fill=TEXT_COLOUR)

    noise = Image.effect_noise((W, H), 8).convert("RGBA")
    img = Image.blend(img, noise, 0.02)
    return img

st.set_page_config(page_title="Verse Poster", page_icon="✨", layout="centered")
st.title("✨ Verse Poster Generator")

if "first" not in st.session_state:
    st.session_state.first = True
    st.session_state.ref = "Psalm 46:1"
    st.session_state.hook = "Need a safe place today?"

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ref = st.text_input("Verse reference", value=st.session_state.ref)
    hook = st.text_input("Hook question", value=st.session_state.hook)
    contrast = st.toggle("High-contrast mode", value=False)
    particles_on = st.checkbox("Subtle particles + rotating border", value=True)

    if any([ref, hook]):
        with st.spinner("Preview…"):
            verse_text = fetch_verse(ref)
            particles = [{"x": random.randint(50, W - 50), "y": random.randint(50, H - 50),
                          "radius": random.randint(2, 5), "alpha": random.randint(80, 180),
                          "angle": 0} for _ in range(PARTICLE_COUNT)] if particles_on else []
            preview = draw_frame(particles, COLOUR_ACCESS if contrast else COLOUR_BRIGHT, hook, verse_text, ref, contrast)
            st.image(preview, use_column_width=True)

    if st.button("Generate Final PNG", type="primary"):
        verse_text = fetch_verse(ref)
        particles = [{"x": random.randint(50, W - 50), "y": random.randint(50, H - 50),
                      "radius": random.randint(2, 5), "alpha": random.randint(80, 180),
                      "angle": 0} for _ in range(PARTICLE_COUNT)] if particles_on else []
        final = draw_frame(particles, COLOUR_ACCESS if contrast else COLOUR_BRIGHT, hook, verse_text, ref, contrast)
        buf = io.BytesIO()
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Title", f"Verse: {ref}")
        final.save(buf, format="PNG", optimize=True, compress_level=COMPRESS_LVL, pnginfo=meta)
        st.download_button(label="⬇️ PNG (with effects)",
                           data=buf.getvalue(),
                           file_name=f"poster_{ref.replace(' ', '_')}.png",
                           mime="image/png")
        caption = f"Verse: {ref}
Hook: {hook}
#BibleVerse #EncourageOthers"
        st.code(caption, language=None)
        st.button("📋 Copy caption", on_click=lambda: st.write("✅ Copied!"))