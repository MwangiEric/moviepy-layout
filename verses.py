import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, PngImagePlugin
import textwrap, io, os, requests, zipfile, textwrap

########################  CONFIG  ########################
W, H = 1080, 1080
MARGIN_OUT = 120
BORDER     = 10
PADDING    = 60
COLOUR_BRIGHT = ("#ff5f6d", "#ffc371")  # pink → mango
COLOUR_ACCESS = ("#222222", "#555555")  # grey duotone (WCAG)
TEXT_COLOUR   = "#ffffff"
FONT_SIZE_HOOK = 80
FONT_SIZE_VERSE= 110
FONT_SIZE_REF  = 42
COMPRESS_LVL   = 9
##########################################################

@st.cache_data(show_spinner=False)
def download_font():
    """Return path to Poppins-Bold TTF (downloaded once)."""
    url = "https://fonts.google.com/download?family=Poppins"
    r = requests.get(url, timeout=10)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extract("Poppins-Bold.ttf")
    return "Poppins-Bold.ttf"

FONT_HOOK = ImageFont.truetype(download_font(), FONT_SIZE_HOOK)
FONT_REF  = ImageFont.truetype(download_font(), FONT_SIZE_REF)
# verse font – default but scaled later (Cloud-safe fallback)

########################  VERSE FETCH  ########################
@st.cache_data(show_spinner=False)
def fetch_verse(ref: str) -> str:
    try:
        r = requests.get("https://getbible.net/json", params={"passage": ref.replace(" ", "")}, timeout=5)
        return r.json()[0]["text"]
    except Exception as e:
        return f"Verse not found ({e})"

########################  DRAW CARD  ########################
def text_size(draw, txt, font):
    bbox = draw.textbbox((0, 0), txt, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def duotone_gradient(w, h, left_hex, right_hex):
    left_rgb  = tuple(int(left_hex[i:i+2], 16) for i in (1, 3, 5))
    right_rgb = tuple(int(right_hex[i:i+2], 16) for i in (1, 3, 5))
    img = Image.new("RGB", (w, h))
    for x in range(w):
        ratio = x / w
        r = int((1-ratio)*left_rgb[0] + ratio*right_rgb[0])
        g = int((1-ratio)*left_rgb[1] + ratio*right_rgb[1])
        b = int((1-ratio)*left_rgb[2] + ratio*right_rgb[2])
        img.paste((r, g, b), (x, 0, x+1, h))
    return img

def fit_textbox(draw, text, max_w, max_h, start=110):
    size = start
    while size > 20:
        font = ImageFont.truetype(download_font(), size) if size > 50 else ImageFont.load_default()
        wrapper = textwrap.TextWrapper(width=int(max_w / (size * 0.6)))
        lines = wrapper.wrap(text)
        block = "\n".join(lines)
        w, h = draw.multiline_textsize(block, font)
        if w <= max_w and h <= max_h:
            return font, lines
        size -= 4
    return ImageFont.load_default(), textwrap.wrap(text, 35)

def draw_card(hook: str, verse: str, ref: str, high_contrast: bool):
    # 1. gradient background
    grad_colours = COLOUR_ACCESS if high_contrast else COLOUR_BRIGHT
    img = duotone_gradient(W, H, *grad_colours)
    draw = ImageDraw.Draw(img, "RGBA")

    # 2. baseline grid positions
    rect_l = MARGIN_OUT
    rect_t = MARGIN_OUT
    rect_r = W - MARGIN_OUT
    rect_b = H - MARGIN_OUT
    box_w = rect_r - rect_l - 2 * PADDING
    box_h = rect_b - rect_t - 2 * PADDING

    y_hook = int(H * 0.25)
    y_verse_mid = int(H * 0.50)
    y_ref = int(H * 0.75)

    # 3. white border + inner shadow
    draw.rectangle([rect_l - BORDER, rect_t - BORDER, rect_r + BORDER, rect_b + BORDER],
                   fill=(255, 255, 255, 255))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_s = ImageDraw.Draw(shadow)
    draw_s.rectangle([rect_l, rect_t, rect_r, rect_b], fill=(0, 0, 0, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img.convert("RGBA"), shadow)
    draw = ImageDraw.Draw(img, "RGBA")  # redraw after composite
    draw.rectangle([rect_l, rect_t, rect_r, rect_b], fill=(0, 0, 0, 180))

    # 4. HOOK (top grid line)
    hook_w, hook_h = text_size(draw, hook, FONT_HOOK)
    draw.text((rect_l + PADDING + (box_w - hook_w) // 2, y_hook - hook_h // 2),
              hook, font=FONT_HOOK, fill=TEXT_COLOUR)

    # 5. VERSE (centre grid line)
    verse_font, verse_lines = fit_textbox(draw, f"“{verse}”", box_w, box_h - 100, start=FONT_SIZE_VERSE)
    verse_block = "\n".join(verse_lines)
    v_w, v_h = draw.multiline_textsize(verse_block, verse_font)
    draw.multiline_text((rect_l + PADDING + (box_w - v_w) // 2, y_verse_mid - v_h // 2),
                        verse_block, font=verse_font, fill=TEXT_COLOUR, spacing=12)

    # 6. REFERENCE (bottom grid line)
    ref_w, ref_h = text_size(draw, ref, FONT_REF)
    draw.text((rect_r - PADDING - ref_w, y_ref - ref_h // 2), ref, font=FONT_REF, fill=TEXT_COLOUR)

    # 7. noise layer (anti-banding)
    noise = Image.effect_noise((W, H), 8).convert("RGBA")
    img = Image.blend(img, noise, 0.02)

    return img

########################  STREAMLIT UI  ########################
st.set_page_config(page_title="Verse Poster", page_icon="✨", layout="centered")
st.title("✨ Verse Poster Generator")
st.markdown("Create a share-ready Bible verse graphic in seconds.")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ref   = st.text_input("Verse reference", placeholder="e.g. John 14:27")
    hook  = st.text_input("Hook question", placeholder="e.g. Need peace today?")
    contrast = st.toggle("High-contrast mode", value=False, help="Better for accessibility")

    if st.button("Generate Poster", type="primary"):
        if not ref or not hook:
            st.error("Please fill both fields.")
            st.stop()
        with st.spinner("Building your card…"):
            verse_text = fetch_verse(ref)
            img = draw_card(hook, verse_text, ref, contrast)
            buf = io.BytesIO()
            meta = PngImagePlugin.PngInfo()
            meta.add_text("Title", f"Verse: {ref}")
            img.save(buf, format="PNG", optimize=True, compress_level=COMPRESS_LVL, pnginfo=meta)
            st.image(img, use_column_width=True)
            st.download_button(label="⬇️ Download PNG",
                               data=buf.getvalue(),
                               file_name=f"poster_{ref.replace(' ','_')}.png",
                               mime="image/png")
            caption = f"Verse: {ref}\nHook: {hook}\n#BibleVerse #EncourageOthers"
            st.code(caption, language=None)
            st.button("📋 Copy caption", on_click=lambda: st.write("✅ Copied!"))
