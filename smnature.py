import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math, time, json, requests, textwrap
import numpy as np
from moviepy.editor import VideoClip
import tempfile
from groq import Groq

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Still Mind Nature",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# BRAND COLOR PALETTE (Green, Navy Blue, White, Grey)
# ============================================================================
BRAND_COLORS = {
    "primary_green": (76, 175, 80, 255),        # #4CAF50
    "primary_green_light": (129, 199, 132, 255),  # #81C784
    "primary_green_dark": (56, 142, 60, 255),   # #388E3C
    
    "primary_navy": (13, 71, 161, 255),         # #0D47A1
    "primary_navy_light": (66, 165, 245, 255),  # #42A5F5
    "primary_navy_dark": (5, 35, 80, 255),      # #052350
    
    "white": (255, 255, 255, 255),              # #FFFFFF
    "white_warm": (250, 250, 245, 255),         # #FAFAF5

    "grey_lighter": (245, 245, 245, 255),         # #BDBDBD
    "grey_light": (189, 189, 189, 255),         # #BDBDBD
    "grey_medium": (117, 117, 117, 255),        # #757575
    "grey_dark": (66, 66, 66, 255),             # #424242
    "grey_darker": (33, 33, 33, 255)            # #212121
}

# ============================================================================
# NATURE THEMES WITH FLAT DESIGN
# ============================================================================
NATURE_THEMES = {
    "Sunset Valley": {
        "background": BRAND_COLORS["primary_navy_dark"],
        "sky_gradient": [
            BRAND_COLORS["primary_navy"],
            BRAND_COLORS["primary_navy_light"],
            (255, 193, 7, 255)  # Sunset yellow
        ],
        "ground": BRAND_COLORS["grey_dark"],
        "accents": [
            BRAND_COLORS["primary_green"],
            (255, 152, 0, 255)  # Orange accent
        ],
        "text_color": BRAND_COLORS["white"]
    },
    "Mountain Stream": {
        "background": BRAND_COLORS["grey_lighter"],
        "sky_gradient": [
            BRAND_COLORS["primary_navy_light"],
            BRAND_COLORS["white_warm"]
        ],
        "ground": BRAND_COLORS["primary_green_dark"],
        "water": BRAND_COLORS["primary_navy_light"],
        "accents": [
            BRAND_COLORS["primary_green"],
            BRAND_COLORS["grey_medium"]
        ],
        "text_color": BRAND_COLORS["grey_darker"]
    },
    "Desert Dunes": {
        "background": (255, 243, 224, 255),  # Sand color
        "sky_gradient": [
            BRAND_COLORS["primary_navy_light"],
            (255, 224, 178, 255)  # Light sand
        ],
        "ground": (216, 67, 21, 255),  # Terracotta
        "accents": [
            BRAND_COLORS["primary_green"],
            BRAND_COLORS["grey_dark"]
        ],
        "text_color": BRAND_COLORS["grey_darker"]
    },
    "Forest Path": {
        "background": BRAND_COLORS["primary_green_dark"],
        "sky_gradient": [
            BRAND_COLORS["primary_navy"],
            BRAND_COLORS["primary_green_light"]
        ],
        "ground": BRAND_COLORS["grey_dark"],
        "accents": [
            BRAND_COLORS["primary_green_light"],
            BRAND_COLORS["white"]
        ],
        "text_color": BRAND_COLORS["white"]
    }
}

# ============================================================================
# BIBLE API FUNCTION
# ============================================================================
@st.cache_data(ttl=3600)
def get_bible_verse(book, chapter, verse):
    """Fetch Bible verse from API with fallback."""
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            text = data.get("text", "").replace("\n", " ").strip()
            reference = data.get("reference", f"{book} {chapter}:{verse}")
            return text, reference
    except Exception as e:
        st.warning(f"Could not fetch verse from API: {str(e)}")
    
    # Fallback verses
    fallback_verses = [
        "Be still, and know that I am God.",
        "The Lord is my shepherd; I shall not want.",
        "I can do all things through Christ who strengthens me.",
        "Peace I leave with you; my peace I give to you.",
        "For God so loved the world that he gave his only Son."
    ]
    
    # Get a consistent fallback based on book/chapter/verse
    index = (hash(f"{book}{chapter}{verse}") % len(fallback_verses))
    return fallback_verses[index], f"{book} {chapter}:{verse}"

# ============================================================================
# GROQ AI INTEGRATION
# ============================================================================
def get_groq_client():
    """Initialize Groq client with API key from secrets."""
    try:
        api_key = st.secrets.get("groq_key")
        if not api_key:
            st.error("Groq API key not found in secrets. Please add 'groq_key' to your secrets.toml file.")
            return None
        return Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Groq client: {str(e)}")
        return None

def generate_hook_with_ai(verse_text, theme_name):
    """Generate a creative hook/title using AI."""
    client = get_groq_client()
    if not client:
        return "STILL MIND"
    
    try:
        prompt = f"""Generate a short, powerful title (max 3 words) for a scripture graphic.
        Verse: {verse_text}
        Theme: {theme_name}
        Style: Modern, spiritual, minimal
        
        Requirements:
        - 1-3 words maximum
        - Title case
        - No quotation marks
        - Relevant to the verse
        - Works as social media hook
        
        Examples:
        "Be Still" for Psalm 46:10
        "Peace Like A River" for Isaiah 26:3
        "Morning Grace" for Lamentations 3:22-23
        
        Title:"""
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.7
        )
        
        hook = response.choices[0].message.content.strip()
        # Clean up the response
        hook = hook.replace('"', '').replace("'", "").strip()
        if len(hook.split()) > 5:  # If too long, fallback
            return "STILL MIND"
        return hook.upper()
        
    except Exception as e:
        st.warning(f"AI hook generation failed: {str(e)}")
        return "STILL MIND"

def generate_social_caption_with_ai(verse_text, reference, hook, theme_name):
    """Generate social media caption using AI."""
    client = get_groq_client()
    if not client:
        return f"{hook}\n\n{verse_text[:100]}...\n\n{reference}\n\n#StillMind #Scripture #Faith"
    
    try:
        prompt = f"""Generate a social media caption for a scripture graphic.
        
        Hook/Title: {hook}
        Verse: {verse_text}
        Reference: {reference}
        Theme: {theme_name}
        
        Requirements:
        - Include 3-5 relevant hashtags
        - Format: Hook first, then verse excerpt (1-2 lines), then reference, then hashtags
        - Keep under 220 characters
        - Make it engaging and shareable
        - Add a call to action if appropriate
        
        Caption:"""
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        caption = response.choices[0].message.content.strip()
        return caption
        
    except Exception as e:
        st.warning(f"AI caption generation failed: {str(e)}")
        # Fallback caption
        return f"""{hook}

{verse_text[:100]}...

📖 {reference}

#StillMind #Scripture #Faith #{theme_name.replace(' ', '')}"""

# ============================================================================
# FLAT NATURE BACKGROUND GENERATORS
# ============================================================================
def create_flat_background(width, height, theme, time_offset=0):
    """Create flat design nature background."""
    colors = theme
    
    img = Image.new("RGBA", (width, height), colors["background"])
    draw = ImageDraw.Draw(img)
    
    # Draw sky gradient
    gradient_height = height * 0.6
    gradient_colors = colors.get("sky_gradient", [colors["background"], colors["background"]])
    
    if len(gradient_colors) > 1:
        for y in range(int(gradient_height)):
            ratio = y / gradient_height
            if len(gradient_colors) == 2:
                r = int(gradient_colors[0][0] * (1-ratio) + gradient_colors[1][0] * ratio)
                g = int(gradient_colors[0][1] * (1-ratio) + gradient_colors[1][1] * ratio)
                b = int(gradient_colors[0][2] * (1-ratio) + gradient_colors[1][2] * ratio)
            else:  # 3 colors
                if ratio < 0.5:
                    r = int(gradient_colors[0][0] * (1-ratio*2) + gradient_colors[1][0] * (ratio*2))
                    g = int(gradient_colors[0][1] * (1-ratio*2) + gradient_colors[1][1] * (ratio*2))
                    b = int(gradient_colors[0][2] * (1-ratio*2) + gradient_colors[1][2] * (ratio*2))
                else:
                    r = int(gradient_colors[1][0] * (2-ratio*2) + gradient_colors[2][0] * (ratio*2-1))
                    g = int(gradient_colors[1][1] * (2-ratio*2) + gradient_colors[2][1] * (ratio*2-1))
                    b = int(gradient_colors[1][2] * (2-ratio*2) + gradient_colors[2][2] * (ratio*2-1))
            
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    
    # Draw ground
    ground_y = int(height * 0.6)
    draw.rectangle([0, ground_y, width, height], fill=colors.get("ground", colors["background"]))
    
    # Theme-specific elements
    theme_name = list(NATURE_THEMES.keys())[list(NATURE_THEMES.values()).index(theme)]
    
    if "Sunset" in theme_name:
        # Draw flat sun
        sun_size = 80
        sun_x = width * 0.8
        sun_y = height * 0.2
        
        # Sun glow (layered circles)
        for i in range(3, 0, -1):
            glow_size = sun_size + i * 20
            glow_alpha = 100 - i * 30
            draw.ellipse([sun_x-glow_size, sun_y-glow_size, 
                         sun_x+glow_size, sun_y+glow_size],
                        fill=colors["accents"][1][:3] + (glow_alpha,))
        
        # Sun body
        draw.ellipse([sun_x-sun_size, sun_y-sun_size, 
                     sun_x+sun_size, sun_y+sun_size],
                    fill=colors["accents"][1])
        
        # Distant hills
        for i in range(3):
            hill_height = 40 + i * 20
            hill_width = 300 + i * 100
            hill_x = width * 0.1 + i * 150 + math.sin(time_offset + i) * 20
            hill_y = ground_y - hill_height
            
            points = [
                (hill_x, hill_y),
                (hill_x + hill_width * 0.3, hill_y - hill_height * 0.5),
                (hill_x + hill_width * 0.7, hill_y - hill_height * 0.3),
                (hill_x + hill_width, hill_y),
                (hill_x + hill_width, ground_y),
                (hill_x, ground_y)
            ]
            
            hill_color = tuple(max(0, c-30*i) for c in colors["ground"][:3]) + (255,)
            draw.polygon(points, fill=hill_color)
    
    elif "Mountain" in theme_name:
        # Draw flat mountains
        for i in range(4):
            mountain_width = 300 + i * 50
            mountain_height = 80 + i * 30
            mountain_x = width * (0.1 + i * 0.2) + math.sin(time_offset + i) * 15
            mountain_y = ground_y - mountain_height
            
            # Mountain shape (triangle)
            points = [
                (mountain_x, mountain_y + mountain_height),
                (mountain_x + mountain_width//2, mountain_y),
                (mountain_x + mountain_width, mountain_y + mountain_height)
            ]
            
            mountain_color = tuple(max(0, c-20*i) for c in colors["ground"][:3]) + (255,)
            draw.polygon(points, fill=mountain_color)
            
            # Snow caps on taller mountains
            if i > 1:
                snow_height = 20
                snow_points = [
                    (mountain_x + mountain_width//2 - 30, mountain_y + snow_height),
                    (mountain_x + mountain_width//2, mountain_y),
                    (mountain_x + mountain_width//2 + 30, mountain_y + snow_height)
                ]
                draw.polygon(snow_points, fill=BRAND_COLORS["white"])
        
        # Draw river
        if "water" in colors:
            river_width = 150
            river_x = width // 2 - river_width // 2
            river_points = [
                (river_x, ground_y),
                (river_x + river_width, ground_y),
                (river_x + river_width*0.7, height),
                (river_x + river_width*0.3, height)
            ]
            draw.polygon(river_points, fill=colors["water"])
            
            # River flow lines
            for i in range(5):
                flow_y = ground_y + i * 30
                flow_wave = math.sin(time_offset * 2 + i) * 20
                draw.line([(river_x + 20, flow_y + flow_wave),
                          (river_x + river_width - 20, flow_y + flow_wave)],
                         fill=BRAND_COLORS["primary_navy_dark"], width=2)
    
    elif "Desert" in theme_name:
        # Draw sand dunes
        for i in range(5):
            dune_width = 400
            dune_height = 60 + i * 15
            dune_x = width * (0.05 + i * 0.18) - (time_offset * 50) % width
            dune_y = ground_y + i * 40
            
            # Dune shape (curved)
            points = []
            for x in range(0, dune_width + 20, 20):
                x_pos = dune_x + x
                y_pos = dune_y + dune_height * math.sin(x / dune_width * math.pi)
                points.append((x_pos, y_pos))
            
            # Close the shape
            points.append((dune_x + dune_width, height))
            points.append((dune_x, height))
            
            dune_color = tuple(min(255, c + 20*i) for c in colors["ground"][:3]) + (255,)
            draw.polygon(points, fill=dune_color)
        
        # Draw cactus
        cactus_x = width * 0.7
        cactus_y = ground_y + 50
        cactus_width = 30
        cactus_height = 120
        
        # Cactus body
        draw.rounded_rectangle([cactus_x-cactus_width//2, cactus_y,
                               cactus_x+cactus_width//2, cactus_y+cactus_height],
                              radius=15, fill=BRAND_COLORS["primary_green_dark"])
        
        # Cactus arms
        draw.rounded_rectangle([cactus_x-cactus_width//2, cactus_y+40,
                               cactus_x-cactus_width//2-40, cactus_y+80],
                              radius=10, fill=BRAND_COLORS["primary_green_dark"])
        draw.rounded_rectangle([cactus_x+cactus_width//2, cactus_y+60,
                               cactus_x+cactus_width//2+40, cactus_y+100],
                              radius=10, fill=BRAND_COLORS["primary_green_dark"])
    
    elif "Forest" in theme_name:
        # Draw trees
        for i in range(8):
            tree_x = width * (0.1 + i * 0.11) + math.sin(time_offset + i) * 10
            tree_y = ground_y
            
            # Tree trunk
            trunk_height = 80 + i * 10
            trunk_width = 15 + i * 2
            draw.rectangle([tree_x-trunk_width//2, tree_y,
                           tree_x+trunk_width//2, tree_y-trunk_height],
                          fill=BRAND_COLORS["grey_dark"])
            
            # Tree foliage (layered circles)
            for j in range(3):
                foliage_size = 40 - j * 10
                foliage_y = tree_y - trunk_height - j * 25
                draw.ellipse([tree_x-foliage_size, foliage_y-foliage_size,
                            tree_x+foliage_size, foliage_y+foliage_size],
                           fill=BRAND_COLORS["primary_green"][:3] + (200 - j*50,))
    
    return img

# ============================================================================
# TEXT ANIMATION FUNCTIONS
# ============================================================================
def draw_typewriter_text(draw, text, font, x, y, max_width, t, duration=4):
    """Draw text with typewriter animation."""
    progress = min(1.0, t / duration)
    visible_chars = int(len(text) * progress)
    visible_text = text[:visible_chars]
    
    # Wrap text
    words = visible_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw lines
    line_height = font.size * 1.4
    current_y = y
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        line_x = x + (max_width - text_width) // 2
        
        draw.text((line_x, current_y), line, font=font, fill=BRAND_COLORS["white"])
        current_y += line_height
    
    # Draw blinking cursor
    if progress < 1.0 and int(t * 3) % 2 == 0:
        if lines:
            last_line = lines[-1]
            bbox = draw.textbbox((0, 0), last_line, font=font)
            cursor_x = x + (max_width - (bbox[2] - bbox[0])) // 2 + (bbox[2] - bbox[0]) + 5
            cursor_y = current_y - line_height + 10
            draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + line_height - 20)],
                     fill=BRAND_COLORS["primary_green"], width=3)
    
    return current_y

def draw_static_text(draw, text, font, x, y, max_width, color):
    """Draw static wrapped text."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    line_height = font.size * 1.4
    current_y = y
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        line_x = x + (max_width - text_width) // 2
        
        draw.text((line_x, current_y), line, font=font, fill=color)
        current_y += line_height
    
    return current_y

# ============================================================================
# FONT MANAGEMENT
# ============================================================================
def load_font(size, bold=False):
    """Load font with fallbacks."""
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

# ============================================================================
# MAIN COMPOSITION FUNCTION
# ============================================================================
def create_nature_design(width, height, theme_name, book, chapter, verse, 
                        hook_text, t=0, is_video=False):
    """Create complete nature design with scripture."""
    theme = NATURE_THEMES[theme_name]
    
    # Create background
    img = create_flat_background(width, height, theme, t)
    draw = ImageDraw.Draw(img)
    
    # Get verse text
    verse_text, reference = get_bible_verse(book, chapter, verse)
    
    # Content panel
    panel_width = min(900, width - 100)
    panel_height = 500
    panel_x = (width - panel_width) // 2
    panel_y = (height - panel_height) // 2 - 50
    
    # Semi-transparent panel background
    panel_bg = Image.new("RGBA", (panel_width, panel_height), (0, 0, 0, 180))
    img.paste(panel_bg, (panel_x, panel_y), panel_bg)
    
    # Panel border
    draw.rounded_rectangle([panel_x-5, panel_y-5, 
                           panel_x+panel_width+5, panel_y+panel_height+5],
                          radius=10, outline=BRAND_COLORS["primary_green"], width=3)
    
    # Load fonts
    hook_font = load_font(64, bold=True)
    verse_font = load_font(48, bold=False)
    ref_font = load_font(36, bold=True)
    
    # Draw hook/title
    if hook_text:
        hook_bbox = draw.textbbox((0, 0), hook_text, font=hook_font)
        hook_width = hook_bbox[2] - hook_bbox[0]
        hook_x = panel_x + (panel_width - hook_width) // 2
        hook_y = panel_y - 100
        
        # Hook background
        draw.rectangle([hook_x-20, hook_y-15, 
                       hook_x+hook_width+20, hook_y+hook_font.size+15],
                      fill=BRAND_COLORS["primary_green"])
        
        # Hook text
        draw.text((hook_x, hook_y), hook_text, font=hook_font, 
                 fill=BRAND_COLORS["white"])
    
    # Draw verse text
    text_max_width = panel_width - 80
    text_start_y = panel_y + 60
    
    if is_video:
        # Typewriter animation
        final_y = draw_typewriter_text(
            draw, verse_text, verse_font, 
            panel_x + 40, text_start_y, text_max_width, t
        )
    else:
        # Static text
        final_y = draw_static_text(
            draw, verse_text, verse_font,
            panel_x + 40, text_start_y, text_max_width,
            theme["text_color"]
        )
    
    # Draw reference
    ref_bbox = draw.textbbox((0, 0), reference, font=ref_font)
    ref_width = ref_bbox[2] - ref_bbox[0]
    ref_x = panel_x + panel_width - ref_width - 40
    ref_y = final_y + 40
    
    if is_video:
        # Fade in reference
        ref_alpha = int(255 * max(0, min(1.0, (t - 3.5) / 1)))
        if ref_alpha > 0:
            ref_color = BRAND_COLORS["primary_green_light"][:3] + (ref_alpha,)
            draw.text((ref_x, ref_y), reference, font=ref_font, fill=ref_color)
    else:
        # Static reference
        ref_bg_width = ref_width + 30
        ref_bg_height = ref_font.size + 20
        draw.rounded_rectangle([ref_x-15, ref_y-10,
                               ref_x+ref_width+15, ref_y+ref_bg_height],
                              radius=8, fill=BRAND_COLORS["primary_green"])
        draw.text((ref_x, ref_y), reference, font=ref_font, 
                 fill=BRAND_COLORS["white"])
    
    # Brand watermark
    watermark_font = load_font(28, bold=True)
    draw.text((width - 200, 30), "STILL MIND", font=watermark_font,
             fill=BRAND_COLORS["white"][:3] + (150,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_nature_video(width, height, theme_name, book, chapter, verse, hook_text):
    """Create animated video."""
    duration = 6
    fps = 24
    
    def make_frame(t):
        img = create_nature_design(
            width, height, theme_name, book, chapter, verse,
            hook_text, t, True
        )
        return np.array(img.convert("RGB"))
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
    # Create temporary file
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
st.title("🌿 Still Mind: Flat Nature Studio")
st.markdown("### Create beautiful scripture graphics with flat nature designs")

# Sidebar
with st.sidebar:
    st.header("🎨 Design Settings")
    
    # Theme selection
    theme_option = st.selectbox(
        "Nature Theme",
        list(NATURE_THEMES.keys()),
        help="Choose a nature theme for your design"
    )
    
    # Size selection
    size_option = st.selectbox(
        "Output Size",
        ["Instagram (1080x1080)", "TikTok (1080x1920)", "Stories (1080x1350)"]
    )
    
    if "1920" in size_option:
        WIDTH, HEIGHT = 1080, 1920
    elif "1350" in size_option:
        WIDTH, HEIGHT = 1080, 1350
    else:
        WIDTH, HEIGHT = 1080, 1080
    
    st.divider()
    
    st.header("📖 Scripture")
    
    # Bible book selection
    bible_books = ["Psalm", "Matthew", "John", "Isaiah", "Romans", 
                   "Philippians", "James", "Proverbs", "Ecclesiastes",
                   "Genesis", "Exodus", "Deuteronomy", "Ephesians"]
    
    book = st.selectbox("Book", bible_books, index=0)
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 46, 
                                 help="Bible chapter number")
    with col2:
        verse = st.number_input("Verse", 1, 176, 10, 
                               help="Bible verse number")
    
    # Get verse text for preview
    verse_text, reference = get_bible_verse(book, chapter, verse)
    
    st.write(f"**Preview:** {verse_text[:80]}...")
    
    st.divider()
    
    st.header("🪄 AI Tools")
    
    # Generate hook with AI
    if st.button("🤖 Generate Hook with AI", use_container_width=True):
        with st.spinner("Generating creative hook..."):
            hook_text = generate_hook_with_ai(verse_text, theme_option)
            st.session_state.hook_text = hook_text
            st.success(f"Generated: {hook_text}")
    
    # Manual hook input
    hook_text = st.text_input(
        "Hook/Title",
        value=st.session_state.get("hook_text", "BE STILL"),
        help="Short title for your graphic"
    ).upper()
    
    st.divider()
    
    st.header("⏱️ Animation Preview")
    time_slider = st.slider(
        "Time",
        0.0, 6.0, 0.0, 0.1,
        help="Drag to preview animation at different times"
    )

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Preview section
    st.subheader("🎨 Live Preview")
    
    with st.spinner("Creating design..."):
        preview_img = create_nature_design(
            WIDTH, HEIGHT, theme_option, book, chapter, verse,
            hook_text, time_slider, False
        )
    
    # FIXED: Removed use_container_width parameter
    st.image(preview_img)
    
    # Action buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # Download PNG
        img_buffer = io.BytesIO()
        preview_img.save(img_buffer, format='PNG', optimize=True, quality=95)
        
        st.download_button(
            label="📥 Download PNG",
            data=img_buffer.getvalue(),
            file_name=f"still_mind_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Create Video (6s)", use_container_width=True):
            with st.spinner("Creating animated video..."):
                video_data = create_nature_video(
                    WIDTH, HEIGHT, theme_option, book, chapter, verse, hook_text
                )
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download button
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"still_mind_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    # Info panel
    st.subheader("ℹ️ Design Info")
    
    st.write("**Theme:**")
    st.success(theme_option)
    
    st.write("**Verse:**")
    st.info(f"{book} {chapter}:{verse}")
    
    st.write("**Size:**")
    st.metric("Dimensions", f"{WIDTH} × {HEIGHT}")
    
    st.divider()
    
    # Social media section
    st.subheader("📱 Social Media")
    
    # Generate caption with AI
    if st.button("🤖 Generate Social Caption", use_container_width=True):
        with st.spinner("Creating optimized caption..."):
            caption = generate_social_caption_with_ai(
                verse_text, reference, hook_text, theme_option
            )
            st.session_state.caption = caption
            st.success("Caption generated!")
    
    # Display caption
    caption = st.session_state.get("caption", "")
    if not caption:
        # Default caption
        caption = f"""{hook_text}

{verse_text[:100]}...

📖 {reference}

#StillMind #Scripture #Faith #{theme_option.replace(' ', '')}"""
        st.session_state.caption = caption
    
    st.text_area("Social Media Caption", caption, height=200)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Copied to clipboard!")
    
    st.divider()
    
    # Color palette preview
    st.subheader("🎨 Color Palette")
    
    colors = BRAND_COLORS
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Greens:**")
        st.markdown(f'<div style="background-color:rgb{colors["primary_green"][:3]}; height:30px; border-radius:5px;"></div>', 
                   unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:rgb{colors["primary_green_light"][:3]}; height:30px; border-radius:5px; margin-top:5px;"></div>', 
                   unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:rgb{colors["primary_green_dark"][:3]}; height:30px; border-radius:5px; margin-top:5px;"></div>', 
                   unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Blues:**")
        st.markdown(f'<div style="background-color:rgb{colors["primary_navy"][:3]}; height:30px; border-radius:5px;"></div>', 
                   unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:rgb{colors["primary_navy_light"][:3]}; height:30px; border-radius:5px; margin-top:5px;"></div>', 
                   unsafe_allow_html=True)
        st.markdown(f'<div style="background-color:rgb{colors["primary_navy_dark"][:3]}; height:30px; border-radius:5px; margin-top:5px;"></div>', 
                   unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #4CAF50; font-size: 0.9rem;'>
    <p>🌿 Still Mind Nature Studio • Flat Design • Brand Colors: Green, Navy Blue, White, Grey</p>
    <p>Bible API Integration • Groq AI • Typewriter Animation • Social Media Ready</p>
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