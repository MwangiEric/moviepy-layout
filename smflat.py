import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math, time, random, requests
import numpy as np
from moviepy.editor import VideoClip
import tempfile
from groq import Groq

# ============================================================================
# STREAMLIT CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Scripture Motion Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern UI Styling
st.markdown("""
<style>
    .main .block-container {padding-top: 1rem;}
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .ai-feature {background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%); color: black; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem;}
    .emotion-badge {display: inline-block; padding: 3px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# EMOTIONAL FLAT DESIGN SYSTEM
# ============================================================================
EMOTIONAL_THEMES = {
    "Morning Calm": {
        "emotion": "calm",
        "colors": {
            "bg": (240, 248, 255, 255),      # Alice Blue
            "primary": (100, 149, 237, 255),  # Cornflower Blue
            "secondary": (135, 206, 250, 255), # Light Sky Blue
            "accent": (255, 255, 255, 255),   # White
            "text": (25, 25, 112, 255)       # Midnight Blue
        },
        "animation": "breathing_circles"
    },
    "Golden Hope": {
        "emotion": "hope",
        "colors": {
            "bg": (255, 248, 225, 255),      # Light Gold
            "primary": (255, 193, 7, 255),    # Amber
            "secondary": (255, 224, 130, 255),# Light Amber
            "accent": (255, 255, 255, 255),
            "text": (139, 69, 19, 255)       # Saddle Brown
        },
        "animation": "sunrise_rays"
    },
    "Night Stillness": {
        "emotion": "stillness",
        "colors": {
            "bg": (10, 15, 30, 255),         # Deep Night
            "primary": (123, 104, 238, 255),  # Medium Slate Blue
            "secondary": (186, 85, 211, 255), # Medium Orchid
            "accent": (255, 255, 255, 200),
            "text": (240, 248, 255, 255)     # Alice Blue
        },
        "animation": "twinkling_stars"
    },
    "Forest Peace": {
        "emotion": "peace",
        "colors": {
            "bg": (240, 255, 240, 255),      # Honeydew
            "primary": (34, 139, 34, 255),    # Forest Green
            "secondary": (152, 251, 152, 255), # Pale Green
            "accent": (255, 255, 255, 255),
            "text": (0, 51, 0, 255)          # Dark Green
        },
        "animation": "swaying_trees"
    }
}

# ============================================================================
# GROQ AI INTEGRATION
# ============================================================================
def get_groq_client():
    """Initialize Groq client"""
    try:
        if hasattr(st, 'secrets') and 'groq_key' in st.secrets:
            return Groq(api_key=st.secrets.groq_key)
        return None
    except:
        return None

def generate_ai_hook(verse, theme, emotion):
    """Generate creative title using AI"""
    client = get_groq_client()
    if not client:
        fallbacks = {
            "calm": ["BE STILL", "INNER PEACE", "QUIET SOUL"],
            "hope": ["NEW DAWN", "PROMISE RISING", "HOPE AWAITS"],
            "stillness": ["NIGHT WATCH", "STARLIT", "MOONLIGHT"],
            "peace": ["FOREST PATH", "GREEN PASTURES", "STILL WATERS"]
        }
        return random.choice(fallbacks.get(emotion, ["STILL MIND"]))
    
    try:
        prompt = f"""Create a powerful 1-3 word title for scripture graphic.
        Verse: {verse[:80]}
        Theme: {theme}
        Emotion: {emotion}
        
        Requirements:
        - 1-3 words, ALL CAPS
        - No punctuation
        - Evokes {emotion} emotion
        - Modern, minimal
        
        Title:"""
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.7
        )
        
        hook = response.choices[0].message.content.strip().upper()
        hook = hook.replace('"', '').replace("'", "").replace(".", "")
        return hook[:30]  # Limit length
    except:
        return "STILL MIND"

def generate_ai_caption(hook, verse, ref, theme, emotion):
    """Generate social media caption using AI"""
    client = get_groq_client()
    if not client:
        return f"""{hook}

{verse[:100]}...

📖 {ref}

#Scripture #{emotion.title()} #{theme.replace(' ', '')}"""
    
    try:
        prompt = f"""Generate TikTok caption for scripture graphic.
        
        Hook: {hook}
        Verse: {verse}
        Reference: {ref}
        Theme: {theme}
        Emotion: {emotion}
        
        Include:
        1. Hook (1 line)
        2. Verse excerpt (short)
        3. Reference
        4. Call to action (Save, Share, Tag)
        5. 3-5 hashtags
        
        Keep under 220 characters.
        
        Caption:"""
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except:
        return f"""{hook}

{verse[:100]}...

📖 {ref}

#Scripture #{emotion.title()} #{theme.replace(' ', '')}"""

# ============================================================================
# ANIMATED FLAT BACKGROUND ENGINE
# ============================================================================
def create_animated_background(width, height, theme_name, time_offset=0):
    """Create flat design animated background"""
    theme = EMOTIONAL_THEMES[theme_name]
    colors = theme["colors"]
    
    img = Image.new("RGBA", (width, height), colors["bg"])
    draw = ImageDraw.Draw(img)
    
    if theme["animation"] == "breathing_circles":
        # Animated breathing circles
        for i in range(12):
            x = width // 2 + math.cos(i * math.pi/6) * 300
            y = height // 2 + math.sin(i * math.pi/6) * 300
            
            breath = math.sin(time_offset * 2 + i) * 0.3 + 0.7
            size = 40 * breath
            
            # Draw flat circle with outline
            draw.ellipse([x-size, y-size, x+size, y+size],
                        outline=colors["primary"], width=3)
            
            # Inner dot
            dot_size = 8 + math.sin(time_offset * 3 + i) * 3
            draw.ellipse([x-dot_size, y-dot_size, x+dot_size, y+dot_size],
                        fill=colors["secondary"])
    
    elif theme["animation"] == "sunrise_rays":
        # Sunrise with animated rays
        sun_x, sun_y = width // 2, height * 0.3
        sun_size = 70 + math.sin(time_offset) * 10
        
        # Sun
        draw.ellipse([sun_x-sun_size, sun_y-sun_size, 
                     sun_x+sun_size, sun_y+sun_size],
                    fill=colors["primary"])
        
        # Rays
        for i in range(16):
            angle = i * math.pi / 8 + time_offset
            length = 100 + math.sin(time_offset * 2 + i) * 30
            end_x = sun_x + length * math.cos(angle)
            end_y = sun_y + length * math.sin(angle)
            
            ray_width = 6 + math.sin(time_offset * 3 + i) * 2
            draw.line([(sun_x, sun_y), (end_x, end_y)],
                     fill=colors["secondary"], width=int(ray_width))
    
    elif theme["animation"] == "twinkling_stars":
        # Twinkling stars
        for i in range(80):
            x = (i * 731) % width
            y = (i * 521) % (height * 0.8)
            
            twinkle = math.sin(time_offset * 4 + i) * 0.5 + 0.5
            size = 1 + int(3 * twinkle)
            alpha = int(200 * twinkle)
            
            draw.ellipse([x-size, y-size, x+size, y+size],
                        fill=colors["accent"][:3] + (alpha,))
        
        # Crescent moon
        moon_x, moon_y = width * 0.8, height * 0.2
        moon_size = 50
        draw.ellipse([moon_x-moon_size, moon_y-moon_size,
                     moon_x+moon_size, moon_y+moon_size],
                    fill=colors["secondary"][:3] + (80,))
        draw.ellipse([moon_x-moon_size//2, moon_y-moon_size//2,
                     moon_x+moon_size//2, moon_y+moon_size//2],
                    fill=colors["bg"])
    
    elif theme["animation"] == "swaying_trees":
        # Swaying flat trees
        tree_count = 8
        for i in range(tree_count):
            tree_x = width * (0.1 + 0.8 * i/(tree_count-1))
            tree_y = height * 0.7
            
            sway = math.sin(time_offset * 0.5 + i) * 15
            tree_x += sway
            
            # Trunk
            trunk_width = 18
            trunk_height = 100
            draw.rectangle([tree_x-trunk_width//2, tree_y,
                           tree_x+trunk_width//2, tree_y-trunk_height],
                          fill=(101, 67, 33, 255))
            
            # Canopy (3 circles)
            for j in range(3):
                canopy_size = 45 - j * 10
                canopy_y = tree_y - trunk_height + j * 30
                sway_offset = math.sin(time_offset + i + j) * 5
                draw.ellipse([tree_x-canopy_size, canopy_y+sway_offset-canopy_size,
                             tree_x+canopy_size, canopy_y+sway_offset+canopy_size],
                            fill=colors["primary"][:3] + (220 - j*50,))
    
    # Add subtle grid
    grid_spacing = 80
    alpha = 15
    for x in range(0, width, grid_spacing):
        offset = (time_offset * 20) % grid_spacing
        draw.line([(x+offset, 0), (x+offset, height)],
                 fill=(255, 255, 255, alpha), width=1)
    
    return img

# ============================================================================
# KINETIC TYPOGRAPHY
# ============================================================================
def draw_kinetic_text(draw, text, x, y, font_size, color, time_offset, style="fade"):
    """Draw text with kinetic animations"""
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except:
        font = ImageFont.load_default(font_size)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    actual_x = x - text_width // 2
    
    if style == "fade":
        # Fade in
        alpha = min(255, int(time_offset * 100))
        draw.text((actual_x, y), text, font=font, fill=color[:3] + (alpha,))
    
    elif style == "typewriter":
        # Typewriter reveal
        chars = int(len(text) * min(1.0, time_offset * 2))
        visible = text[:chars]
        draw.text((actual_x, y), visible, font=font, fill=color)
        
        # Blinking cursor
        if chars < len(text) and int(time_offset * 3) % 2 == 0:
            cursor_x = actual_x + draw.textbbox((0, 0), visible, font=font)[2]
            cursor_y = y + 5
            draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y+font_size-10)],
                     fill=color, width=4)
    
    elif style == "float":
        # Floating animation
        float_y = y + math.sin(time_offset * 2) * 5
        draw.text((actual_x, float_y), text, font=font, fill=color)
    
    elif style == "pulse":
        # Pulsing size
        pulse = math.sin(time_offset * 3) * 0.1 + 1.0
        pulse_size = int(font_size * pulse)
        
        try:
            pulse_font = ImageFont.truetype("arialbd.ttf", pulse_size)
        except:
            pulse_font = ImageFont.load_default(pulse_size)
        
        bbox = pulse_font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        actual_x = x - text_width // 2
        
        draw.text((actual_x, y), text, font=pulse_font, fill=color)
    
    return text_width

# ============================================================================
# MAIN COMPOSITION ENGINE
# ============================================================================
def create_scripture_design(width, height, theme_name, hook, verse, ref, time_offset=0):
    """Create complete scripture design"""
    theme = EMOTIONAL_THEMES[theme_name]
    colors = theme["colors"]
    
    # Create background
    img = create_animated_background(width, height, theme_name, time_offset)
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = width // 2, height // 2
    
    # Draw hook/title (top)
    hook_y = height * 0.15
    hook_font_size = 90 if len(hook) < 15 else 70
    draw_kinetic_text(draw, hook, center_x, hook_y,
                     hook_font_size, colors["primary"], 
                     max(0, time_offset), "pulse")
    
    # Draw verse (middle)
    verse_font_size = 56
    max_line_width = width - 200
    
    # Simple text wrapping
    words = verse.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if len(test_line) > 40:  # Character limit
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw lines with staggered animation
    line_spacing = 75
    verse_start_y = center_y - (len(lines) - 1) * line_spacing // 2
    
    for i, line in enumerate(lines):
        line_y = verse_start_y + i * line_spacing
        line_time = max(0, time_offset - 0.5 - i * 0.2)
        draw_kinetic_text(draw, line, center_x, line_y,
                         verse_font_size, colors["text"], 
                         line_time, "typewriter")
    
    # Draw reference (bottom)
    if ref:
        ref_font_size = 48
        ref_y = height * 0.85
        ref_time = max(0, time_offset - 2)
        
        # Reference background
        ref_font = ImageFont.load_default(ref_font_size)
        bbox = ref_font.getbbox(ref.upper())
        ref_width = bbox[2] - bbox[0]
        
        # Animated background
        bg_alpha = int(200 * min(1.0, ref_time * 2))
        padding = 25
        draw.rounded_rectangle(
            [center_x - ref_width//2 - padding,
             ref_y - padding,
             center_x + ref_width//2 + padding,
             ref_y + bbox[3] - bbox[1] + padding],
            radius=15,
            fill=colors["primary"][:3] + (bg_alpha,)
        )
        
        # Reference text
        text_alpha = int(255 * min(1.0, ref_time * 2))
        draw.text((center_x - ref_width//2, ref_y), ref.upper(),
                 font=ref_font, fill=colors["accent"][:3] + (text_alpha,))
    
    # Watermark (subtle)
    watermark_font = ImageFont.load_default(28)
    draw.text((width - 180, height - 50), "@scripture.motion",
             font=watermark_font, fill=colors["text"][:3] + (100,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_scripture_video(width, height, theme_name, hook, verse, ref):
    """Create video with animated scripture"""
    duration = 7  # Optimal for TikTok
    fps = 30
    
    def make_frame(t):
        img = create_scripture_design(
            width, height, theme_name, hook, verse, ref, t
        )
        return np.array(img.convert("RGB"))
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
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
            preset='ultrafast'
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
st.title("⚡ Scripture Motion Pro")
st.markdown("### TikTok-Ready Scripture Videos • Flat Design • AI-Powered")

# Initialize session
if 'hook' not in st.session_state:
    st.session_state.hook = "BE STILL"
if 'caption' not in st.session_state:
    st.session_state.caption = ""

# Sidebar
with st.sidebar:
    st.markdown("### 🎨 Design")
    
    # Theme selection
    theme_option = st.selectbox(
        "Choose Theme",
        list(EMOTIONAL_THEMES.keys()),
        index=0
    )
    
    theme = EMOTIONAL_THEMES[theme_option]
    emotion = theme["emotion"]
    
    # Show theme preview
    st.markdown(f"""
    <div style="background: rgba{theme['colors']['bg'][:3] + (0.2,)};
                padding: 1rem; border-radius: 10px; margin: 1rem 0;
                border-left: 4px solid rgba{theme['colors']['primary'][:3] + (1,)};">
        <div style="color: rgba{theme['colors']['text'][:3] + (1,)}; font-weight: bold;">
            {theme_option}
        </div>
        <div class="emotion-badge" style="background: rgba{theme['colors']['primary'][:3] + (0.2,)}; 
               color: rgba{theme['colors']['primary'][:3] + (1,)};">
            {emotion.upper()}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Scripture input
    st.markdown("### 📖 Scripture")
    
    verse = st.text_area(
        "Verse Text",
        "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth.",
        height=120
    )
    
    ref = st.text_input(
        "Reference",
        "PSALM 46:10"
    )
    
    st.markdown("---")
    
    # AI Tools
    st.markdown("### 🤖 AI Tools")
    
    if get_groq_client():
        st.success("✅ AI Connected")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Generate Hook", use_container_width=True):
                with st.spinner("Creating..."):
                    hook = generate_ai_hook(verse, theme_option, emotion)
                    st.session_state.hook = hook
                    st.success(f"✓ {hook}")
        
        with col2:
            if st.button("📝 Generate Caption", use_container_width=True):
                with st.spinner("Writing..."):
                    caption = generate_ai_caption(
                        st.session_state.hook, verse, ref, theme_option, emotion
                    )
                    st.session_state.caption = caption
                    st.success("Caption ready!")
    else:
        st.warning("⚠️ Add Groq API key to secrets for AI features")
    
    st.markdown("---")
    
    # Hook input
    hook = st.text_input(
        "Hook/Title",
        value=st.session_state.hook,
        help="Short title (AI can generate this)"
    ).upper()
    
    st.session_state.hook = hook
    
    # Size selection
    st.markdown("---")
    st.markdown("### 📐 Size")
    
    size_option = st.radio(
        "Video Size",
        ["TikTok (1080x1920)", "Instagram (1080x1350)", "Square (1080x1080)"],
        index=0
    )
    
    if "TikTok" in size_option:
        width, height = 1080, 1920
    elif "Instagram" in size_option:
        width, height = 1080, 1350
    else:
        width, height = 1080, 1080
    
    # Animation preview
    st.markdown("---")
    st.markdown("### ⏱️ Preview")
    
    time_slider = st.slider(
        "Animation Time",
        0.0, 7.0, 0.0, 0.1
    )
    
    st.markdown("---")
    
    # Actions
    if st.button("🎬 CREATE VIDEO", type="primary", use_container_width=True):
        st.session_state.create_video = True
    
    if st.button("🖼️ EXPORT IMAGE", use_container_width=True):
        st.session_state.export_image = True

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Live preview
    st.markdown("### 👁️ LIVE PREVIEW")
    
    # Create preview
    preview_width = 400 if height > width else 500
    preview_height = int(preview_width * height / width)
    
    preview_img = create_scripture_design(
        preview_width, preview_height, theme_option, hook, verse, ref, time_slider
    )
    
    st.image(preview_img, use_column_width=True)
    
    # Video generation
    if st.session_state.get('create_video', False):
        with st.spinner("🎬 Creating TikTok-ready video..."):
            video_data = create_scripture_video(
                width, height, theme_option, hook, verse, ref
            )
            
            st.video(video_data)
            
            # Download buttons
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                st.download_button(
                    label="📥 Download MP4",
                    data=video_data,
                    file_name=f"scripture_{theme_option.lower().replace(' ', '_')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            
            with col_v2:
                st.download_button(
                    label="📱 Copy Caption",
                    data=st.session_state.caption,
                    file_name="caption.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        st.session_state.create_video = False
    
    # Image export
    if st.session_state.get('export_image', False):
        with st.spinner("Creating high-quality image..."):
            full_img = create_scripture_design(
                width, height, theme_option, hook, verse, ref, 0
            )
            
            img_buffer = io.BytesIO()
            full_img.save(img_buffer, format='PNG', optimize=True, quality=95)
            
            st.download_button(
                label="📥 Download PNG",
                data=img_buffer.getvalue(),
                file_name=f"scripture_{theme_option.lower().replace(' ', '_')}.png",
                mime="image/png",
                use_container_width=True
            )
        
        st.session_state.export_image = False

with col2:
    # Features & Info
    st.markdown("### ⚡ FEATURES")
    
    features = [
        "🎨 **4 Emotional Themes** - Each with unique animations",
        "🌀 **Animated Backgrounds** - Flat design with movement",
        "✍️ **Kinetic Typography** - Typewriter, fade, pulse effects",
        "🤖 **AI-Powered** - Auto-generate hooks & captions",
        "📱 **TikTok Optimized** - Perfect 9:16 vertical format",
        "⚡ **Fast Export** - Ready in seconds, not minutes"
    ]
    
    for feature in features:
        st.markdown(f"• {feature}")
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 QUICK STATS")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Theme", theme_option)
        st.metric("Emotion", emotion.title())
    
    with col_s2:
        st.metric("Size", f"{width}×{height}")
        st.metric("AI", "✅ ON" if get_groq_client() else "⚠️ OFF")
    
    st.markdown("---")
    
    # Quick templates
    st.markdown("### ⚡ QUICK TEMPLATES")
    
    if st.button("🌅 Morning Devotional", use_container_width=True):
        theme_option = "Morning Calm"
        hook = "NEW MERCIES"
        verse = "The steadfast love of the Lord never ceases; his mercies never come to an end; they are new every morning; great is your faithfulness."
        ref = "LAMENTATIONS 3:22-23"
        st.rerun()
    
    if st.button("🌙 Evening Peace", use_container_width=True):
        theme_option = "Night Stillness"
        hook = "PEACEFUL NIGHT"
        verse = "In peace I will lie down and sleep, for you alone, Lord, make me dwell in safety."
        ref = "PSALM 4:8"
        st.rerun()
    
    if st.button("🌿 Psalm 23", use_container_width=True):
        theme_option = "Forest Peace"
        hook = "MY SHEPHERD"
        verse = "The Lord is my shepherd, I lack nothing. He makes me lie down in green pastures, he leads me beside quiet waters, he refreshes my soul."
        ref = "PSALM 23:1-3"
        st.rerun()
    
    st.markdown("---")
    
    # Caption preview
    if st.session_state.caption:
        st.markdown("### 📝 CAPTION PREVIEW")
        st.text_area("Ready to Copy:", st.session_state.caption, height=150)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>⚡ Scripture Motion Pro • Made for TikTok Growth • Flat Design Animations</p>
    <p>Create 30+ videos per hour • Post 3x daily • Grow your following</p>
</div>
""", unsafe_allow_html=True)