import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, math, time, requests
import numpy as np
from moviepy.editor import VideoClip
import tempfile
from functools import lru_cache

# ============================================================================
# STREAMLIT CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Nature Motion Studio",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit branding
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    .reportview-container .main .block-container {
        padding-top: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ============================================================================
# MODERN COLOR PALETTE
# ============================================================================
COLORS = {
    # Primary colors
    "deep_blue": (13, 36, 56, 255),       # #0D2438
    "forest_green": (41, 128, 99, 255),   # #298063
    "sand": (237, 221, 195, 255),         # #EDDDC3
    "sunset": (255, 147, 79, 255),        # #FF934F
    
    # Accents
    "mist": (255, 255, 255, 180),         # #FFFFFF
    "shadow": (0, 0, 0, 80),              # #000000
    "glow": (255, 255, 255, 120),         # #FFFFFF
    
    # Text
    "text_light": (250, 250, 250, 255),   # #FAFAFA
    "text_dark": (33, 33, 33, 255),       # #212121
}

# ============================================================================
# FLAT NATURE THEMES WITH ANIMATION PARAMETERS
# ============================================================================
NATURE_THEMES = {
    "Desert Dunes": {
        "bg": COLORS["sand"],
        "sky": (255, 248, 235, 255),
        "sand_layers": [
            (217, 193, 166, 255),
            (194, 173, 149, 255),
            (171, 153, 132, 255)
        ],
        "sun": (255, 213, 79, 255),
        "shadow": (194, 173, 149, 255),
        "animation": {
            "dune_speed": 0.3,
            "sun_speed": 0.1,
            "cloud_speed": 0.2
        }
    },
    "Mountain Fog": {
        "bg": COLORS["deep_blue"],
        "sky": (66, 135, 245, 255),
        "mountains": [
            (41, 128, 99, 255),
            (31, 97, 74, 255),
            (21, 66, 49, 255)
        ],
        "fog": (255, 255, 255, 120),
        "water": (66, 165, 245, 255),
        "animation": {
            "fog_speed": 0.4,
            "cloud_speed": 0.25,
            "water_speed": 0.5
        }
    },
    "Forest Dawn": {
        "bg": (13, 36, 56, 255),
        "sky": (255, 147, 79, 255),
        "trees": [
            (41, 128, 99, 255),
            (31, 97, 74, 255),
            (21, 66, 49, 255)
        ],
        "sun": (255, 213, 79, 255),
        "mist": (255, 255, 255, 60),
        "animation": {
            "leaf_speed": 0.6,
            "mist_speed": 0.35,
            "sun_speed": 0.15
        }
    },
    "Ocean Waves": {
        "bg": (13, 36, 56, 255),
        "sky": (66, 135, 245, 255),
        "water_layers": [
            (66, 165, 245, 255),
            (33, 150, 243, 255),
            (21, 101, 192, 255)
        ],
        "foam": (255, 255, 255, 200),
        "sun": (255, 213, 79, 255),
        "animation": {
            "wave_speed": 0.8,
            "foam_speed": 0.4,
            "cloud_speed": 0.2
        }
    }
}

# ============================================================================
# FLAT DESIGN BACKGROUND GENERATOR
# ============================================================================
def create_flat_background(width, height, theme_name, time_offset=0):
    """Create animated flat design nature background"""
    theme = NATURE_THEMES[theme_name]
    img = Image.new("RGBA", (width, height), theme["bg"])
    draw = ImageDraw.Draw(img)
    
    # Draw animated sky gradient
    sky_height = height // 3
    for y in range(sky_height):
        # Simple gradient with subtle wave animation
        wave = math.sin(y * 0.02 + time_offset * 0.5) * 5
        ratio = y / sky_height
        
        # Animate gradient colors
        r = int(theme["sky"][0] * (1 - ratio) + theme["bg"][0] * ratio)
        g = int(theme["sky"][1] * (1 - ratio) + theme["bg"][1] * ratio)
        b = int(theme["sky"][2] * (1 - ratio) + theme["bg"][2] * ratio)
        
        # Add animated wave effect
        if y % 3 == 0:
            draw.line([(0, y + int(wave)), (width, y + int(wave))], 
                     fill=(r, g, b, 255), width=3)
    
    # Theme-specific flat animations
    if "Desert" in theme_name:
        # Animated dunes
        dune_height = height // 4
        for i in range(5):
            dune_y = height // 2 + i * (dune_height // 3)
            
            # Calculate dune position with animation
            offset = math.sin(time_offset * theme["animation"]["dune_speed"] + i) * 50
            dune_width = width + abs(offset) * 2
            
            # Create dune shape
            points = []
            for x in range(0, dune_width, 20):
                x_pos = x - offset
                wave = math.sin(x * 0.01 + time_offset + i) * 40
                y_pos = dune_y + wave * (1 - i/5)
                points.append((x_pos, y_pos))
            
            # Close the shape
            if points:
                points.append((width, height))
                points.append((0, height))
                draw.polygon(points, fill=theme["sand_layers"][i % len(theme["sand_layers"])])
        
        # Animated sun
        sun_size = 80
        sun_x = width * 0.8 + math.sin(time_offset * theme["animation"]["sun_speed"]) * 20
        sun_y = height * 0.3 + math.cos(time_offset * theme["animation"]["sun_speed"]) * 10
        
        # Sun glow
        for size in range(sun_size, sun_size + 40, 10):
            alpha = 80 - (size - sun_size) * 2
            draw.ellipse([sun_x - size, sun_y - size, sun_x + size, sun_y + size],
                        fill=theme["sun"][:3] + (alpha,))
        
        # Sun body
        draw.ellipse([sun_x - sun_size, sun_y - sun_size, sun_x + sun_size, sun_y + sun_size],
                    fill=theme["sun"])
    
    elif "Mountain" in theme_name:
        # Animated mountain layers
        for layer in range(3):
            mountain_color = theme["mountains"][layer % len(theme["mountains"])]
            mountain_height = 200 - layer * 40
            mountain_y = height // 2 + layer * 20
            
            # Animate mountains slightly
            offset = math.sin(time_offset * 0.2 + layer) * 30
            
            for i in range(-1, 3):
                mountain_width = 300 + layer * 50
                mountain_x = i * 350 + offset * (layer + 1)
                
                # Simple mountain triangle
                points = [
                    (mountain_x, mountain_y + mountain_height),
                    (mountain_x + mountain_width // 2, mountain_y),
                    (mountain_x + mountain_width, mountain_y + mountain_height)
                ]
                draw.polygon(points, fill=mountain_color)
        
        # Animated fog
        fog_height = 60
        fog_y = height // 2 - 50
        fog_offset = time_offset * theme["animation"]["fog_speed"] * 100
        
        for i in range(3):
            fog_width = 400
            fog_x = i * 450 + fog_offset % 450
            
            # Create fog shape with rounded ends
            fog_rect = [fog_x, fog_y, fog_x + fog_width, fog_y + fog_height]
            draw.rounded_rectangle(fog_rect, radius=30, fill=theme["fog"])
            
            # Add subtle animation to fog opacity
            pulse = abs(math.sin(time_offset + i)) * 0.3 + 0.7
            fog_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            fog_draw = ImageDraw.Draw(fog_overlay)
            fog_draw.rounded_rectangle(fog_rect, radius=30, 
                                      fill=theme["fog"][:3] + (int(theme["fog"][3] * pulse),))
            img = Image.alpha_composite(img, fog_overlay)
    
    elif "Forest" in theme_name:
        # Animated tree layers
        tree_width = 80
        tree_spacing = 120
        
        for i in range(10):
            # Animate trees moving slightly
            tree_offset = math.sin(time_offset * 0.3 + i) * 10
            tree_x = i * tree_spacing + tree_offset
            tree_height = 150 + (i % 3) * 30
            
            # Tree trunk
            trunk_width = 20
            trunk_height = 60
            draw.rectangle([
                tree_x + tree_width//2 - trunk_width//2, height//2 + tree_height - trunk_height,
                tree_x + tree_width//2 + trunk_width//2, height//2 + tree_height
            ], fill=(101, 67, 33, 255))
            
            # Tree canopy (simple circles)
            canopy_layers = 3
            for layer in range(canopy_layers):
                canopy_size = tree_width - layer * 20
                canopy_y = height//2 + tree_height - trunk_height - layer * 40
                
                # Slight canopy movement
                canopy_wave = math.sin(time_offset * theme["animation"]["leaf_speed"] + i + layer) * 5
                
                draw.ellipse([
                    tree_x + (tree_width - canopy_size)//2,
                    canopy_y + canopy_wave,
                    tree_x + (tree_width + canopy_size)//2,
                    canopy_y + canopy_size + canopy_wave
                ], fill=theme["trees"][layer % len(theme["trees"])])
        
        # Animated sun rays
        sun_x = width * 0.2
        sun_y = height * 0.3
        sun_size = 60
        
        # Sun body
        draw.ellipse([sun_x - sun_size, sun_y - sun_size, sun_x + sun_size, sun_y + sun_size],
                    fill=theme["sun"])
        
        # Sun rays animation
        for ray in range(8):
            angle = ray * (360 / 8) + time_offset * 50
            ray_length = 80
            ray_width = 15
            
            # Calculate ray position
            end_x = sun_x + ray_length * math.cos(math.radians(angle))
            end_y = sun_y + ray_length * math.sin(math.radians(angle))
            
            # Draw ray with animation
            ray_alpha = abs(math.sin(time_offset + ray)) * 150 + 100
            draw.line([(sun_x, sun_y), (end_x, end_y)], 
                     fill=theme["sun"][:3] + (int(ray_alpha),), width=ray_width)
    
    elif "Ocean" in theme_name:
        # Animated ocean waves
        wave_height = 40
        
        for wave in range(5):
            wave_y = height // 2 + wave * wave_height
            
            # Calculate wave animation
            wave_offset = math.sin(time_offset * theme["animation"]["wave_speed"] + wave) * 50
            wave_width = width + 100
            
            # Create wave shape
            points = []
            for x in range(0, wave_width, 20):
                x_pos = x - wave_offset
                wave_height_mod = math.sin(x * 0.02 + time_offset * 2 + wave) * 20
                y_pos = wave_y + wave_height_mod
                points.append((x_pos, y_pos))
            
            # Close wave shape
            if points:
                points.append((width, height))
                points.append((0, height))
                
                # Draw wave with gradient effect
                wave_color = theme["water_layers"][wave % len(theme["water_layers"])]
                draw.polygon(points, fill=wave_color)
            
            # Animated foam on wave crests
            foam_y = wave_y - 10
            foam_width = 30
            
            for i in range(10):
                foam_x = (i * 100 + time_offset * 50) % width
                foam_wave = math.sin(time_offset * theme["animation"]["foam_speed"] + i) * 10
                
                draw.ellipse([
                    foam_x - foam_width//2, foam_y + foam_wave - 5,
                    foam_x + foam_width//2, foam_y + foam_wave + 5
                ], fill=theme["foam"])
    
    return img

# ============================================================================
# MODERN KINETIC TYPOGRAPHY
# ============================================================================
def draw_modern_text(draw, text, x, y, t, font_size, max_width, color, style="title"):
    """Draw modern kinetic text with flat design"""
    
    if style == "title":
        # Title with pulsing glow
        pulse = math.sin(t * 3) * 3
        current_size = int(font_size + pulse)
        
        try:
            font = ImageFont.truetype("arialbd.ttf", current_size)
        except:
            font = ImageFont.load_default(current_size)
        
        # Floating effect
        float_offset = math.sin(t * 2) * 2
        
        # Modern shadow (flat, offset)
        shadow_offset = 4
        draw.text((x + shadow_offset, y + shadow_offset + float_offset),
                 text, font=font, fill=(0, 0, 0, 120))
        
        # Main text with slight color variation
        r, g, b, a = color
        color_variation = int(math.sin(t * 4) * 20)
        animated_color = (
            min(255, max(0, r + color_variation)),
            min(255, max(0, g + color_variation)),
            min(255, max(0, b + color_variation)),
            a
        )
        
        draw.text((x, y + float_offset), text, font=font, fill=animated_color)
        
        return current_size
    
    elif style == "verse":
        # Typewriter reveal with modern fade
        font = ImageFont.load_default(font_size)
        
        # Animated reveal
        duration = 5
        progress = min(1.0, t / duration)
        visible_chars = int(len(text) * progress)
        
        # Split into words for clean wrap
        words = text.split()
        lines = []
        current_line = []
        
        # Build lines based on visible words
        visible_words = int(len(words) * progress)
        for i in range(visible_words):
            word = words[i]
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw lines with fade effect
        line_height = font_size * 1.4
        current_y = y
        
        for i, line in enumerate(lines):
            # Line position animation
            line_offset = math.sin(t * 2 + i) * 2
            
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            line_x = x + (max_width - text_width) // 2
            
            # Progressive fade for each line
            line_progress = min(1.0, (progress - i * 0.3) * 2)
            text_alpha = int(255 * line_progress)
            
            # Flat shadow
            draw.text((line_x + 3, current_y + line_offset + 3), line,
                     font=font, fill=(0, 0, 0, text_alpha//2))
            
            # Main text
            draw.text((line_x, current_y + line_offset), line,
                     font=font, fill=color[:3] + (text_alpha,))
            
            current_y += line_height
        
        return current_y

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_nature_video(width, height, theme, text, duration=8):
    """Create smooth animated video"""
    fps = 30
    
    def make_frame(t):
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        
        # Draw animated background
        bg = create_flat_background(width, height, theme, t)
        img.paste(bg, (0, 0))
        
        # Add text overlay
        draw = ImageDraw.Draw(img)
        
        # Draw title
        draw_modern_text(draw, "STILL MIND", width//2 - 150, 100, t,
                        font_size=72, max_width=300,
                        color=COLORS["text_light"], style="title")
        
        # Draw verse text
        draw_modern_text(draw, text, 100, height//2 - 100, t,
                        font_size=48, max_width=width - 200,
                        color=COLORS["text_light"], style="verse")
        
        # Add simple watermark
        watermark_font = ImageFont.load_default(24)
        draw.text((width - 150, height - 40), "nature.motion",
                 font=watermark_font, fill=(255, 255, 255, 180))
        
        return np.array(img.convert("RGB"))
    
    # Create video clip
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
    # Export
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_path = temp_file.name
    
    try:
        clip.write_videofile(
            temp_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None,
            preset='ultrafast',
            ffmpeg_params=['-crf', '28']
        )
        
        with open(temp_path, 'rb') as f:
            video_bytes = f.read()
        
        return video_bytes
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ============================================================================
# MAIN APP
# ============================================================================
# Title with minimal styling
st.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <h1 style="margin: 0; color: #298063;">Nature Motion Studio</h1>
    <p style="color: #666; margin: 0.5rem 0;">Animated Flat Design Backgrounds</p>
</div>
""", unsafe_allow_html=True)

# Simple two-column layout
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    # Minimal controls
    st.markdown("### Settings")
    
    # Theme selection with preview
    theme_option = st.selectbox(
        "🌿 Theme",
        list(NATURE_THEMES.keys()),
        index=0
    )
    
    # Display theme preview
    theme = NATURE_THEMES[theme_option]
    preview_size = 200
    
    # Create mini preview
    preview_img = create_flat_background(preview_size, preview_size//2, theme_option, 0)
    st.image(preview_img, caption=theme_option)
    
    # Text input
    st.markdown("---")
    st.markdown("### Text")
    
    text_input = st.text_area(
        "Enter your text",
        value="Be still and know that I am God",
        height=100
    )
    
    # Animation speed
    speed = st.slider("Animation Speed", 0.5, 2.0, 1.0, 0.1)
    
    # Resolution
    res_option = st.selectbox(
        "Resolution",
        ["1080x1920 (Vertical)", "1920x1080 (Horizontal)", "1080x1080 (Square)"]
    )
    
    # Action buttons
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🎬 Create Video", type="primary", use_container_width=True):
            st.session_state.create_video = True
    
    with col_btn2:
        if st.button("🔄 Live Preview", use_container_width=True):
            st.session_state.live_preview = not st.session_state.get("live_preview", False)

with col2:
    # Main preview area
    st.markdown("### Preview")
    
    # Get dimensions
    if "1080x1920" in res_option:
        width, height = 540, 960  # Half size for preview
    elif "1920x1080" in res_option:
        width, height = 960, 540
    else:
        width, height = 540, 540
    
    # Create preview placeholder
    preview_placeholder = st.empty()
    
    # Live preview animation
    if st.session_state.get("live_preview", False):
        for i in range(100):
            t = i * 0.1 * speed
            preview_img = create_flat_background(width, height, theme_option, t)
            
            # Add text overlay
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            draw_modern_text(draw, "STILL MIND", width//2 - 150, 50, t,
                            font_size=48, max_width=300,
                            color=COLORS["text_light"], style="title")
            
            draw_modern_text(draw, text_input, 50, height//2 - 50, t,
                            font_size=32, max_width=width - 100,
                            color=COLORS["text_light"], style="verse")
            
            # Combine
            preview_img = Image.alpha_composite(preview_img, overlay)
            
            preview_placeholder.image(preview_img)
            time.sleep(0.1)
    else:
        # Static preview
        preview_img = create_flat_background(width, height, theme_option, 0)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        draw_modern_text(draw, "STILL MIND", width//2 - 150, 50, 0,
                        font_size=48, max_width=300,
                        color=COLORS["text_light"], style="title")
        
        draw_modern_text(draw, text_input, 50, height//2 - 50, 0,
                        font_size=32, max_width=width - 100,
                        color=COLORS["text_light"], style="verse")
        
        preview_img = Image.alpha_composite(preview_img, overlay)
        preview_placeholder.image(preview_img)
    
    # Video creation
    if st.session_state.get("create_video", False):
        with st.spinner("🎬 Creating animated video..."):
            # Get full resolution
            if "1080x1920" in res_option:
                vid_width, vid_height = 1080, 1920
            elif "1920x1080" in res_option:
                vid_width, vid_height = 1920, 1080
            else:
                vid_width, vid_height = 1080, 1080
            
            video_data = create_nature_video(vid_width, vid_height, theme_option, text_input)
            
            if video_data:
                st.video(video_data)
                
                # Download button
                st.download_button(
                    label="📥 Download MP4",
                    data=video_data,
                    file_name=f"nature_motion_{theme_option.lower().replace(' ', '_')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        
        st.session_state.create_video = False

# Simple footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
    "Nature Motion Studio • Flat Design Animations • Made with Streamlit"
    "</div>",
    unsafe_allow_html=True
)

# Initialize session state
if "live_preview" not in st.session_state:
    st.session_state.live_preview = False
if "create_video" not in st.session_state:
    st.session_state.create_video = False