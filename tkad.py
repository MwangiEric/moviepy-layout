import streamlit as st
import os, io, tempfile, math, time, gc, requests, subprocess
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import AudioFileClip
import contextlib
import cv2

# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------
WIDTH, HEIGHT = 1080, 1920
FPS, DURATION = 24, 4
TOTAL_FRAMES  = FPS * DURATION

# Colours
MAROON      = (153, 0, 0)
WHITE       = (255, 255, 255)
LIME_GREEN  = (50, 205, 50)
TEXT_COLOUR = (30, 30, 30)
BG_COLOUR   = (245, 245, 247)

# Remote assets  (WebP when available → 30 % smaller)
LOGO_URL    = "https://www.tripplek.co.ke/wp-content/uploads/2024/10/Tripple-K-Com-Logo-255-by-77.png"
PRODUCT_URL = "https://www.tripplek.co.ke/wp-content/uploads/2025/02/iphone-16e-33.png"
AUDIO_URL   = "https://ik.imagekit.io/ericmwangi/tech-ambient.mp3?updatedAt=1764372632499"

# --------------------------------------------------------
# HELPERS
# --------------------------------------------------------
@st.cache_data(show_spinner=False)
def download(url, suffix=".png"):
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception as e:
        st.warning("Asset download failed – using fallback")
    return None


@st.cache_resource(show_spinner=False)
def load_image(url_or_path, target_size, name="Image"):
    if os.path.isfile(url_or_path):
        img = Image.open(url_or_path).convert("RGBA")
    else:
        path = download(url_or_path, ".png")
        if not path:
            img = Image.new("RGBA", target_size, (0, 0, 0, 0))
            ImageDraw.Draw(img).rounded_rectangle(
                (50, 50) + tuple(map(lambda x: x - 50, target_size)), radius=40,
                fill="#ffffff", outline="#000", width=3)
        else:
            img = Image.open(path).convert("RGBA")
    return img.resize(target_size, Image.Resampling.LANCZOS)


@st.cache_resource(show_spinner=False)
def _font_bytes(bold=True):
    url = ("https://github.com/google/fonts/raw/main/ofl/inter/" +
           ("Inter-Bold.ttf" if bold else "Inter-Medium.ttf"))
    return requests.get(url, timeout=20).content


def get_font(size, bold=True):
    size = max(20, int(size))
    try:
        return ImageFont.truetype(io.BytesIO(_font_bytes(bold)), size)
    except Exception:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except:
            return ImageFont.load_default()

# --------------------------------------------------------
# PREMIUM LOOK FILTERS  (GPU)
# --------------------------------------------------------
def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def film_grain_gpu(gpu, intensity=0.02):
    noise = cv2.cuda_GpuMat(gpu.size(), cv2.CV_8UC3)
    cv2.cuda.randn(noise, 0, intensity * 255, noise)
    return cv2.cuda.add(gpu, noise, dtype=cv2.CV_8UC3)


def chromatic_aberration_gpu(gpu, amount=1.5):
    b, g, r = cv2.cuda.split(gpu)
    b = cv2.cuda.resize(b, (b.cols + int(amount), b.rows + int(amount)))
    b = b.colRange(int(amount // 2), b.cols - int(amount // 2))
    b = b.rowRange(int(amount // 2), b.rows - int(amount // 2))
    return cv2.cuda.merge([b, g, r])


# --------------------------------------------------------
# LIGHT BACKGROUND  (CPU)
# --------------------------------------------------------
def light_bg(t):
    base = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOUR)
    draw = ImageDraw.Draw(base, "RGBA")

    for i in range(4):
        x = int(WIDTH / 2 + 400 * math.sin(t * 0.2 + i))
        y = int(HEIGHT / 2 + 400 * math.cos(t * 0.15 + i))
        r = 280 + 60 * math.sin(t * 0.3 + i)
        opacity = int(60 + 40 * math.sin(t * 0.4 + i))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(*ACCENT, opacity))

    for i in range(6):
        w = 200 + 50 * math.sin(t * 0.7 + i)
        h = 200 + 50 * math.cos(t * 0.5 + i)
        cx = WIDTH / 2 + 350 * math.sin(t * 0.6 + i)
        cy = HEIGHT / 2 + 350 * math.cos(t * 0.5 + i)
        angle = math.degrees(t * 0.4 + i * 60)
        coords = []
        for k in range(4):
            θ = math.radians(angle + k * 90)
            coords.append((cx + w / 2 * math.cos(θ), cy + h / 2 * math.sin(θ)))
        opacity = int(80 + 50 * math.sin(t * 0.8 + i))
        draw.polygon(coords, fill=(*LIME_GREEN, opacity))

    for i in range(20):
        x = int(WIDTH * (0.05 + 0.9 * (math.sin(t * 2.1 + i * 2.3) + 1) / 2))
        y = int(HEIGHT * (0.05 + 0.9 * (math.cos(t * 2.3 + i * 1.9) + 1) / 2))
        s = 6 + 4 * math.sin(t * 3 + i)
        opacity = int(200 + 55 * math.sin(t * 4 + i))
        draw.ellipse([x - s, y - s, x + s, y + s], fill=(*WHITE, opacity))

    return np.array(base)

# --------------------------------------------------------
# TEXT BOX  (vector scale)
# --------------------------------------------------------
def text_box(text, font, colour):
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    w, h = r - l, b - t
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(box)
    draw.text((-l, -t), text, font=font, fill=colour)
    return box

# --------------------------------------------------------
# DRAW FRAME  (CPU → GPU)
# --------------------------------------------------------
def draw_frame(t, product, specs, price,
               logo_size, logo_xy, product_size, product_xy,
               headline_size, headline_xy, spec_size, spec_xy, spec_spacing,
               price_size, price_xy, price_font,
               cta_size, cta_xy, cta_font):
    # CPU part
    rgb  = light_bg(t)
    base = Image.fromarray(rgb).convert("RGBA")
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

    # logo
    logo = load_image(LOGO_URL, logo_size)
    canvas.paste(logo, logo_xy, logo)

    # headline (centred + spring motion)
    head_img = text_box(product.upper(), get_font(headline_size), TEXT_COLOUR)
    spring_x = int(40 * ease_out_elastic((t*0.6) % 1))
    head_x = (WIDTH - head_img.width) // 2 + headline_xy[0] + spring_x
    canvas.paste(head_img, (head_x, headline_xy[1]), head_img)

    # product (centred + float)
    phone = load_image(PRODUCT_URL, product_size)
    float_y = int(product_xy[1] + 40 * ease_out_elastic((t*0.8) % 1))
    prod_x = (WIDTH - product_size[0]) // 2 + product_xy[0]
    canvas.paste(phone, (prod_x, float_y), phone)

    # specs
    font_spec = get_font(spec_size[1])
    spec_lines = specs.split("\n")[:4]
    start_y = HEIGHT // 2 - 150
    for i, txt in enumerate(spec_lines):
        alpha = int(255 * min(1, max(0, (t - 0.5 - i * 0.2) * 2)))
        if alpha <= 0: continue
        y = start_y + i * spec_spacing
        card = Image.new("RGBA", (320, 70), (*WHITE, alpha // 2))
        canvas.paste(card, (spec_xy[0] - 20, y - 10), card)
        txt_img = text_box(txt, font_spec, (*TEXT_COLOUR, alpha))
        canvas.paste(txt_img, (spec_xy[0], y), txt_img)

    # price (pulse)
    pulse = 1 + 0.05 * math.sin(t * 3)
    pw, ph = int(price_size[0] * pulse), int(price_size[1] * pulse)
    px = (WIDTH - pw) // 2 + price_xy[0]
    py = price_xy[1] + (price_size[1] - ph) // 2
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((px, py, px + pw, py + ph), radius=25, fill=ACCENT)
    price_img = text_box(price, get_font(price_font), WHITE)
    canvas.paste(price_img,
                (px + (pw - price_img.width) // 2,
                 py + (ph - price_img.height) // 2),
                price_img)

    # cta
    cta_img = text_box("SHOP NOW", get_font(cta_font), WHITE)
    canvas.paste(cta_img,
                (cta_xy[0] + (cta_size[0] - cta_img.width) // 2,
                 cta_xy[1] + (cta_size[1] - cta_img.height) // 2),
                cta_img)

    # website
    web_img = text_box("www.tripplek.co.ke", get_font(32, bold=False), TEXT_COLOUR)
    canvas.paste(web_img,
                ((WIDTH - web_img.width) // 2, HEIGHT - 50),
                web_img)

    # CPU → GPU for premium filters
    gpu = cv2.cuda_GpuMat()
    gpu.upload(np.asarray(canvas))
    gpu = chromatic_aberration_gpu(gpu, amount=1.5)
    gpu = film_grain_gpu(gpu, intensity=0.02)
    return gpu.download()

# --------------------------------------------------------
# STREAMING GPU ENCODER  (H.265 2-pass)
# --------------------------------------------------------
def build_video(product, specs, price, ui):
    # pass-1 log file
    pass1_log = tempfile.mktemp(suffix=".log")
    tmp1 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp1.close()

    # pass-1 (fast)
    cmd1 = [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "bgr24", "-r", str(FPS), "-i", "-",
        "-c:v", "libx265", "-b:v", "2M", "-pass", "1", "-passlogfile", pass1_log,
        "-preset", "fast", "-an", "-f", "mp4", tmp1.name
    ]
    bar = st.progress(0)
    proc1 = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for i in range(TOTAL_FRAMES):
        frame = draw_frame(i / FPS, product, specs, price, **ui)
        proc1.stdin.write(frame.tobytes())
        bar.progress((i + 1) / TOTAL_FRAMES)
    proc1.stdin.close()
    proc1.wait()

    # pass-2 (final)
    tmp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp2.close()
    audio_path = download(AUDIO_URL, ".mp3")
    audio_cmd = ["-i", audio_path, "-c:a", "aac", "-b:a", "128k"] if audio_path else ["-an"]
    cmd2 = [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "bgr24", "-r", str(FPS), "-i", "-",
        "-i", audio_path, "-c:v", "libx265", "-b:v", "2M", "-pass", "2",
        "-passlogfile", pass1_log, "-preset", "slow", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", tmp2.name
    ] if audio_path else [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "bgr24", "-r", str(FPS), "-i", "-",
        "-c:v", "libx265", "-b:v", "2M", "-pass", "2", "-passlogfile", pass1_log,
        "-preset", "slow", "-movflags", "+faststart", "-an", tmp2.name
    ]
    proc2 = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for i in range(TOTAL_FRAMES):
        frame = draw_frame(i / FPS, product, specs, price, **ui)
        proc2.stdin.write(frame.tobytes())
    proc2.stdin.close()
    proc2.wait()

    os.remove(tmp1.name)
    os.remove(pass1_log)
    return tmp2.name

# --------------------------------------------------------
# UI  (same sliders as before)
# --------------------------------------------------------
st.set_page_config(page_title="TrippleK Ad Studio", layout="centered")
st.title("📱 TrippleK Premium Ad Generator")
st.caption("GPU render • H.265 • Spring motion • Film grain • 2-pass encode")

# Sidebar sliders (identical to previous answer – kept short)
with st.sidebar:
    product = st.text_input("Phone Name", "iPhone 16e")
    specs   = st.text_area("Specs (1 per line)",
                          "A18 Bionic Chip\n48 MP Camera\n256 GB Storage\n20 % Off",
                          height=120)
    price   = st.text_input("Price text", "KSh 145,000")

    st.subheader("🎚️ Layout Sliders")
    logo_w  = st.slider("Logo width", 200, 600, 420, 10)
    logo_h  = st.slider("Logo height", 60, 200, 100, 10)
    logo_x  = st.slider("Logo X", 0, 300, 60, 10)
    logo_y  = st.slider("Logo Y", 0, 300, 60, 10)
    head_size = st.slider("Headline font size", 40, 120, 90, 2)
    head_x    = st.slider("Headline X offset", -200, 200, 0, 10)
    head_y    = st.slider("Headline Y", 150, 400, 220, 10)
    prod_w = st.slider("Product width", 400, 900, 650, 10)
    prod_h = st.slider("Product height", 600, 1000, 900, 10)
    prod_x = st.slider("Product X offset", -200, 200, 0, 10)
    prod_y = st.slider("Product Y", 200, 700, 450, 10)
    spec_size = st.slider("Spec font size", 20, 80, 42, 2)
    spec_x    = st.slider("Spec X", 0, 900, 750, 10)
    spec_y_off= st.slider("Spec Y offset from middle", -200, 200, 0, 10)
    spec_gap  = st.slider("Spec line gap", 50, 150, 90, 10)
    price_w = st.slider("Price tag width", 200, 500, 300, 10)
    price_h = st.slider("Price tag height", 50, 150, 90, 10)
    price_x = st.slider("Price X offset", -200, 200, 0, 10)
    price_y = st.slider("Price Y", HEIGHT - 400, HEIGHT - 100, HEIGHT - 210, 10)
    price_font = st.slider("Price font size", 20, 100, 48, 2)
    cta_w  = st.slider("CTA width", 200, 600, 350, 10)
    cta_h  = st.slider("CTA height", 40, 120, 80, 10)
    cta_x  = st.slider("CTA X", 0, 500, 60, 10)
    cta_y  = st.slider("CTA Y", HEIGHT - 300, HEIGHT - 100, HEIGHT - 180, 10)
    cta_font = st.slider("CTA font size", 20, 100, 46, 2)

    # voice-over upload (premium)
    voice = st.file_uploader("Upload voice-over (optional)", type=["mp3", "wav"])
    export = st.button("🚀 Generate Premium MP4", type="primary", use_container_width=True)

# Pack UI
ui_pack = {
    "logo_size": (logo_w, logo_h),
    "logo_xy": (logo_x, logo_y),
    "product_size": (prod_w, prod_h),
    "product_xy": (prod_x, prod_y),
    "headline_size": head_size,
    "headline_xy": (head_x, head_y),
    "spec_size": (320, spec_size),
    "spec_xy": (spec_x, HEIGHT // 2 - 150 + spec_y_off),
    "spec_spacing": spec_gap,
    "price_size": (price_w, price_h),
    "price_xy": (price_x, price_y),
    "price_font": price_font,
    "cta_size": (cta_w, cta_h),
    "cta_xy": (cta_x, cta_y),
    "cta_font": cta_font
}

# Main preview / export
if export:
    if not product.strip():
        st.error("Add a product name!")
        st.stop()
    with st.spinner("GPU rendering + 2-pass encode..."):
        path = build_video(product, specs, price, ui_pack)
    st.success("✅ Premium ad ready!")
    with open(path, "rb") as f:
        st.download_button("⬇️ Download MP4", f, file_name="TrippleK_Premium.mp4", use_container_width=True)
    st.video(path)
    try:
        os.remove(path)
    except:
        pass
    gc.collect()
else:
    preview = np.asarray(draw_frame(1.0, product, specs, price, **ui_pack))
    st.image(preview, use_column_width=True)
