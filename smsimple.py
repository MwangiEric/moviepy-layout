import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, math, time, random, textwrap
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# MODERN FLAT DESIGN SYSTEM
# ============================================================================
st.set_page_config(
    page_title="Still Mind Modern",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Flat design color palettes inspired by examples
THEMES = {
    "Minimal Navy": {
        "primary": (10, 25, 45, 255),        # Deep Navy (from examples)
        "secondary": (76, 175, 80, 255),     # Emerald Green
        "accent": (255, 195, 0, 255),        # Gold/Yellow
        "text": (255, 255, 255, 255),        # Pure White
        "background": (20, 40, 70, 255),     # Blue-Grey
        "surface": (30, 50, 90, 255),        # Lighter Navy
        "border": 3                          # Thin border
    },
    "Clean White": {
        "primary": (255, 255, 255, 255),     # Pure White
        "secondary": (10, 25, 45, 255),      # Navy Blue
        "accent": (230, 57, 70, 255),        # Red Accent
        "text": (10, 25, 45, 255),           # Navy Text
        "background": (245, 245, 245, 255),  # Light Grey
        "surface": (255, 255, 255, 255),     # White surface
        "border": 4
    },
    "Warm Beige": {
        "primary": (245, 229, 208, 255),     # Warm Beige
        "secondary": (118, 68, 138, 255),    # Purple
        "accent": (46, 196, 182, 255),       # Teal
        "text": (40, 30, 20, 255),           # Dark Brown
        "background": (255, 250, 240, 255),  # Off-white
        "surface": (235, 219, 188, 255),     # Beige surface
        "border": 3
    }
}

# Font styles
FONT_STYLES = {
    "Bold Sans": {"family": "DejaVuSans-Bold.ttf", "spacing": 1.0},
    "Clean Serif": {"family": "DejaVuSerif.ttf", "spacing": 1.1},
    "Modern Mono": {"family": "DejaVuSansMono.ttf", "spacing": 1.2},
    "Light Sans": {"family": "DejaVuSans-ExtraLight.ttf", "spacing": 1.0}
}

# Layout templates inspired by examples
LAYOUTS = {
    "Centered Text": {
        "title_pos": "center",
        "verse_pos": "center",
        "ref_pos": "bottom_right",
        "brand_pos": "bottom_left"
    },
    "Left Aligned": {
        "title_pos": "left",
        "verse_pos": "left",
        "ref_pos": "right",
        "brand_pos": "bottom_center"
    },
    "Top Heavy": {
        "title_pos": "top_center",
        "verse_pos": "center",
        "ref_pos": "bottom_center",
        "brand_pos": "bottom_right"
    }
}

# ============================================================================
# FONT MANAGEMENT
# ============================================================================
@st.cache_resource
def load_font_safe(font_name, size):
    """Load font with multiple fallback options."""
    font_config = FONT_STYLES.get(font_name, FONT_STYLES["Bold Sans"])
    font_family = font_config["family"]
    
    font_paths = [
        f"/usr/share/fonts/truetype/dejavu/{font_family}",
        f"/System/Library/Fonts/{font_family.replace('.ttf', '.ttc')}",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/cour.ttf"
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    
    # Ultimate fallback
    return ImageFont.load_default(size)

# ============================================================================
# TEXT LAYOUT ENGINE
# ============================================================================
def calculate_text_layout(text, font, max_width, max_height, line_spacing=1.2):
    """Calculate how to fit text within boundaries."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line) if hasattr(font, 'getbbox') else font.getsize(test_line)
        text_width = bbox[2] - bbox[0] if hasattr(font, 'getbbox') else bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Calculate total height
    if hasattr(font, 'getbbox'):
        line_height = font.getbbox("A")[3] * line_spacing
    else:
        line_height = font.getsize("A")[1] * line_spacing
    
    total_height = len(lines) * line_height
    
    return lines, line_height, total_height

def draw_text_block(draw, lines, font, position, color, line_height, align="center", max_width=None):
    """Draw a block of text with specified alignment."""
    x, y = position
    
    for i, line in enumerate(lines):
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
        else:
            line_width = font.getsize(line)[0]
        
        if align == "center":
            line_x = x - line_width // 2
        elif align == "right":
            line_x = x - line_width
        else:  # left
            line_x = x
        
        draw.text((line_x, y + i * line_height), line, font=font, fill=color)
    
    return y + len(lines) * line_height

# ============================================================================
# FLAT DESIGN ELEMENTS
# ============================================================================
def draw_geometric_background(draw, width, height, colors, style="solid"):
    """Draw modern flat background."""
    if style == "gradient":
        # Simple vertical gradient
        for y in range(height):
            ratio = y / height
            r = int(colors["primary"][0] * (1 - ratio) + colors["background"][0] * ratio)
            g = int(colors["primary"][1] * (1 - ratio) + colors["background"][1] * ratio)
            b = int(colors["primary"][2] * (1 - ratio) + colors["background"][2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    else:
        # Solid color
        draw.rectangle([0, 0, width, height], fill=colors["primary"])

def draw_simple_ornaments(draw, width, height, colors):
    """Draw minimalist geometric ornaments like in examples."""
    # Top left ornament (corner)
    corner_size = 60
    draw.line([(40, 40), (40, 40 + corner_size)], fill=colors["accent"], width=3)
    draw.line([(40, 40), (40 + corner_size, 40)], fill=colors["accent"], width=3)
    
    # Bottom right ornament
    draw.line([(width - 40, height - 40), (width - 40, height - 40 - corner_size)], 
              fill=colors["accent"], width=3)
    draw.line([(width - 40, height - 40), (width - 40 - corner_size, height - 40)], 
              fill=colors["accent"], width=3)

def draw_modern_divider(draw, x1, y1, x2, y2, color, width=3, style="line"):
    """Draw modern divider lines."""
    if style == "dashed":
        # Dashed line
        dash_length = 20
        gap_length = 10
        current_x = x1
        while current_x < x2:
            draw.line([(current_x, y1), (min(current_x + dash_length, x2), y1)], 
                     fill=color, width=width)
            current_x += dash_length + gap_length
    else:
        # Solid line
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

# ============================================================================
# MAIN COMPOSITION ENGINE
# ============================================================================
def create_modern_flat_design(width, height, theme_name, layout_name, 
                            font_style, title_text, verse_text, reference, 
                            brand_text="", t=0, is_video=False):
    """Create a modern flat design composition."""
    colors = THEMES[theme_name]
    layout = LAYOUTS[layout_name]
    
    # Create image
    img = Image.new("RGBA", (width, height), colors["primary"])
    draw = ImageDraw.Draw(img)
    
    # Add subtle texture/noise for modern look
    if colors["primary"][0] < 100:  # Dark background
        noise = np.random.randint(0, 20, (height, width, 3), dtype=np.uint8)
        noise_img = Image.fromarray(noise, mode='RGB').convert('RGBA')
        noise_img.putalpha(3)  # Very subtle
        img = Image.alpha_composite(img, noise_img)
        draw = ImageDraw.Draw(img)
    
    # Draw background elements
    draw_geometric_background(draw, width, height, colors, "solid")
    draw_simple_ornaments(draw, width, height, colors)
    
    # Calculate text areas
    content_width = width - 160  # Margins
    content_height = height - 240
    
    # Load fonts
    title_font = load_font_safe(font_style, 72)
    verse_font = load_font_safe(font_style, 56)
    ref_font = load_font_safe(font_style, 42)
    brand_font = load_font_safe(font_style, 28)
    
    # Typewriter effect for verse
    if is_video:
        verse_duration = 5
        verse_progress = min(1.0, t / verse_duration)
        visible_verse = verse_text[:int(len(verse_text) * verse_progress)]
    else:
        verse_progress = 1.0
        visible_verse = verse_text
    
    # Layout calculations
    title_lines, title_line_height, title_total_height = calculate_text_layout(
        title_text, title_font, content_width, content_height // 4
    )
    
    verse_lines, verse_line_height, verse_total_height = calculate_text_layout(
        visible_verse, verse_font, content_width, content_height // 2
    )
    
    # Draw title based on layout
    if layout["title_pos"] == "center":
        title_y = height * 0.2
        draw_text_block(draw, title_lines, title_font, 
                       (width // 2, title_y), colors["secondary"], 
                       title_line_height, "center")
    elif layout["title_pos"] == "left":
        title_y = height * 0.15
        draw_text_block(draw, title_lines, title_font, 
                       (80, title_y), colors["secondary"], 
                       title_line_height, "left")
    else:  # top_center
        title_y = 80
        draw_text_block(draw, title_lines, title_font, 
                       (width // 2, title_y), colors["secondary"], 
                       title_line_height, "center")
    
    # Draw divider after title
    if layout["title_pos"] == "center":
        divider_y = title_y + title_total_height + 40
        draw_modern_divider(draw, width // 2 - 100, divider_y, 
                           width // 2 + 100, divider_y, 
                           colors["accent"], 3, "line")
    
    # Draw verse text
    if layout["verse_pos"] == "center":
        verse_y = height // 2 - verse_total_height // 2
        
        # Fade in effect for video
        verse_alpha = int(255 * verse_progress) if is_video else 255
        verse_color = colors["text"][:3] + (verse_alpha,)
        
        draw_text_block(draw, verse_lines, verse_font,
                       (width // 2, verse_y), verse_color,
                       verse_line_height, "center")
    
    elif layout["verse_pos"] == "left":
        verse_y = height * 0.4
        verse_alpha = int(255 * verse_progress) if is_video else 255
        verse_color = colors["text"][:3] + (verse_alpha,)
        
        draw_text_block(draw, verse_lines, verse_font,
                       (80, verse_y), verse_color,
                       verse_line_height, "left")
    
    # Draw reference
    if reference:
        ref_lines, ref_line_height, ref_total_height = calculate_text_layout(
            reference, ref_font, 300, 100
        )
        
        ref_alpha = 255 if not is_video else int(255 * max(0, min(1.0, (t - 4) / 1)))
        
        if ref_alpha > 0:
            if layout["ref_pos"] == "bottom_right":
                ref_x = width - 100
                ref_y = height - 120
                draw_text_block(draw, ref_lines, ref_font,
                              (ref_x, ref_y), colors["accent"],
                              ref_line_height, "right")
            
            elif layout["ref_pos"] == "bottom_center":
                ref_y = height - 100
                draw_text_block(draw, ref_lines, ref_font,
                              (width // 2, ref_y), colors["accent"],
                              ref_line_height, "center")
            
            else:  # right
                ref_x = width - 100
                ref_y = height * 0.8
                draw_text_block(draw, ref_lines, ref_font,
                              (ref_x, ref_y), colors["accent"],
                              ref_line_height, "right")
    
    # Draw brand text
    if brand_text:
        brand_alpha = 180
        if layout["brand_pos"] == "bottom_left":
            draw.text((60, height - 60), brand_text, 
                     font=brand_font, fill=colors["text"][:3] + (brand_alpha,))
        elif layout["brand_pos"] == "bottom_center":
            if hasattr(brand_font, 'getbbox'):
                bbox = brand_font.getbbox(brand_text)
                brand_width = bbox[2] - bbox[0]
            else:
                brand_width = brand_font.getsize(brand_text)[0]
            
            brand_x = (width - brand_width) // 2
            draw.text((brand_x, height - 60), brand_text,
                     font=brand_font, fill=colors["text"][:3] + (brand_alpha,))
        else:  # bottom_right
            if hasattr(brand_font, 'getbbox'):
                bbox = brand_font.getbbox(brand_text)
                brand_width = bbox[2] - bbox[0]
            else:
                brand_width = brand_font.getsize(brand_text)[0]
            
            brand_x = width - brand_width - 60
            draw.text((brand_x, height - 60), brand_text,
                     font=brand_font, fill=colors["text"][:3] + (brand_alpha,))
    
    # Add "Still Mind" watermark (subtle)
    watermark_font = load_font_safe(font_style, 24)
    draw.text((30, 30), "STILL MIND", 
             font=watermark_font, fill=colors["text"][:3] + (100,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_modern_video(width, height, theme_name, layout_name, font_style,
                       title_text, verse_text, reference, brand_text):
    """Create animated flat design video."""
    duration = 6
    fps = 24
    
    def make_frame(t):
        img = create_modern_flat_design(
            width, height, theme_name, layout_name, font_style,
            title_text, verse_text, reference, brand_text, t, True
        )
        return np.array(img.convert("RGB"))
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
    # Create temporary file
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_path = temp_file.name
    
    try:
        clip.write_videofile(
            temp_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        
        with open(temp_path, 'rb') as f:
            video_bytes = f.read()
        
        return video_bytes
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("✨ Still Mind: Modern Flat Design Studio")
st.markdown("### Clean typography • Bold colors • Minimalist layouts")

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        background-color: #2C3E50;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #1A252F;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1C2833, #2C3E50);
    }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 0.75rem;
    }
    .stSelectbox > div > div {
        font-size: 1rem;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🎨 Design Settings")
    
    # Theme selection
    theme_option = st.selectbox("Color Theme", list(THEMES.keys()))
    
    # Layout selection
    layout_option = st.selectbox("Layout Style", list(LAYOUTS.keys()))
    
    # Font selection
    font_option = st.selectbox("Font Style", list(FONT_STYLES.keys()))
    
    # Size selection
    size_options = {
        "Instagram (1080x1080)": (1080, 1080),
        "Stories (1080x1920)": (1080, 1920),
        "Desktop (1920x1080)": (1920, 1080),
        "Square (1200x1200)": (1200, 1200)
    }
    size_option = st.selectbox("Size Format", list(size_options.keys()))
    width, height = size_options[size_option]
    
    st.divider()
    
    st.header("📝 Content")
    
    # Title/Header
    st.subheader("Title Text")
    title_text = st.text_area("Title (use SHIFT+ENTER for line breaks)", 
                             "STILL\nMIND", height=100)
    
    # Verse text
    st.subheader("Main Text")
    verse_text = st.text_area("Verse/Quote (will be auto-wrapped)", 
                             "Be still, and know that I am God.\nI will be exalted among the nations,\nI will be exalted in the earth.",
                             height=150)
    
    # Reference
    st.subheader("Reference")
    reference = st.text_input("Bible Reference or Author", "PSALM 46:10")
    
    # Brand/Website
    brand_text = st.text_input("Brand/Website (optional)", "stillmind.com")
    
    st.divider()
    
    # Animation preview
    st.header("⏱️ Animation Preview")
    time_scrubber = st.slider("Time", 0.0, 6.0, 0.0, 0.1)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Preview section
    st.subheader("✨ Live Preview")
    
    with st.spinner("Creating modern design..."):
        preview_img = create_modern_flat_design(
            width, height, theme_option, layout_option, font_option,
            title_text, verse_text, reference, brand_text, time_scrubber, False
        )
    
    st.image(preview_img, use_column_width=True)
    
    # Action buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # Download PNG
        img_buffer = io.BytesIO()
        preview_img.save(img_buffer, format='PNG', optimize=True, quality=95)
        
        st.download_button(
            label="📥 Download PNG",
            data=img_buffer.getvalue(),
            file_name=f"modern_design_{theme_option.lower().replace(' ', '_')}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Create Motion Graphic", use_container_width=True):
            with st.spinner("Animating text reveal..."):
                video_data = create_modern_video(
                    width, height, theme_option, layout_option, font_option,
                    title_text, verse_text, reference, brand_text
                )
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"modern_motion_{theme_option.lower().replace(' ', '_')}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    # Design details panel
    st.subheader("🖼️ Design Details")
    
    # Show color palette
    colors = THEMES[theme_option]
    st.write("**Color Palette:**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.color_picker("Primary", 
                       value=f"#{colors['primary'][0]:02x}{colors['primary'][1]:02x}{colors['primary'][2]:02x}",
                       disabled=True)
    with col2:
        st.color_picker("Accent", 
                       value=f"#{colors['accent'][0]:02x}{colors['accent'][1]:02x}{colors['accent'][2]:02x}",
                       disabled=True)
    with col3:
        st.color_picker("Text", 
                       value=f"#{colors['text'][0]:02x}{colors['text'][1]:02x}{colors['text'][2]:02x}",
                       disabled=True)
    
    # Layout info
    st.write("**Layout:**")
    layout_info = LAYOUTS[layout_option]
    for key, value in layout_info.items():
        st.caption(f"{key.replace('_', ' ').title()}: {value}")
    
    # Font info
    st.write("**Typography:**")
    font_config = FONT_STYLES[font_option]
    st.caption(f"Font: {font_option}")
    st.caption(f"Spacing: {font_config['spacing']}")
    
    # Statistics
    st.write("**Image Stats:**")
    st.metric("Resolution", f"{width} × {height}")
    st.metric("Theme", theme_option)
    
    st.divider()
    
    # Social media caption generator
    st.subheader("📱 Social Media")
    
    caption = f"""{title_text}

{verse_text[:100]}...

{reference}

👉 {brand_text if brand_text else 'stillmind.com'}

#StillMind #Faith #Inspiration #Design #Typography"""
    
    st.text_area("Social Media Caption", caption, height=180)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Copied!")
    
    st.divider()
    
    # Quick templates
    st.subheader("⚡ Quick Templates")
    
    if st.button("Psalm 23 Template", use_container_width=True):
        st.session_state.title_text = "THE LORD\nIS MY\nSHEPHERD"
        st.session_state.verse_text = "I shall not want. He makes me lie down in green pastures, he leads me beside quiet waters, he refreshes my soul."
        st.session_state.reference = "PSALM 23:1-3"
        st.rerun()
    
    if st.button("Be Still Template", use_container_width=True):
        st.session_state.title_text = "BE\nSTILL"
        st.session_state.verse_text = "And know that I am God. I will be exalted among the nations, I will be exalted in the earth."
        st.session_state.reference = "PSALM 46:10"
        st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #7F8C8D; font-size: 0.9rem;'>
    <p>✨ Modern Flat Design Studio • Inspired by clean typography and minimalist aesthetics</p>
    <p>Create beautiful scripture graphics for social media, presentations, and personal use</p>
</div>
""", unsafe_allow_html=True)

# Cleanup temporary files
for file in os.listdir("."):
    if file.startswith("temp_") and file.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(file) > 300:  # 5 minutes old
                os.remove(file)
        except:
            pass