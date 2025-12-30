import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, math, time, random
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# FLAT DESIGN THEME SYSTEM
# ============================================================================
st.set_page_config(
    page_title="Still Mind Flat",
    page_icon="🟩",
    layout="wide",
    initial_sidebar_state="expanded"
)

THEMES = {
    "Emerald Forest": {
        "primary": (46, 204, 113, 255),    # Flat Emerald
        "primary_dark": (39, 174, 96, 255),
        "primary_light": (111, 226, 154, 255),
        "background": (26, 36, 48, 255),   # Deep Navy
        "surface": (52, 73, 94, 255),      # Slate Blue
        "text": (236, 240, 241, 255),      # Off-White
        "accent": (255, 195, 0, 255),      # Yellow accent
        "border": 6                        # Thick border width
    },
    "Sunset Minimal": {
        "primary": (255, 159, 67, 255),    # Orange
        "primary_dark": (230, 126, 34, 255),
        "primary_light": (255, 189, 89, 255),
        "background": (41, 128, 185, 255), # Blue
        "surface": (52, 152, 219, 255),
        "text": (245, 246, 250, 255),
        "accent": (255, 121, 121, 255),    # Coral
        "border": 5
    },
    "Midnight Purple": {
        "primary": (155, 89, 182, 255),    # Purple
        "primary_dark": (142, 68, 173, 255),
        "primary_light": (195, 155, 211, 255),
        "background": (44, 62, 80, 255),   # Dark Blue
        "surface": (52, 73, 94, 255),
        "text": (236, 240, 241, 255),
        "accent": (26, 188, 156, 255),     # Teal
        "border": 4
    }
}

SIZES = {
    "Mobile (1080x1920)": (1080, 1920),
    "Square (1080x1080)": (1080, 1080),
    "Desktop (1920x1080)": (1920, 1080),
    "Stories (1080x1350)": (1080, 1350)
}

# ============================================================================
# GEOMETRIC FLAT DESIGN ELEMENTS
# ============================================================================
def draw_geometric_sun(draw, w, h, t, colors):
    """Draw a flat geometric sun with rays."""
    sun_size = 80
    sun_x = w // 2
    sun_y = h * 0.25
    
    # Sun body (circle)
    draw.ellipse([sun_x - sun_size, sun_y - sun_size, 
                  sun_x + sun_size, sun_y + sun_size], 
                 fill=colors["primary_light"], 
                 outline=colors["text"], 
                 width=colors["border"])
    
    # Sun rays (geometric lines)
    ray_count = 8
    ray_length = 40
    
    for i in range(ray_count):
        angle = (i / ray_count) * (2 * math.pi) + t * 0.5
        start_x = sun_x + (sun_size + 5) * math.cos(angle)
        start_y = sun_y + (sun_size + 5) * math.sin(angle)
        end_x = start_x + ray_length * math.cos(angle)
        end_y = start_y + ray_length * math.sin(angle)
        
        draw.line([(start_x, start_y), (end_x, end_y)], 
                  fill=colors["primary"], 
                  width=colors["border"])

def draw_geometric_mountains(draw, w, h, colors):
    """Draw flat triangular mountains."""
    # Left mountain
    left_mountain = [
        (w * 0.2, h),
        (w * 0.4, h * 0.5),
        (w * 0.6, h)
    ]
    draw.polygon(left_mountain, 
                 fill=colors["surface"], 
                 outline=colors["text"], 
                 width=colors["border"])
    
    # Right mountain
    right_mountain = [
        (w * 0.5, h),
        (w * 0.7, h * 0.4),
        (w * 0.9, h)
    ]
    draw.polygon(right_mountain, 
                 fill=colors["surface"], 
                 outline=colors["text"], 
                 width=colors["border"])

def draw_geometric_trees(draw, w, h, t, colors):
    """Draw flat geometric trees."""
    tree_colors = [
        colors["primary"],
        colors["primary_dark"],
        colors["primary_light"]
    ]
    
    # Tree positions
    tree_positions = [
        (w * 0.2, h - 100),
        (w * 0.35, h - 80),
        (w * 0.5, h - 120),
        (w * 0.65, h - 90),
        (w * 0.8, h - 110)
    ]
    
    for i, (x, y) in enumerate(tree_positions):
        # Tree trunk
        trunk_height = 60 + i * 10
        trunk_width = 12
        
        draw.rectangle([x - trunk_width//2, y - trunk_height, 
                       x + trunk_width//2, y], 
                      fill=colors["surface"], 
                      outline=colors["text"], 
                      width=colors["border"]//2)
        
        # Tree crown (triangle for flat design)
        crown_size = 80 + i * 5
        crown = [
            (x, y - trunk_height - crown_size),
            (x - crown_size//2, y - trunk_height),
            (x + crown_size//2, y - trunk_height)
        ]
        
        tree_color = tree_colors[i % len(tree_colors)]
        draw.polygon(crown, 
                    fill=tree_color, 
                    outline=colors["text"], 
                    width=colors["border"])

def draw_geometric_birds(draw, w, h, t, colors):
    """Draw flat geometric bird shapes (V-shapes)."""
    bird_count = 5
    
    for i in range(bird_count):
        # Bird position with animation
        base_x = (t * 200 + i * 150) % (w + 200) - 100
        base_y = h * 0.3 + math.sin(t * 2 + i) * 30
        
        # Wing flap animation
        flap = math.sin(t * 10 + i) * 15
        
        # Draw flat V-shaped bird
        wing_length = 20 + i * 3
        
        # Left wing
        draw.line([(base_x, base_y), 
                  (base_x - wing_length, base_y - 15 + flap)], 
                 fill=colors["text"], 
                 width=colors["border"])
        
        # Right wing
        draw.line([(base_x, base_y), 
                  (base_x + wing_length, base_y - 15 + flap)], 
                 fill=colors["text"], 
                 width=colors["border"])

def draw_geometric_river(draw, w, h, t, colors):
    """Draw a flat geometric river."""
    river_points = [
        (w * 0.3, h * 0.7),
        (w * 0.4, h * 0.75),
        (w * 0.5, h * 0.7),
        (w * 0.6, h * 0.75),
        (w * 0.7, h * 0.7),
        (w * 0.7, h),
        (w * 0.3, h)
    ]
    
    # River body
    draw.polygon(river_points, 
                fill=colors["surface"], 
                outline=colors["text"], 
                width=colors["border"])
    
    # River waves (geometric lines)
    wave_count = 8
    for i in range(wave_count):
        wave_x = w * 0.3 + (i * (w * 0.4) / wave_count)
        wave_y = h * 0.85 + math.sin(t * 3 + i) * 10
        
        wave_length = 40
        draw.line([(wave_x, wave_y), 
                  (wave_x + wave_length, wave_y)], 
                 fill=colors["primary_light"], 
                 width=colors["border"]//2)

def draw_flat_ui_panel(draw, w, h, colors):
    """Draw a flat UI panel for text."""
    panel_width = 900
    panel_height = 550
    panel_x = (w - panel_width) // 2
    panel_y = (h - panel_height) // 2 - 50
    
    # Main panel
    draw.rectangle([panel_x, panel_y, 
                   panel_x + panel_width, panel_y + panel_height], 
                  fill=colors["background"], 
                  outline=colors["text"], 
                  width=colors["border"])
    
    # Accent bar on left
    accent_width = 20
    draw.rectangle([panel_x, panel_y, 
                   panel_x + accent_width, panel_y + panel_height], 
                  fill=colors["primary"])
    
    return panel_x, panel_y, panel_width, panel_height

def draw_geometric_elements(draw, w, h, t, colors):
    """Draw all geometric elements in flat design."""
    # Draw background elements
    draw_geometric_mountains(draw, w, h, colors)
    draw_geometric_sun(draw, w, h, t, colors)
    draw_geometric_river(draw, w, h, t, colors)
    draw_geometric_trees(draw, w, h, t, colors)
    draw_geometric_birds(draw, w, h, t, colors)

# ============================================================================
# TYPOGRAPHY & TEXT HANDLING
# ============================================================================
def load_flat_font(size, bold=False):
    """Load a font that works well with flat design."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf"
    ]
    
    if bold:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica-Bold.ttc",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf"
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    
    return ImageFont.load_default(size)

def wrap_text_flat(text, font, max_width):
    """Wrap text for flat design layout."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
        else:
            text_width = font.getsize(test_line)[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# ============================================================================
# MAIN IMAGE GENERATION
# ============================================================================
def create_flat_design_image(width, height, theme_name, book, chapter, verse, 
                            hook, t=0, is_video=False):
    """Create a flat design image with geometric elements."""
    colors = THEMES[theme_name]
    
    # Create base image
    img = Image.new("RGBA", (width, height), colors["background"])
    draw = ImageDraw.Draw(img)
    
    # Draw geometric elements
    draw_geometric_elements(draw, width, height, t, colors)
    
    # Draw UI panel
    panel_x, panel_y, panel_width, panel_height = draw_flat_ui_panel(
        draw, width, height, colors
    )
    
    # Load fonts
    title_font = load_flat_font(70, bold=True)
    verse_font = load_flat_font(48, bold=False)
    ref_font = load_flat_font(38, bold=True)
    brand_font = load_flat_font(32, bold=True)
    
    # Draw title/hook
    if hook:
        if hasattr(title_font, 'getbbox'):
            bbox = title_font.getbbox(hook.upper())
            title_width = bbox[2] - bbox[0]
        else:
            title_width = title_font.getsize(hook.upper())[0]
        
        title_x = panel_x + (panel_width - title_width) // 2
        title_y = panel_y - 100
        
        draw.text((title_x, title_y), hook.upper(), 
                 font=title_font, fill=colors["primary"])
    
    # Draw verse text
    verse_text = "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth."
    
    if is_video:
        typewriter_duration = 5
        typewriter_progress = min(1.0, t / typewriter_duration)
        visible_text = verse_text[:int(len(verse_text) * typewriter_progress)]
    else:
        visible_text = verse_text
    
    # Wrap verse text
    max_text_width = panel_width - 100
    lines = wrap_text_flat(visible_text, verse_font, max_text_width)
    
    # Draw verse lines
    line_height = 65
    text_y = panel_y + 100
    
    for line in lines:
        if hasattr(verse_font, 'getbbox'):
            bbox = verse_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
        else:
            line_width = verse_font.getsize(line)[0]
        
        line_x = panel_x + (panel_width - line_width) // 2
        
        # Text shadow for flat depth
        draw.text((line_x + 2, text_y + 2), line, 
                 font=verse_font, fill=(0, 0, 0, 100))
        
        # Main text
        text_alpha = int(255 * (1 if not is_video else typewriter_progress))
        draw.text((line_x, text_y), line, 
                 font=verse_font, fill=colors["text"][:3] + (text_alpha,))
        
        text_y += line_height
    
    # Draw reference
    reference = f"{book} {chapter}:{verse}"
    
    if hasattr(ref_font, 'getbbox'):
        bbox = ref_font.getbbox(reference)
        ref_width = bbox[2] - bbox[0]
    else:
        ref_width = ref_font.getsize(reference)[0]
    
    ref_x = panel_x + panel_width - ref_width - 50
    ref_y = panel_y + panel_height + 60
    
    ref_alpha = 255 if not is_video else int(255 * max(0, min(1.0, (t - 4) / 1)))
    
    if ref_alpha > 0:
        # Reference background block
        draw.rectangle([ref_x - 20, ref_y - 15, 
                       ref_x + ref_width + 20, ref_y + 45], 
                      fill=colors["primary"], 
                      outline=colors["text"], 
                      width=colors["border"]//2)
        
        # Reference text
        draw.text((ref_x, ref_y), reference, 
                 font=ref_font, fill=colors["text"])
    
    # Draw brand watermark
    brand_text = "STILL MIND FLAT"
    if hasattr(brand_font, 'getbbox'):
        bbox = brand_font.getbbox(brand_text)
        brand_width = bbox[2] - bbox[0]
    else:
        brand_width = brand_font.getsize(brand_text)[0]
    
    brand_x = panel_x + 50
    brand_y = panel_y + panel_height + 60
    
    draw.text((brand_x, brand_y), brand_text, 
             font=brand_font, fill=colors["text"][:3] + (180,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_flat_design_video(width, height, theme_name, book, chapter, verse, hook):
    """Create a flat design animation."""
    duration = 7  # seconds
    fps = 24
    
    def make_frame(t):
        img = create_flat_design_image(
            width, height, theme_name, book, chapter, verse, 
            hook, t, True
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
st.title("🟩 Still Mind: Flat Design Edition")
st.markdown("### Clean, geometric design with bold colors and minimalist aesthetics")

# Custom CSS for flat design
st.markdown("""
<style>
    .stButton > button {
        background-color: #2E86C1;
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #2874A6;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1C2833, #2C3E50);
    }
    .stSlider > div > div > div {
        background: #2E86C1;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🎨 Flat Design Settings")
    
    theme_option = st.selectbox("Color Theme", list(THEMES.keys()))
    size_option = st.selectbox("Size Format", list(SIZES.keys()))
    width, height = SIZES[size_option]
    
    st.header("📝 Content")
    hook = st.text_input("Header Text", "STILLNESS & STRENGTH")
    
    bible_books = ["Psalm", "Isaiah", "Matthew", "John", "Romans", 
                   "Philippians", "James", "Proverbs", "Ecclesiastes"]
    book = st.selectbox("Book", bible_books)
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 23)
    with col2:
        verse = st.number_input("Verse", 1, 176, 1)
    
    st.header("⏱️ Animation")
    time_scrubber = st.slider("Animation Time", 0.0, 7.0, 0.0, 0.1)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Preview
    st.subheader("🟩 Design Preview")
    
    with st.spinner("Creating flat design..."):
        preview_img = create_flat_design_image(
            width, height, theme_option, book, chapter, verse, 
            hook, time_scrubber, False
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
            file_name=f"flat_design_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Create Flat Animation (7s)", use_container_width=True):
            with st.spinner("Animating geometric elements..."):
                video_data = create_flat_design_video(
                    width, height, theme_option, book, chapter, verse, hook
                )
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download button
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"flat_design_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    # Info panel
    st.subheader("📐 Design Elements")
    
    st.write("**Flat Design Features:**")
    st.success("✓ Geometric Shapes Only")
    st.success("✓ Bold, Solid Colors")
    st.success("✓ Thick Borders")
    st.success("✓ Minimalist Aesthetics")
    st.success("✓ Clear Typography")
    st.success("✓ Consistent Spacing")
    
    st.metric("Image Size", f"{width} × {height}")
    st.metric("Border Width", f"{THEMES[theme_option]['border']}px")
    
    st.divider()
    
    # Color palette preview
    st.subheader("🎨 Color Palette")
    
    colors = THEMES[theme_option]
    col_pal1, col_pal2, col_pal3 = st.columns(3)
    
    with col_pal1:
        st.color_picker("Primary", 
                       value=f"#{colors['primary'][0]:02x}{colors['primary'][1]:02x}{colors['primary'][2]:02x}",
                       disabled=True)
    with col_pal2:
        st.color_picker("Background", 
                       value=f"#{colors['background'][0]:02x}{colors['background'][1]:02x}{colors['background'][2]:02x}",
                       disabled=True)
    with col_pal3:
        st.color_picker("Text", 
                       value=f"#{colors['text'][0]:02x}{colors['text'][1]:02x}{colors['text'][2]:02x}",
                       disabled=True)
    
    st.divider()
    
    # Design tips
    st.subheader("💡 Flat Design Principles")
    
    design_tips = [
        "**Simplicity**: Remove unnecessary elements",
        "**Clarity**: Use clear, readable typography",
        "**Consistency**: Maintain uniform spacing and sizing",
        "**Color**: Use bold, contrasting colors",
        "**Hierarchy**: Establish clear visual hierarchy"
    ]
    
    for tip in design_tips:
        st.markdown(f"- {tip}")
    
    st.divider()
    
    # Export settings
    st.subheader("⚙️ Export Settings")
    
    export_quality = st.select_slider("Quality", ["Low", "Medium", "High"], value="High")
    include_brand = st.checkbox("Include Brand Watermark", value=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #7F8C8D; font-size: 0.9rem;'>
    <p>🟩 Still Mind Flat Design Edition • Modern minimalist aesthetics • Clean geometric shapes</p>
</div>
""", unsafe_allow_html=True)

# Cleanup
for file in os.listdir("."):
    if file.startswith("temp_") and file.endswith(".mp4"):
        try:
            os.remove(file)
        except:
            pass