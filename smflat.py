import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, math, time, random
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# PREMIUM MODERN DESIGN SYSTEM
# ============================================================================
st.set_page_config(
    page_title="Still Mind Pro",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium themes with modern color psychology
THEMES = {
    "Nordic Calm": {
        "primary": (88, 86, 214, 255),      # Vibrant Purple
        "secondary": (45, 212, 191, 255),   # Turquoise
        "accent": (255, 107, 107, 255),     # Coral
        "bg_gradient_top": (15, 23, 42, 255),    # Deep Navy
        "bg_gradient_bottom": (30, 41, 59, 255),  # Slate
        "surface": (51, 65, 85, 255),       # Card BG
        "text": (248, 250, 252, 255),       # Off-white
        "text_secondary": (203, 213, 225, 255),
        "glow": (139, 92, 246, 100)         # Purple glow
    },
    "Golden Hour": {
        "primary": (251, 191, 36, 255),     # Amber
        "secondary": (249, 115, 22, 255),   # Orange
        "accent": (236, 72, 153, 255),      # Pink
        "bg_gradient_top": (17, 24, 39, 255),
        "bg_gradient_bottom": (31, 41, 55, 255),
        "surface": (55, 65, 81, 255),
        "text": (254, 252, 232, 255),
        "text_secondary": (253, 230, 138, 255),
        "glow": (251, 191, 36, 100)
    },
    "Ocean Deep": {
        "primary": (34, 211, 238, 255),     # Cyan
        "secondary": (59, 130, 246, 255),   # Blue
        "accent": (168, 85, 247, 255),      # Purple
        "bg_gradient_top": (3, 7, 18, 255),
        "bg_gradient_bottom": (15, 23, 42, 255),
        "surface": (30, 41, 59, 255),
        "text": (240, 249, 255, 255),
        "text_secondary": (186, 230, 253, 255),
        "glow": (34, 211, 238, 100)
    },
    "Forest Zen": {
        "primary": (52, 211, 153, 255),     # Emerald
        "secondary": (134, 239, 172, 255),  # Green
        "accent": (251, 191, 36, 255),      # Gold
        "bg_gradient_top": (6, 20, 15, 255),
        "bg_gradient_bottom": (20, 40, 30, 255),
        "surface": (34, 60, 50, 255),
        "text": (236, 253, 245, 255),
        "text_secondary": (167, 243, 208, 255),
        "glow": (52, 211, 153, 100)
    }
}

SIZES = {
    "Instagram Post (1080x1080)": (1080, 1080),
    "Instagram Story (1080x1920)": (1080, 1920),
    "YouTube Thumbnail (1920x1080)": (1920, 1080),
    "TikTok (1080x1920)": (1080, 1920),
    "Twitter Post (1200x675)": (1200, 675),
    "Facebook Post (1200x630)": (1200, 630)
}

# ============================================================================
# ADVANCED VISUAL EFFECTS
# ============================================================================
def create_gradient_background(w, h, colors):
    """Create smooth gradient with noise texture."""
    img = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(img)
    
    # Diagonal gradient
    for y in range(h):
        ratio = y / h
        # Smooth color interpolation
        r = int(colors["bg_gradient_top"][0] * (1-ratio) + colors["bg_gradient_bottom"][0] * ratio)
        g = int(colors["bg_gradient_top"][1] * (1-ratio) + colors["bg_gradient_bottom"][1] * ratio)
        b = int(colors["bg_gradient_top"][2] * (1-ratio) + colors["bg_gradient_bottom"][2] * ratio)
        draw.rectangle([(0, y), (w, y+1)], fill=(r, g, b, 255))
    
    # Add subtle noise texture
    noise = np.random.normal(0, 5, (h, w, 4))
    noise[:,:,3] = 0  # Keep alpha channel
    noise_img = Image.fromarray(noise.astype('uint8'), 'RGBA')
    img = Image.alpha_composite(img, noise_img)
    
    return img

def draw_glowing_orbs(draw, w, h, t, colors, count=8):
    """Draw animated glowing orbs with motion blur effect."""
    for i in range(count):
        # Parametric circular motion
        angle = (t * 0.3 + i * (2 * math.pi / count)) % (2 * math.pi)
        radius_orbit = min(w, h) * 0.35
        
        cx = w/2 + radius_orbit * math.cos(angle) * 0.8
        cy = h/2 + radius_orbit * math.sin(angle) * 0.6
        
        # Size variation
        size = 40 + 30 * math.sin(t * 2 + i)
        
        # Multi-layer glow effect
        for layer in range(5):
            layer_size = size * (1 + layer * 0.4)
            alpha = int(40 / (layer + 1))
            
            color = colors["primary"] if i % 2 == 0 else colors["secondary"]
            glow_color = color[:3] + (alpha,)
            
            draw.ellipse([cx - layer_size, cy - layer_size,
                         cx + layer_size, cy + layer_size],
                        fill=glow_color)

def draw_geometric_grid(draw, w, h, t, colors):
    """Draw animated geometric grid with depth."""
    grid_size = 60
    line_width = 2
    
    # Perspective grid
    for x in range(0, w, grid_size):
        # Animate opacity based on time
        alpha = int(30 + 20 * math.sin(t + x/100))
        color = colors["text_secondary"][:3] + (alpha,)
        
        # Vertical lines with wave
        offset = math.sin(t * 2 + x/100) * 10
        draw.line([(x, 0), (x + offset, h)], fill=color, width=line_width)
    
    for y in range(0, h, grid_size):
        alpha = int(30 + 20 * math.cos(t + y/100))
        color = colors["text_secondary"][:3] + (alpha,)
        
        # Horizontal lines with wave
        offset = math.cos(t * 2 + y/100) * 10
        draw.line([(0, y), (w, y + offset)], fill=color, width=line_width)

def draw_floating_particles(draw, w, h, t, colors, count=30):
    """Draw floating particle system."""
    for i in range(count):
        # Unique motion path for each particle
        seed = i * 123.456
        x = (w * 0.2 + (t * 50 + seed * 10) % (w * 0.6))
        y = (h * 0.1 + ((t * 30 + seed * 5) % (h * 0.8)))
        
        # Add sine wave motion
        x += math.sin(t * 3 + i) * 20
        y += math.cos(t * 2 + i) * 15
        
        # Varying sizes
        size = 3 + (i % 5)
        
        # Pulsing alpha
        alpha = int(100 + 100 * math.sin(t * 4 + i))
        color = colors["accent"][:3] + (alpha,)
        
        # Draw particle with glow
        draw.ellipse([x-size*2, y-size*2, x+size*2, y+size*2],
                    fill=colors["accent"][:3] + (50,))
        draw.ellipse([x-size, y-size, x+size, y+size], fill=color)

def draw_premium_panel(draw, w, h, colors):
    """Draw glassmorphism-style panel with shadows."""
    panel_w = int(w * 0.75)
    panel_h = int(h * 0.55)
    px = (w - panel_w) // 2
    py = (h - panel_h) // 2 - 30
    
    corner_radius = 30
    
    # Shadow layers
    for offset in range(20, 0, -4):
        shadow_alpha = int(10 * (20 - offset) / 20)
        shadow_color = (0, 0, 0, shadow_alpha)
        
        draw.rounded_rectangle(
            [px + offset//2, py + offset//2, 
             px + panel_w + offset//2, py + panel_h + offset//2],
            radius=corner_radius,
            fill=shadow_color
        )
    
    # Glassmorphism panel
    panel_color = colors["surface"][:3] + (240,)
    draw.rounded_rectangle(
        [px, py, px + panel_w, py + panel_h],
        radius=corner_radius,
        fill=panel_color
    )
    
    # Gradient border
    border_width = 3
    for i in range(border_width):
        alpha = int(255 * (border_width - i) / border_width)
        border_color = colors["primary"][:3] + (alpha,)
        
        draw.rounded_rectangle(
            [px + i, py + i, px + panel_w - i, py + panel_h - i],
            radius=corner_radius,
            outline=border_color,
            width=1
        )
    
    # Accent gradient bar
    accent_h = 8
    draw.rectangle([px, py, px + panel_w, py + accent_h], 
                   fill=colors["primary"])
    
    return px, py, panel_w, panel_h

# ============================================================================
# PREMIUM TYPOGRAPHY
# ============================================================================
def load_premium_font(size, weight="regular"):
    """Load premium fonts with fallback."""
    font_map = {
        "bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica-Bold.ttc",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/ariblk.ttf"
        ],
        "regular": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ],
        "light": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf",
            "/System/Library/Fonts/Helvetica-Light.ttc",
            "C:/Windows/Fonts/segoeuil.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
    }
    
    for path in font_map.get(weight, font_map["regular"]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    
    return ImageFont.load_default(size)

def draw_text_with_glow(draw, pos, text, font, color, glow_color):
    """Draw text with multi-layer glow effect."""
    x, y = pos
    
    # Outer glow layers
    for offset in range(8, 0, -2):
        alpha = int(glow_color[3] * (8 - offset) / 8)
        layer_color = glow_color[:3] + (alpha,)
        
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    draw.text((x+dx, y+dy), text, font=font, fill=layer_color)
    
    # Main text
    draw.text((x, y), text, font=font, fill=color)

def wrap_text_smart(text, font, max_width, max_lines=4):
    """Smart text wrapping with optimal line breaks."""
    words = text.split()
    lines = []
    current = []
    
    for word in words:
        test = ' '.join(current + [word])
        
        try:
            bbox = font.getbbox(test)
            width = bbox[2] - bbox[0]
        except:
            width = font.getsize(test)[0]
        
        if width <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
            
            if len(lines) >= max_lines:
                break
    
    if current and len(lines) < max_lines:
        lines.append(' '.join(current))
    
    return lines

# ============================================================================
# MAIN IMAGE GENERATION
# ============================================================================
def create_premium_image(w, h, theme, book, chapter, verse, hook, t=0, video=False):
    """Generate premium modern design."""
    colors = THEMES[theme]
    
    # Background with gradient
    img = create_gradient_background(w, h, colors)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Visual effects layers
    draw_geometric_grid(draw, w, h, t, colors)
    draw_glowing_orbs(draw, w, h, t, colors)
    draw_floating_particles(draw, w, h, t, colors)
    
    # Main content panel
    px, py, pw, ph = draw_premium_panel(draw, w, h, colors)
    
    # Load fonts
    title_font = load_premium_font(int(h * 0.055), "bold")
    verse_font = load_premium_font(int(h * 0.032), "regular")
    ref_font = load_premium_font(int(h * 0.038), "bold")
    brand_font = load_premium_font(int(h * 0.025), "light")
    
    # Draw hook/title with glow
    if hook:
        hook_upper = hook.upper()
        
        try:
            bbox = title_font.getbbox(hook_upper)
            hook_w = bbox[2] - bbox[0]
        except:
            hook_w = title_font.getsize(hook_upper)[0]
        
        hook_x = px + (pw - hook_w) // 2
        hook_y = py - int(h * 0.08)
        
        draw_text_with_glow(
            draw, (hook_x, hook_y), hook_upper,
            title_font, colors["primary"], colors["glow"]
        )
    
    # Verse text with typewriter effect
    verse_text = "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth."
    
    if video:
        progress = min(1.0, t / 4.0)
        visible = verse_text[:int(len(verse_text) * progress)]
    else:
        visible = verse_text
    
    # Wrap and draw verse
    max_text_w = pw - int(w * 0.08)
    lines = wrap_text_smart(visible, verse_font, max_text_w)
    
    line_spacing = int(h * 0.045)
    text_y = py + int(ph * 0.25)
    
    for line in lines:
        try:
            bbox = verse_font.getbbox(line)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = verse_font.getsize(line)[0]
        
        line_x = px + (pw - line_w) // 2
        
        # Subtle shadow
        shadow_offset = 3
        draw.text((line_x + shadow_offset, text_y + shadow_offset), 
                 line, font=verse_font, 
                 fill=(0, 0, 0, 80))
        
        # Main text
        alpha = 255 if not video else int(255 * progress)
        draw.text((line_x, text_y), line, 
                 font=verse_font, fill=colors["text"][:3] + (alpha,))
        
        text_y += line_spacing
    
    # Reference with accent background
    reference = f"{book} {chapter}:{verse}"
    
    try:
        bbox = ref_font.getbbox(reference)
        ref_w = bbox[2] - bbox[0]
        ref_h = bbox[3] - bbox[1]
    except:
        ref_w, ref_h = ref_font.getsize(reference)
    
    ref_x = px + pw - ref_w - int(w * 0.04)
    ref_y = py + ph + int(h * 0.05)
    
    ref_alpha = 255 if not video else int(255 * max(0, (t - 3) / 1))
    
    if ref_alpha > 0:
        # Accent pill background
        pill_padding = int(w * 0.02)
        pill_radius = int(ref_h * 0.6)
        
        draw.rounded_rectangle(
            [ref_x - pill_padding, ref_y - pill_padding//2,
             ref_x + ref_w + pill_padding, ref_y + ref_h + pill_padding//2],
            radius=pill_radius,
            fill=colors["primary"]
        )
        
        draw.text((ref_x, ref_y), reference, 
                 font=ref_font, fill=colors["bg_gradient_top"])
    
    # Brand watermark
    brand = "STILL MIND"
    
    try:
        bbox = brand_font.getbbox(brand)
        brand_w = bbox[2] - bbox[0]
    except:
        brand_w = brand_font.getsize(brand)[0]
    
    brand_x = px + int(w * 0.03)
    brand_y = py + ph + int(h * 0.05)
    
    draw.text((brand_x, brand_y), brand, 
             font=brand_font, fill=colors["text_secondary"][:3] + (180,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_premium_video(w, h, theme, book, chapter, verse, hook):
    """Create premium animated video."""
    duration = 8
    fps = 30
    
    def make_frame(t):
        img = create_premium_image(w, h, theme, book, chapter, verse, hook, t, True)
        return np.array(img.convert("RGB"))
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
        temp_path = f.name
    
    try:
        clip.write_videofile(
            temp_path, fps=fps, codec="libx264",
            audio_codec="aac", verbose=False, logger=None,
            bitrate="8000k"
        )
        
        with open(temp_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        color: white; border: none; padding: 0.75rem 2rem;
        border-radius: 12px; font-weight: 600;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(139,92,246,0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(139,92,246,0.6);
    }
    .css-1d391kg { background: #1e293b; border-radius: 12px; padding: 1.5rem; }
    h1 { background: linear-gradient(135deg, #8b5cf6, #06b6d4);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent;
         font-size: 3rem !important; font-weight: 800; }
    .stMetric { background: rgba(139,92,246,0.1); padding: 1rem;
                border-radius: 8px; border-left: 4px solid #8b5cf6; }
</style>
""", unsafe_allow_html=True)

st.title("✨ Still Mind Pro")
st.markdown("### Premium Social Media Content • Viral-Ready Designs")

# Sidebar
with st.sidebar:
    st.markdown("## 🎨 Design Studio")
    
    theme = st.selectbox("Premium Theme", list(THEMES.keys()), 
                        help="Select visual mood")
    size_key = st.selectbox("Platform", list(SIZES.keys()),
                           help="Optimized for each platform")
    w, h = SIZES[size_key]
    
    st.markdown("---")
    st.markdown("## 📝 Content")
    
    hook = st.text_input("Headline", "FIND YOUR PEACE",
                        help="Attention-grabbing hook")
    
    books = ["Psalm", "Proverbs", "Isaiah", "Matthew", "John", 
            "Romans", "Philippians", "James", "Ecclesiastes", "Luke"]
    book = st.selectbox("Book", books)
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Ch.", 1, 150, 46, help="Chapter")
    with col2:
        verse = st.number_input("V.", 1, 176, 10, help="Verse")
    
    st.markdown("---")
    st.markdown("## ⚙️ Settings")
    
    quality = st.select_slider("Export Quality", 
                               ["Good", "High", "Ultra"], value="Ultra")
    
    st.markdown("---")
    time_t = st.slider("Preview Animation", 0.0, 8.0, 0.0, 0.1,
                      help="Scrub through animation")

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 🖼️ Live Preview")
    
    with st.spinner("Rendering premium design..."):
        preview = create_premium_image(w, h, theme, book, chapter, verse, hook, time_t, False)
    
    st.image(preview, use_column_width=True)
    
    # Actions
    col_a, col_b = st.columns(2)
    
    with col_a:
        buf = io.BytesIO()
        preview.save(buf, format='PNG', optimize=True, quality=95)
        
        st.download_button(
            "📥 Download Image",
            buf.getvalue(),
            f"stillmind_{book}_{chapter}_{verse}.png",
            "image/png",
            use_container_width=True
        )
    
    with col_b:
        if st.button("🎬 Create Video (8s)", use_container_width=True):
            with st.spinner("Rendering animation..."):
                video = create_premium_video(w, h, theme, book, chapter, verse, hook)
                
                if video:
                    st.video(video)
                    st.download_button(
                        "📥 Download Video",
                        video,
                        f"stillmind_{book}_{chapter}_{verse}.mp4",
                        "video/mp4",
                        use_column_width=True
                    )

with col2:
    st.markdown("### 📊 Stats")
    
    st.metric("Resolution", f"{w}×{h}")
    st.metric("Aspect Ratio", f"{w//120}:{h//120}")
    st.metric("Theme", theme)
    
    st.markdown("---")
    st.markdown("### ✨ Features")
    
    features = [
        "🎨 Glassmorphism UI",
        "✨ Animated Particles",
        "🌟 Glowing Orbs",
        "📐 Geometric Grid",
        "🎭 Smooth Gradients",
        "💫 Motion Effects"
    ]
    
    for feat in features:
        st.markdown(f"**{feat}**")
    
    st.markdown("---")
    st.markdown("### 🎯 Best Practices")
    
    tips = {
        "Instagram": "Use 1080x1080 or Stories format",
        "TikTok": "Vertical 1080x1920 performs best",
        "YouTube": "Thumbnail should be eye-catching",
        "Twitter": "Keep text minimal and bold"
    }
    
    for platform, tip in tips.items():
        st.info(f"**{platform}**: {tip}")

st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: rgba(139,92,246,0.1); 
            border-radius: 12px; margin-top: 2rem;'>
    <h4 style='color: #8b5cf6; margin-bottom: 0.5rem;'>✨ Premium Content Generation</h4>
    <p style='color: #94a3b8;'>Modern • Professional • Viral-Ready</p>
</div>
""", unsafe_allow_html=True)