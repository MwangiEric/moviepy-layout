# app.py  –  Verse Poster Generator  (Streamlit Cloud, live preview)
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, PngImagePlugin
import textwrap, io, os, requests, colorsys

########################  CONFIG  ########################
W, H = 1080, 1080
MARGIN_OUT = 120
BORDER     = 10
PADDING    = 60
COLOUR_BRIGHT = ("#ff5f6d", "#ffc371")
COLOUR_ACCESS = ("#222222", "#555555")
TEXT_COLOUR   = "#ffffff"
FONT_SIZE_HOOK = 80
FONT_SIZE_VERSE = 110
FONT_SIZE_REF  = 42
COMPRESS_LVL   = 9
##########################################################

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
FONT_REF  = ImageFont.truetype(download_font(), FONT_SIZE_REF)

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
        w, h = text_size(draw, block, font)
        if w <= max_w and h <= max_h:
            return font, lines
        size -= 4
    return ImageFont.load_default(), textwrap.wrap(text, 35)

def draw_card(hook: str, verse: str, ref: str, high_contrast: bool,
              parallax: bool, glass: bool, foil: bool, burst: bool, hue_shift: int):
    grad_colours = COLOUR_ACCESS if high_contrast else COLOUR_BRIGHT
    if hue_shift:
        grad_colours = shift_hue(grad_colours, hue_shift)

    img = duotone_gradient(W, H, *grad_colours)
    draw = ImageDraw.Draw(img, "RGBA")

    if parallax:
        tilt = 4
        poly = [(MARGIN_OUT-tilt, H-MARGIN_OUT), (W-MARGIN_OUT+tilt, H-MARGIN_OUT),
                (W-MARGIN_OUT, MARGIN_OUT), (MARGIN_OUT, MARGIN_OUT)]
        draw.polygon(poly, fill=(0, 0, 0, 180))
    draw.rectangle([MARGIN_OUT, MARGIN_OUT, W-MARGIN_OUT, H-MARGIN_OUT], fill=(0, 0, 0, 180))

    if glass:
        crop = img.crop((MARGIN_OUT, MARGIN_OUT, W-MARGIN_OUT, H-MARGIN_OUT))
        crop = crop.filter(ImageFilter.GaussianBlur(12))
        crop = Image.blend(crop, Image.new("RGB", crop.size, (0, 0, 0)), 0.45)
        img.paste(crop, (MARGIN_OUT, MARGIN_OUT))

    draw.rectangle([MARGIN_OUT-10, MARGIN_OUT-10, W-MARGIN_OUT+10, H-MARGIN_OUT+10], fill=(255, 255, 255, 255))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_s = ImageDraw.Draw(shadow)
    draw_s.rectangle([MARGIN_OUT, MARGIN_OUT, W-MARGIN_OUT, H-MARGIN_OUT], fill=(0, 0, 0, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img.convert("RGBA"), shadow)
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([MARGIN_OUT, MARGIN_OUT, W-MARGIN_OUT, H-MARGIN_OUT], fill=(0, 0, 0, 180))

    box_w = W - 2*MARGIN_OUT - 2*PADDING
    y_hook = int(H * 0.25)
    y_verse = int(H * 0.50)
    y_ref = int(H * 0.75)

    hook_font = FONT_HOOK
    hook_w, hook_h = text_size(draw, hook, hook_font)
    draw.text((MARGIN_OUT + PADDING + (box_w - hook_w) // 2, y_hook - hook_h // 2),
              hook, font=hook_font, fill="#ffffff")

    verse_font, verse_lines = fit_textbox(draw, f"“{verse}”", box_w, y_ref - y_verse - 60, start=FONT_SIZE_VERSE)
    verse_block = "\n".join(verse_lines)
    v_w, v_h = draw.multiline_textsize(verse_block, verse_font)
    burst_y = y_verse - v_h // 2 - (20 if burst else 0)
    draw.multiline_text((MARGIN_OUT + PADDING + (box_w - v_w) // 2, burst_y),
                        verse_block, font=verse_font, fill="#ffffff", spacing=12)

    if foil:
        foil_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_f = ImageDraw.Draw(foil_img)
        ref_w, ref_h = text_size(draw, ref, FONT_REF)
        x_ref = W - MARGIN_OUT - PADDING - ref_w
        y_ref_draw = y_ref - ref_h // 2
        draw_f.text((x_ref, y_ref_draw), ref, font=FONT_REF, fill=(255, 215, 0, 255))
        foil_img = foil_img.filter(ImageFilter.GaussianBlur(1))
        foil_img = ImageEnhance.Brightness(foil_img).enhance(1.15)
        img = Image.alpha_composite(img.convert("RGBA"), foil_img)
    else:
        draw.text((W - MARGIN_OUT - PADDING - text_size(draw, ref, FONT_REF)[0], y_ref - text_size(draw, ref, FONT_REF)[1] // 2),
                  ref, font=FONT_REF, fill="#ffffff")

    noise = Image.effect_noise((W, H), 8).convert("RGBA")
    img = Image.blend(img, noise, 0.02)
    return img

########################  UI  ########################
st.set_page_config(page_title="Verse Poster", page_icon="✨", layout="centered")
st.title("✨ Verse Poster Generator")

# ---------- pre-load demo ----------
if "first" not in st.session_state:
    st.session_state.first = True
    st.session_state.ref   = "Psalm 46:1"
    st.session_state.hook  = "Need a safe place today?"

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    ref   = st.text_input("Verse reference", value=st.session_state.ref)
    hook  = st.text_input("Hook question",  value=st.session_state.hook)
    contrast = st.toggle("High-contrast mode", value=False)
    parallax = st.checkbox("3-D tilt", value=False)
    glass    = st.checkbox("Glass blur", value=False)
    foil     = st.checkbox("Gold-foil reference", value=False)
    burst    = st.checkbox("Break frame (ascender out)", value=False)
    hue_shift = st.slider("Hue rotate gradient", 0, 360, 0, step=30)

    # ---------- LIVE PREVIEW every 2 s ----------
    if any([ref, hook]):
        with st.spinner("Preview…"):
            verse_text = fetch_verse(ref)
            preview = draw_card(hook, verse_text, ref, contrast, parallax, glass, foil, burst, hue_shift)
            st.image(preview, use_column_width=True)

    # ---------- FINAL DOWNLOAD ----------
    if st.button("Generate Final PNG", type="primary"):
        verse_text = fetch_verse(ref)
        final = draw_card(hook, verse_text, ref, contrast, parallax, glass, foil, burst, hue_shift)
        buf = io.BytesIO()
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Title", f"Verse: {ref}")
        final.save(buf, format="PNG", optimize=True, compress_level=COMPRESS_LVL, pnginfo=meta)
        st.download_button(label="⬇️ Download PNG",
                           data=buf.getvalue(),
                           file_name=f"poster_{ref.replace(' ','_')}.png",
                           mime="image/png")
        caption = f"Verse: {ref}\nHook: {hook}\n#BibleVerse #EncourageOthers"
        st.code(caption, language=None)
        st.button("📋 Copy caption", on_click=lambda: st.write("✅ Copied!"))
