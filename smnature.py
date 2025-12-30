import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time
import numpy as np
from moviepy.editor import VideoClip
import random

# ============================================================================
# STREAMLIT SETUP
# ============================================================================
st.set_page_config(
    page_title="Still Mind Nature",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# NATURE THEME SYSTEM
# ============================================================================
THEMES = {
    "Forest Sunrise": {
        "dawn": {
            "sky": [(10, 25, 35, 255), (80, 40, 60, 255)],  # Night to dawn purple
            "light": (255, 200, 0, 180),  # Golden sunlight
            "tree": (30, 80, 40, 255),  # Deep green
            "water": (40, 100, 150, 120)
        },
        "day": {
            "sky": [(80, 40, 60, 255), (200, 100, 50, 255)],  # Dawn to sunrise
            "light": (255, 220, 120, 255),  # Bright sunlight
            "tree": (60, 140, 80, 255),  # Bright green
            "water": (80, 150, 180, 180)
        },
        "accent": (76, 175, 80, 255),
        "text": (255, 255, 255, 255)
    },
    "Ocean Twilight": {
        "dawn": {
            "sky": [(20, 30, 60, 255), (60, 40, 100, 255)],  # Deep blue to purple
            "light": (100, 200, 255, 180),  # Blue light
            "tree": (20, 60, 80, 255),
            "water": (30, 80, 120, 150)
        },
        "day": {
            "sky": [(60, 40, 100, 255), (150, 100, 200, 255)],  Purple to pink
            "light": (180, 140, 255, 255),
            "tree": (40, 100, 120, 255),
            "water": (60, 120, 160, 200)
        },
        "accent": (0, 200, 200, 255),
        "text": (255, 255, 255, 255)
    },
    "Mountain Mist": {
        "dawn": {
            "sky": [(25, 35, 45, 255), (60, 70, 90, 255)],
            "light": (200, 220, 240, 150),
            "tree": (40, 60, 50, 255),
            "water": (50, 80, 90, 130)
        },
        "day": {
            "sky": [(60, 70, 90, 255), (120, 140, 160, 255)],
            "light": (240, 245, 250, 220),
            "tree": (80, 100, 90, 255),
            "water": (80, 120, 130, 180)
        },
        "accent": (140, 180, 170, 255),
        "text": (255, 255, 255, 255)
    }
}

SIZES = {
    "TikTok (1080x1920)": (1080, 1920),
    "Instagram (1080x1080)": (1080, 1080),
    "Stories (1080x1350)": (1080, 1350),
    "Desktop (1920x1200)": (1920, 1200)
}

# ============================================================================
# ORGANIC NATURE GENERATORS
# ============================================================================
def interpolate_color(color1, color2, progress):
    """Smooth color transition between two RGBA colors."""
    r1, g1, b1, a1 = color1
    r2, g2, b2, a2 = color2
    r = int(r1 + (r2 - r1) * progress)
    g = int(g1 + (g2 - g1) * progress)
    b = int(b1 + (b2 - b1) * progress)
    a = int(a1 + (a2 - a1) * progress)
    return (r, g, b, a)

def draw_fractal_tree(draw, x, y, angle, length, depth, time_offset, wind_strength, colors):
    """Recursive tree with wind animation and seasonal colors."""
    if depth <= 0 or length < 2:
        return
    
    # Wind sway with natural variation
    wind_sway = wind_strength * math.sin(time_offset * 1.5 + depth * 0.3) * (0.2 / max(1, depth - 2))
    branch_angle = angle + wind_sway
    
    # Calculate end point
    x2 = x + math.cos(branch_angle) * length
    y2 = y + math.sin(branch_angle) * length
    
    # Branch thickness decreases with depth
    thickness = max(1, depth * 2)
    
    # Color variation through depth (trunk to leaves)
    if depth > 3:  # Trunk/branches
        branch_color = colors["tree"][:3] + (200,)
    else:  # Leaves/twigs
        leaf_variation = int(40 * math.sin(time_offset + depth))
        leaf_color = (
            min(255, colors["tree"][0] + leaf_variation),
            min(255, colors["tree"][1] + leaf_variation),
            min(255, colors["tree"][2] + leaf_variation),
            180
        )
        branch_color = leaf_color
    
    # Draw branch
    draw.line([(x, y), (x2, y2)], fill=branch_color, width=thickness)
    
    # Branch randomness for organic feel
    branch_randomness = 0.3 + 0.2 * math.sin(time_offset + depth)
    
    # Recursive branches
    if depth > 1:
        # Left branch
        left_angle = branch_angle - (0.45 * branch_randomness)
        left_length = length * (0.65 + 0.1 * math.sin(time_offset + depth))
        draw_fractal_tree(draw, x2, y2, left_angle, left_length, depth - 1, 
                         time_offset, wind_strength, colors)
        
        # Right branch
        right_angle = branch_angle + (0.45 * branch_randomness)
        right_length = length * (0.65 + 0.1 * math.cos(time_offset + depth))
        draw_fractal_tree(draw, x2, y2, right_angle, right_length, depth - 1, 
                         time_offset, wind_strength, colors)
        
        # Occasionally add a third branch for fuller trees
        if depth > 2 and random.random() > 0.7:
            middle_angle = branch_angle + (0.1 * math.sin(time_offset))
            middle_length = length * 0.5
            draw_fractal_tree(draw, x2, y2, middle_angle, middle_length, 
                             depth - 2, time_offset, wind_strength, colors)

def draw_ocean_waves(draw, width, height, time_offset, colors):
    """Organic wave patterns with light interaction."""
    for wave_layer in range(4):  # Multiple wave layers for depth
        wave_height = 120 + wave_layer * 20
        wave_points = [(0, height)]
        
        # Wave frequency and amplitude variations
        freq1 = 0.003 + wave_layer * 0.001
        freq2 = 0.008 + wave_layer * 0.002
        amp1 = 15 + wave_layer * 3
        amp2 = 8 + wave_layer * 2
        
        for x in range(0, width + 50, 25):
            # Combined sine waves for organic movement
            y_offset = (wave_layer * 25)
            y_wave = amp1 * math.sin(freq1 * x + time_offset * 2 + wave_layer)
            y_wave += amp2 * math.sin(freq2 * x - time_offset * 1.7 + wave_layer * 1.3)
            y_wave += 5 * math.sin(0.02 * x + time_offset * 0.5)
            
            y = height - wave_height + y_offset + y_wave
            wave_points.append((x, y))
        
        wave_points.append((width, height))
        
        # Wave color with depth variation
        wave_color = interpolate_color(
            colors["water"],
            colors["light"],
            wave_layer * 0.2
        )
        
        # Draw wave polygon
        draw.polygon(wave_points, fill=wave_color)

def draw_stars(draw, width, height, time_offset, dawn_progress):
    """Twinkling stars that fade at dawn."""
    # Stars become less visible as dawn progresses
    star_opacity = int(255 * (1 - dawn_progress))
    
    if star_opacity > 0:
        # Draw background stars (small, faint)
        for i in range(60):
            # Star positions based on pseudo-random but consistent placement
            angle = i * 0.1
            radius = 0.3 + 0.2 * math.sin(i)
            x = width * (0.5 + radius * math.cos(angle + time_offset * 0.05))
            y = height * (0.3 + radius * math.sin(angle + time_offset * 0.07))
            
            # Twinkling effect
            twinkle = abs(math.sin(time_offset * 3 + i)) * 0.5 + 0.5
            size = 1 + int(2 * twinkle)
            opacity = int(star_opacity * (0.3 + 0.7 * twinkle))
            
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=(255, 255, 255, opacity))
        
        # Draw a few brighter stars
        for i in range(8):
            angle = i * 0.8
            radius = 0.4 + 0.3 * math.cos(i)
            x = width * (0.5 + radius * math.cos(angle + time_offset * 0.03))
            y = height * (0.3 + radius * math.sin(angle + time_offset * 0.04))
            
            twinkle = abs(math.sin(time_offset * 2 + i * 0.5))
            size = 2 + int(3 * twinkle)
            opacity = int(star_opacity * (0.6 + 0.4 * twinkle))
            
            # Add glow around bright stars
            glow_size = size + 3
            draw.ellipse([x-glow_size, y-glow_size, x+glow_size, y+glow_size],
                        fill=(255, 255, 255, opacity // 3))
            draw.ellipse([x-size, y-size, x+size, y+size],
                        fill=(255, 255, 255, opacity))

def draw_glass_ui(draw, img, x1, y1, x2, y2, accent_color, dawn_progress, time_offset):
    """Frosted glass effect UI with natural elements."""
    # Crop and blur area for glass effect
    glass_region = img.crop((x1-20, y1-20, x2+20, y2+20))
    glass_region = glass_region.filter(ImageFilter.GaussianBlur(radius=15))
    img.paste(glass_region, (x1-20, y1-20))
    
    # Glass overlay with varying opacity based on dawn
    glass_opacity = int(180 + 75 * math.sin(time_offset * 0.5))
    draw.rectangle([x1, y1, x2, y2], 
                  fill=(20, 30, 40, glass_opacity))
    
    # Subtle border with dawn glow
    border_glow = interpolate_color(
        (76, 175, 80, 100),
        (255, 200, 0, 150),
        dawn_progress
    )
    draw.rectangle([x1, y1, x2, y2], 
                  outline=border_glow, 
                  width=3)
    
    # Natural corner decorations (leaf/vine inspired)
    corner_size = 40
    leaf_color = interpolate_color(
        accent_color,
        (255, 220, 100, 255),
        dawn_progress
    )
    
    def draw_natural_corner(cx, cy, rotation):
        # Draw vine-like corner decoration
        points = []
        for i in range(5):
            angle = rotation + i * 0.3
            px = cx + corner_size * math.cos(angle) * (1 - i * 0.15)
            py = cy + corner_size * math.sin(angle) * (1 - i * 0.15)
            points.append((px, py))
        
        # Draw leaf shapes
        for point in points:
            leaf_size = 8 + 4 * math.sin(time_offset + point[0] * 0.01)
            draw.ellipse([point[0]-leaf_size, point[1]-leaf_size,
                         point[0]+leaf_size, point[1]+leaf_size],
                        fill=leaf_color[:3] + (180,))
    
    # Draw corners
    draw_natural_corner(x1, y1, math.pi)  # Top-left
    draw_natural_corner(x2, y1, -math.pi/2)  # Top-right
    draw_natural_corner(x1, y2, math.pi/2)  # Bottom-left
    draw_natural_corner(x2, y2, 0)  # Bottom-right

# ============================================================================
# FONT MANAGEMENT
# ============================================================================
def load_natural_font(size, bold=False):
    """Load a font that fits natural themes."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    
    if bold:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Helvetica-Bold.ttc"
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    
    return ImageFont.load_default(size)

# ============================================================================
# BIBLE VERSE FETCHING
# ============================================================================
@st.cache_data(ttl=3600)
def fetch_bible_verse(book, chapter, verse):
    """Fetch verse with fallback to natural-themed verses."""
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            text = data.get("text", "").replace("\n", " ").strip()
            return text, data.get("reference", f"{book} {chapter}:{verse}")
    except:
        pass
    
    # Natural-themed fallback verses
    fallback_verses = [
        "Be still, and know that I am God.",
        "The Lord is my shepherd; I shall not want.",
        "He makes me lie down in green pastures.",
        "Peace I leave with you; my peace I give to you.",
        "Consider the lilies of the field, how they grow.",
        "The trees of the Lord are watered abundantly.",
        "Let the sea roar, and all that fills it."
    ]
    
    text = random.choice(fallback_verses)
    return text, f"{book} {chapter}:{verse}"

# ============================================================================
# MAIN IMAGE GENERATION
# ============================================================================
def create_nature_scene(width, height, theme_name, book, chapter, verse, 
                       hook, dawn_progress=0.0, time_offset=0, is_video=False):
    """Create a complete nature scene with dawn progression."""
    theme = THEMES[theme_name]
    
    # Interpolate colors based on dawn progress
    dawn_colors = theme["dawn"]
    day_colors = theme["day"]
    
    current_colors = {}
    for key in dawn_colors:
        if isinstance(dawn_colors[key][0], (list, tuple)) and len(dawn_colors[key][0]) == 4:
            # Handle gradient tuples
            start_grad = dawn_colors[key]
            end_grad = day_colors[key]
            current_colors[key] = (
                interpolate_color(start_grad[0], end_grad[0], dawn_progress),
                interpolate_color(start_grad[1], end_grad[1], dawn_progress)
            )
        else:
            current_colors[key] = interpolate_color(
                dawn_colors[key], 
                day_colors[key], 
                dawn_progress
            )
    
    current_colors["accent"] = theme["accent"]
    current_colors["text"] = theme["text"]
    
    # Create base image
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Draw sky gradient
    sky_start, sky_end = current_colors["sky"]
    for y in range(height):
        ratio = y / height
        # Add wave effect to gradient
        wave = 0.05 * math.sin(y * 0.01 + time_offset * 0.3)
        ratio = max(0, min(1, ratio + wave))
        
        r = int((1-ratio) * sky_start[0] + ratio * sky_end[0])
        g = int((1-ratio) * sky_start[1] + ratio * sky_end[1])
        b = int((1-ratio) * sky_start[2] + ratio * sky_end[2])
        a = int((1-ratio) * sky_start[3] + ratio * sky_end[3])
        draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    # Draw stars (fade out with dawn)
    draw_stars(draw, width, height, time_offset, dawn_progress)
    
    # Draw ocean waves
    draw_ocean_waves(draw, width, height, time_offset, current_colors)
    
    # Draw fractal trees with wind
    wind_strength = 0.5 + 0.3 * math.sin(time_offset * 0.2)
    
    # Left tree
    draw_fractal_tree(draw, width * 0.2, height - 100, 
                     -math.pi/2, 130, 8, time_offset, 
                     wind_strength, current_colors)
    
    # Right tree
    draw_fratcal_tree(draw, width * 0.8, height - 100, 
                     -math.pi/2, 110, 7, time_offset, 
                     wind_strength, current_colors)
    
    # Draw sun/moon based on dawn progress
    sun_size = 60 + 40 * dawn_progress
    sun_x = width * (0.5 + 0.3 * dawn_progress)
    sun_y = height * 0.25
    
    sun_color = interpolate_color(
        (200, 200, 220, 200),  # Moon-like
        (255, 220, 100, 255),  # Sun-like
        dawn_progress
    )
    
    # Sun glow
    for glow in range(3, 0, -1):
        glow_size = sun_size + glow * 20
        glow_opacity = int(100 * (1 - glow * 0.3) * dawn_progress)
        draw.ellipse([sun_x-glow_size, sun_y-glow_size, 
                     sun_x+glow_size, sun_y+glow_size],
                    fill=sun_color[:3] + (glow_opacity,))
    
    # Sun/Moon body
    draw.ellipse([sun_x-sun_size, sun_y-sun_size, 
                 sun_x+sun_size, sun_y+sun_size],
                fill=sun_color)
    
    # Glass UI Box
    box_width = 900
    box_height = 500
    box_x = (width - box_width) // 2
    box_y = (height - box_height) // 2 - 50
    
    draw_glass_ui(draw, img, box_x, box_y, box_x + box_width, box_y + box_height,
                 current_colors["accent"], dawn_progress, time_offset)
    
    # Get verse text
    verse_text, reference = fetch_bible_verse(book, chapter, verse)
    
    # Typewriter effect for video
    if is_video:
        typewriter_duration = 5  # seconds
        typewriter_progress = min(1.0, time_offset / typewriter_duration)
        visible_text = verse_text[:int(len(verse_text) * typewriter_progress)]
    else:
        visible_text = verse_text
    
    # Wrap text
    verse_font = load_natural_font(50)
    words = visible_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = verse_font.getbbox(test_line)
        if bbox[2] - bbox[0] <= box_width - 100:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw verse text
    line_height = verse_font.getbbox("A")[3] * 1.5
    text_y = box_y + 60
    
    for line in lines:
        bbox = verse_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        
        # Text shadow for readability
        draw.text((x+2, text_y+2), line, 
                 font=verse_font, fill=(0, 0, 0, 150))
        
        # Main text
        text_color = current_colors["text"][:3] + (
            int(255 * (1 if not is_video else min(1.0, time_offset / 2))),
        )
        draw.text((x, text_y), line, 
                 font=verse_font, fill=text_color)
        
        text_y += line_height
    
    # Draw hook (top)
    if hook:
        hook_font = load_natural_font(70, bold=True)
        hook_bbox = hook_font.getbbox(hook.upper())
        hook_x = (width - (hook_bbox[2] - hook_bbox[0])) // 2
        hook_y = box_y - 120
        
        hook_opacity = 255 if not is_video else int(255 * min(1.0, time_offset / 1))
        
        # Hook shadow
        draw.text((hook_x+3, hook_y+3), hook.upper(),
                 font=hook_font, fill=(0, 0, 0, hook_opacity // 2))
        
        # Hook text
        draw.text((hook_x, hook_y), hook.upper(),
                 font=hook_font, 
                 fill=current_colors["accent"][:3] + (hook_opacity,))
    
    # Draw reference (bottom)
    ref_font = load_natural_font(40, bold=True)
    ref_bbox = ref_font.getbbox(reference)
    ref_x = box_x + box_width - (ref_bbox[2] - ref_bbox[0]) - 40
    ref_y = box_y + box_height + 40
    
    ref_opacity = 255 if not is_video else int(255 * max(0, min(1.0, (time_offset - 4) / 1)))
    
    if ref_opacity > 0:
        # Reference background
        draw.rectangle([ref_x-15, ref_y-10, 
                       ref_x + (ref_bbox[2] - ref_bbox[0]) + 15, 
                       ref_y + (ref_bbox[3] - ref_bbox[1]) + 10],
                      fill=current_colors["accent"][:3] + (ref_opacity // 3,))
        
        # Reference text
        draw.text((ref_x, ref_y), reference,
                 font=ref_font,
                 fill=current_colors["text"][:3] + (ref_opacity,))
    
    # Add "Still Mind Nature" watermark
    watermark_font = load_natural_font(35)
    draw.text((30, 30), "Still Mind Nature",
             font=watermark_font,
             fill=current_colors["accent"][:3] + (180,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_nature_video(width, height, theme_name, book, chapter, verse, hook):
    """Create a video showing dawn progression."""
    duration = 8  # seconds
    fps = 24
    
    def make_frame(t):
        # Dawn progresses from 0 to 1 over the video duration
        dawn_progress = min(1.0, t / duration)
        
        img = create_nature_scene(
            width, height, theme_name, book, chapter, verse,
            hook, dawn_progress, t, True
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
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("🌿 Still Mind Nature")
st.markdown("### Create serene nature-themed scripture graphics")

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(90deg, #4CAF50, #2E7D32);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #45a049, #1B5E20);
        transform: translateY(-2px);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a2c1a, #0d1b0d);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🎨 Nature Settings")
    
    theme_option = st.selectbox("Theme", list(THEMES.keys()))
    size_option = st.selectbox("Size Format", list(SIZES.keys()))
    width, height = SIZES[size_option]
    
    st.header("🌅 Dawn Settings")
    dawn_slider = st.slider("Dawn Progress", 0.0, 1.0, 0.0, 0.1,
                           help="0.0 = Night, 1.0 = Full Sunrise")
    
    st.header("📖 Scripture")
    bible_books = ["Psalm", "Isaiah", "Matthew", "John", "Romans", 
                   "Ephesians", "Philippians", "Colossians", "James"]
    book = st.selectbox("Book", bible_books)
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 23)
    with col2:
        verse = st.number_input("Verse", 1, 176, 1)
    
    hook = st.text_input("Header Text", "PEACE LIKE A RIVER")
    
    st.header("🌬️ Nature Effects")
    wind_strength = st.slider("Wind Strength", 0.0, 1.0, 0.5, 0.1)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Generate preview
    st.subheader("🌿 Live Preview")
    
    with st.spinner("Painting nature scene..."):
        preview_img = create_nature_scene(
            width, height, theme_option, book, chapter, verse,
            hook, dawn_slider, 0, False
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
            file_name=f"nature_peace_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Sunrise Meditation (8s)", use_container_width=True):
            with st.spinner("Watching the sunrise..."):
                video_data = create_nature_video(
                    width, height, theme_option,
                    book, chapter, verse, hook
                )
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"sunrise_meditation_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    st.subheader("🌳 Scene Info")
    
    # Theme preview
    theme = THEMES[theme_option]
    col_a, col_b = st.columns(2)
    with col_a:
        st.color_picker("Dawn Color", 
                       value=f"#{theme['dawn']['sky'][0][0]:02x}{theme['dawn']['sky'][0][1]:02x}{theme['dawn']['sky'][0][2]:02x}",
                       disabled=True)
    with col_b:
        st.color_picker("Sunrise Color", 
                       value=f"#{theme['day']['sky'][1][0]:02x}{theme['day']['sky'][1][1]:02x}{theme['day']['sky'][1][2]:02x}",
                       disabled=True)
    
    st.metric("Image Size", f"{width} × {height}")
    st.metric("Dawn Progress", f"{dawn_slider:.0%}")
    
    st.divider()
    
    # Verse info
    verse_text, reference = fetch_bible_verse(book, chapter, verse)
    st.write("**Selected Verse:**")
    st.info(f"{book} {chapter}:{verse}")
    
    st.write("**Text Preview:**")
    st.caption(verse_text[:100] + "..." if len(verse_text) > 100 else verse_text)
    
    st.divider()
    
    # Nature effects info
    st.subheader("🍃 Nature Effects")
    
    st.write("**Active Effects:**")
    if dawn_slider > 0:
        st.success(f"☀️ Sunrise: {dawn_slider:.0%}")
    else:
        st.info("🌙 Night Sky")
    
    st.write(f"🌬️ Wind Strength: {wind_strength:.1f}")
    st.write("🌊 Ocean Waves: Animated")
    st.write("🌳 Fractal Trees: Dynamic")
    
    st.divider()
    
    # Social media caption
    st.subheader("📱 Social Share")
    
    nature_hashtags = {
        "Forest Sunrise": "#Forest #Sunrise #Morning #NaturePeace",
        "Ocean Twilight": "#Ocean #Twilight #Sea #CalmWaters",
        "Mountain Mist": "#Mountains #Mist #Fog #Serenity"
    }
    
    caption = f"""{hook}

"{verse_text[:120]}..."

🌿 {reference}

{nature_hashtags.get(theme_option, "#Nature #Peace #Stillness")}
#StillMindNature #ScriptureInNature"""

    st.text_area("Caption", caption, height=150)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Copied!")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #4CAF50;'>
    <p>🌿 Still Mind Nature v2.0 • Finding peace in creation • Psalm 19:1</p>
</div>
""", unsafe_allow_html=True)