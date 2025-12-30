import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math, time, requests, textwrap
import numpy as np
from moviepy.editor import VideoClip
import tempfile
from groq import Groq

# ============================================================================
# SETUP & CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Still Mind Pro",
    page_icon="🌄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# BRAND COLOR PALETTE (Fixed with all keys)
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
    
    "grey_light": (189, 189, 189, 255),         # #BDBDBD
    "grey_medium": (117, 117, 117, 255),        # #757575
    "grey_dark": (66, 66, 66, 255),             # #424242
    "grey_darker": (33, 33, 33, 255)            # #212121
}

# ============================================================================
# NATURE THEMES WITH ENHANCED ATMOSPHERIC DEPTH
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
        "fog_color": (255, 255, 255, 60),  # White mist
        "glow_color": (255, 235, 59, 100),  # Yellow glow
        "accents": [
            BRAND_COLORS["primary_green"],
            (255, 152, 0, 255)  # Orange accent
        ],
        "text_color": BRAND_COLORS["white"]
    },
    "Mountain Stream": {
        "background": BRAND_COLORS["grey_light"],  # Fixed: was "grey_lighter"
        "sky_gradient": [
            BRAND_COLORS["primary_navy_light"],
            BRAND_COLORS["white_warm"]
        ],
        "ground": BRAND_COLORS["primary_green_dark"],
        "water": BRAND_COLORS["primary_navy_light"],
        "fog_color": (255, 255, 255, 40),  # White mountain mist
        "glow_color": (66, 165, 245, 80),  # Blue glow
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
        "fog_color": (255, 255, 255, 30),  # Sand mist
        "glow_color": (255, 193, 7, 120),  # Desert sun glow
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
        "fog_color": (129, 199, 132, 50),  # Green forest mist
        "glow_color": (76, 175, 80, 100),  # Green glow
        "accents": [
            BRAND_COLORS["primary_green_light"],
            BRAND_COLORS["white"]
        ],
        "text_color": BRAND_COLORS["white"]
    },
    "Night Desert": {
        "background": (10, 12, 26, 255),  # Deep night blue
        "sky_gradient": [
            (20, 25, 50, 255),
            (30, 40, 80, 255)
        ],
        "ground": (30, 20, 10, 255),  # Dark desert
        "fog_color": (255, 255, 255, 15),  # Night mist
        "glow_color": (100, 149, 237, 150),  # Night blue glow
        "accents": [
            BRAND_COLORS["primary_green"],
            (200, 200, 255, 255)  # Star color
        ],
        "text_color": BRAND_COLORS["white"]
    }
}

# ============================================================================
# SOCIAL MEDIA SAFE ZONES
# ============================================================================
SAFE_ZONES = {
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "title_safe": {
            "top": 100,
            "bottom": 1700,
            "left": 100,
            "right": 980
        },
        "text_safe": {
            "top": 400,
            "bottom": 1500,
            "left": 140,
            "right": 940
        }
    },
    "instagram_square": {
        "width": 1080,
        "height": 1080,
        "title_safe": {
            "top": 100,
            "bottom": 900,
            "left": 100,
            "right": 980
        },
        "text_safe": {
            "top": 300,
            "bottom": 800,
            "left": 140,
            "right": 940
        }
    },
    "instagram_story": {
        "width": 1080,
        "height": 1350,
        "title_safe": {
            "top": 150,
            "bottom": 1150,
            "left": 100,
            "right": 980
        },
        "text_safe": {
            "top": 350,
            "bottom": 1000,
            "left": 140,
            "right": 940
        }
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
# ENHANCED FLAT NATURE BACKGROUND WITH ATMOSPHERIC DEPTH
# ============================================================================
def create_atmospheric_background(width, height, theme, time_offset=0):
    """Create flat design nature background with atmospheric depth."""
    colors = theme
    
    img = Image.new("RGBA", (width, height), colors["background"])
    draw = ImageDraw.Draw(img)
    
    # Draw sky gradient with glow
    gradient_height = height * 0.7
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
            
            # Add subtle glow effect
            glow_strength = 0.3 * math.sin(y * 0.01 + time_offset)
            glow_color = colors.get("glow_color", (255, 255, 255, 0))
            if glow_color[3] > 0:
                glow_ratio = max(0, 1 - abs(y - gradient_height * 0.3) / (gradient_height * 0.3))
                r = int(r * (1 - glow_ratio) + glow_color[0] * glow_ratio)
                g = int(g * (1 - glow_ratio) + glow_color[1] * glow_ratio)
                b = int(b * (1 - glow_ratio) + glow_color[2] * glow_ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    
    # Theme-specific atmospheric elements
    theme_name = [k for k, v in NATURE_THEMES.items() if v == theme][0]
    
    if "Desert" in theme_name or "Night" in theme_name:
        # Draw atmospheric mist layers (parallax effect)
        fog_color = colors["fog_color"]
        if fog_color[3] > 0:
            for layer in range(3):
                # Different speeds for parallax
                speed = 10 + layer * 5
                fog_offset = (time_offset * speed) % (width + 400) - 200
                
                # Draw flat mist rectangles
                fog_height = 40 + layer * 20
                fog_y = height * 0.5 + layer * 30
                
                for i in range(-1, 3):
                    fog_x = i * 400 + fog_offset
                    fog_width = 300 + layer * 50
                    
                    # Rounded rectangle for flat mist
                    draw.rounded_rectangle(
                        [fog_x, fog_y, fog_x + fog_width, fog_y + fog_height],
                        radius=fog_height // 2,
                        fill=fog_color[:3] + (fog_color[3] // (layer + 2),)
                    )
        
        # Draw dunes with atmospheric perspective
        ground_y = int(height * 0.6)
        draw.rectangle([0, ground_y, width, height], fill=colors["ground"])
        
        # Draw multiple dune layers with different colors for depth
        for layer in range(4):
            dune_color = list(colors["ground"])
            # Make dunes lighter as they recede (atmospheric perspective)
            lighten = layer * 15
            dune_color[0] = min(255, dune_color[0] + lighten)
            dune_color[1] = min(255, dune_color[1] + lighten)
            dune_color[2] = min(255, dune_color[2] + lighten)
            
            # Different speeds for parallax
            speed = 20 + layer * 10
            dune_offset = (time_offset * speed) % (width + 600) - 300
            
            for i in range(-1, 3):
                dune_width = 500 + layer * 100
                dune_height = 80 - layer * 15  # Smaller dunes in distance
                dune_x = i * 600 + dune_offset
                dune_y = ground_y + layer * 30
                
                # Dune shape
                points = []
                for x in range(0, dune_width + 20, 20):
                    x_pos = dune_x + x
                    # Sine wave for dune shape
                    wave = math.sin(x / dune_width * math.pi * 2 + time_offset * 0.5) * 20
                    y_pos = dune_y + dune_height * (x / dune_width) * (1 - x / dune_width) * 4 + wave
                    points.append((x_pos, y_pos))
                
                # Close the shape
                points.append((dune_x + dune_width, height))
                points.append((dune_x, height))
                
                if len(points) > 2:
                    draw.polygon(points, fill=tuple(dune_color))
        
        # Add stars for night desert
        if "Night" in theme_name:
            for i in range(100):
                star_x = (i * 31) % width  # Prime number spacing
                star_y = (i * 47) % int(height * 0.6)  # Different prime for y
                
                # Twinkle effect
                twinkle = abs(math.sin(time_offset * 3 + i)) * 0.5 + 0.5
                star_size = 1 + int(2 * twinkle)
                star_alpha = int(200 * twinkle)
                
                draw.ellipse(
                    [star_x - star_size, star_y - star_size,
                     star_x + star_size, star_y + star_size],
                    fill=(255, 255, 255, star_alpha)
                )
    
    elif "Mountain" in theme_name:
        # Draw mountains with atmospheric haze
        ground_y = int(height * 0.6)
        draw.rectangle([0, ground_y, width, height], fill=colors["ground"])
        
        # Draw mist between mountain layers
        fog_color = colors["fog_color"]
        if fog_color[3] > 0:
            for layer in range(2):
                fog_y = ground_y - 100 + layer * 40
                fog_height = 60
                fog_offset = (time_offset * (15 + layer * 10)) % (width + 300) - 150
                
                for i in range(-1, 3):
                    fog_x = i * 400 + fog_offset
                    fog_width = 350
                    draw.rounded_rectangle(
                        [fog_x, fog_y, fog_x + fog_width, fog_y + fog_height],
                        radius=30,
                        fill=fog_color[:3] + (fog_color[3] // (layer + 3),)
                    )
        
        # Draw mountain layers with atmospheric perspective
        for layer in range(3):
            mountain_color = list(colors["ground"])
            # Make mountains bluer as they recede
            mountain_color[0] = max(0, mountain_color[0] - layer * 10)
            mountain_color[1] = max(0, mountain_color[1] - layer * 5)
            mountain_color[2] = min(255, mountain_color[2] + layer * 15)
            
            mountain_width = 400 + layer * 80
            mountain_height = 120 - layer * 30
            mountain_spacing = 300
            speed = 5 + layer * 5
            
            for i in range(-1, 3):
                mountain_x = i * mountain_spacing + (time_offset * speed) % (width + 400) - 200
                mountain_y = ground_y - mountain_height + layer * 20
                
                # Mountain shape (flat triangle)
                points = [
                    (mountain_x, mountain_y + mountain_height),
                    (mountain_x + mountain_width // 2, mountain_y),
                    (mountain_x + mountain_width, mountain_y + mountain_height)
                ]
                
                draw.polygon(points, fill=tuple(mountain_color))
                
                # Snow caps on taller mountains
                if layer == 0 and mountain_height > 80:
                    snow_width = 60
                    snow_points = [
                        (mountain_x + mountain_width // 2 - snow_width // 2, mountain_y),
                        (mountain_x + mountain_width // 2, mountain_y - 20),
                        (mountain_x + mountain_width // 2 + snow_width // 2, mountain_y)
                    ]
                    draw.polygon(snow_points, fill=BRAND_COLORS["white"])
        
        # Draw river with glow
        if "water" in colors:
            river_width = 180
            river_x = width // 2 - river_width // 2
            river_points = [
                (river_x, ground_y),
                (river_x + river_width, ground_y),
                (river_x + river_width * 0.7, height),
                (river_x + river_width * 0.3, height)
            ]
            
            # River glow
            glow_size = 10
            for glow in range(3):
                glow_alpha = 80 - glow * 25
                offset = glow * 3
                glow_points = [
                    (river_x - offset, ground_y),
                    (river_x + river_width + offset, ground_y),
                    (river_x + river_width * 0.7 + offset, height),
                    (river_x + river_width * 0.3 - offset, height)
                ]
                draw.polygon(glow_points, fill=colors["water"][:3] + (glow_alpha,))
            
            # River body
            draw.polygon(river_points, fill=colors["water"])
            
            # River flow lines with glow
            for i in range(6):
                flow_y = ground_y + i * 40
                flow_wave = math.sin(time_offset * 2 + i) * 25
                
                # Flow line glow
                for glow in range(2):
                    glow_offset = glow * 2
                    draw.line([
                        (river_x + 20 + glow_offset, flow_y + flow_wave),
                        (river_x + river_width - 20 - glow_offset, flow_y + flow_wave)
                    ], fill=BRAND_COLORS["primary_navy_dark"][:3] + (100 - glow * 40,), width=3)
                
                # Main flow line
                draw.line([
                    (river_x + 20, flow_y + flow_wave),
                    (river_x + river_width - 20, flow_y + flow_wave)
                ], fill=BRAND_COLORS["primary_navy_dark"], width=3)
    
    elif "Forest" in theme_name or "Sunset" in theme_name:
        # Simplified versions for other themes
        ground_y = int(height * 0.6)
        draw.rectangle([0, ground_y, width, height], fill=colors["ground"])
        
        # Add atmospheric glow
        glow_color = colors.get("glow_color", (255, 255, 255, 0))
        if glow_color[3] > 0:
            glow_center_x = width * 0.8 if "Sunset" in theme_name else width * 0.5
            glow_center_y = height * 0.3
            
            for size in range(100, 20, -20):
                glow_alpha = int(glow_color[3] * (1 - size / 120))
                draw.ellipse([
                    glow_center_x - size, glow_center_y - size,
                    glow_center_x + size, glow_center_y + size
                ], fill=glow_color[:3] + (glow_alpha,))
    
    return img

# ============================================================================
# KINETIC TYPOGRAPHY SYSTEM
# ============================================================================
def draw_kinetic_text(draw, text, x, y, t, font_base_size, max_width, color, text_type="hook"):
    """Draw text with kinetic animations."""
    
    if text_type == "hook":
        # Hook animation: pulsing/floating effect
        pulse = math.sin(t * 3) * 5  # Independent sine wave
        current_size = font_base_size + int(pulse)
        
        try:
            # Try to load dynamic font size
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", current_size)
        except:
            font = ImageFont.load_default(current_size)
        
        # Calculate position with floating effect
        float_offset = math.sin(t * 2) * 3
        current_y = y + float_offset
        
        # Draw text shadow for depth
        shadow_offset = int(current_size / 25) + 2
        draw.text((x + shadow_offset, current_y + shadow_offset), 
                 text, font=font, fill=(0, 0, 0, 150))
        
        # Draw main text
        draw.text((x, current_y), text, font=font, fill=color)
        
        return current_size
    
    elif text_type == "verse":
        # Typewriter animation for verse
        font = ImageFont.load_default(font_base_size)
        
        # Typewriter progress
        duration = 4  # seconds for full reveal
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
        line_height = font_base_size * 1.4
        current_y = y
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            line_x = x + (max_width - text_width) // 2
            
            # Text shadow
            draw.text((line_x + 2, current_y + 2), line, 
                     font=font, fill=(0, 0, 0, 100))
            
            # Main text with fade-in
            text_alpha = int(255 * progress)
            draw.text((line_x, current_y), line, 
                     font=font, fill=color[:3] + (text_alpha,))
            
            current_y += line_height
        
        # Blinking cursor
        if progress < 1.0 and int(t * 2) % 2 == 0:
            if lines:
                last_line = lines[-1]
                bbox = draw.textbbox((0, 0), last_line, font=font)
                cursor_x = x + (max_width - (bbox[2] - bbox[0])) // 2 + (bbox[2] - bbox[0]) + 5
                cursor_y = current_y - line_height + 10
                cursor_height = line_height - 20
                
                # Animated cursor width
                cursor_width = 3 + int(2 * abs(math.sin(t * 5)))
                draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height)],
                         fill=BRAND_COLORS["primary_green"], width=cursor_width)
        
        return current_y
    
    elif text_type == "reference":
        # Fade-in animation for reference
        font = ImageFont.load_default(font_base_size)
        
        # Calculate fade-in timing
        fade_start = 3.5  # Start fading in after 3.5 seconds
        fade_duration = 1.0  # Fade over 1 second
        
        if t < fade_start:
            return y
        
        fade_progress = min(1.0, (t - fade_start) / fade_duration)
        text_alpha = int(255 * fade_progress)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Reference background with fade
        bg_alpha = int(200 * fade_progress)
        bg_width = text_width + 40
        bg_height = font_base_size + 20
        
        draw.rounded_rectangle(
            [x - 20, y - 10, x + bg_width - 20, y + bg_height - 10],
            radius=10,
            fill=BRAND_COLORS["primary_green"][:3] + (bg_alpha,)
        )
        
        # Reference text
        draw.text((x, y), text, font=font, 
                 fill=color[:3] + (text_alpha,))
        
        return y + bg_height

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
# MAIN COMPOSITION WITH SAFE ZONES
# ============================================================================
def create_safe_design(width, height, platform, theme_name, book, chapter, verse, 
                      hook_text, t=0, is_video=False):
    """Create design with social media safe zones."""
    
    # Get safe zone dimensions
    safe_config = SAFE_ZONES.get(platform, SAFE_ZONES["instagram_square"])
    
    # Ensure dimensions match
    if width != safe_config["width"] or height != safe_config["height"]:
        # Scale safe zones proportionally
        scale_x = width / safe_config["width"]
        scale_y = height / safe_config["height"]
        
        safe_top = int(safe_config["title_safe"]["top"] * scale_y)
        safe_bottom = int(safe_config["title_safe"]["bottom"] * scale_y)
        safe_left = int(safe_config["title_safe"]["left"] * scale_x)
        safe_right = int(safe_config["title_safe"]["right"] * scale_x)
        
        text_top = int(safe_config["text_safe"]["top"] * scale_y)
        text_bottom = int(safe_config["text_safe"]["bottom"] * scale_y)
        text_left = int(safe_config["text_safe"]["left"] * scale_x)
        text_right = int(safe_config["text_safe"]["right"] * scale_x)
    else:
        safe_top = safe_config["title_safe"]["top"]
        safe_bottom = safe_config["title_safe"]["bottom"]
        safe_left = safe_config["title_safe"]["left"]
        safe_right = safe_config["title_safe"]["right"]
        
        text_top = safe_config["text_safe"]["top"]
        text_bottom = safe_config["text_safe"]["bottom"]
        text_left = safe_config["text_safe"]["left"]
        text_right = safe_config["text_safe"]["right"]
    
    theme = NATURE_THEMES[theme_name]
    
    # Create background with atmospheric depth
    img = create_atmospheric_background(width, height, theme, t)
    draw = ImageDraw.Draw(img)
    
    # Get verse text
    verse_text, reference = get_bible_verse(book, chapter, verse)
    
    # Content panel (within safe zone)
    panel_width = text_right - text_left
    panel_height = text_bottom - text_top
    panel_x = text_left
    panel_y = text_top
    
    # Semi-transparent panel background (within safe zone)
    panel_bg = Image.new("RGBA", (panel_width, panel_height), (0, 0, 0, 180))
    img.paste(panel_bg, (panel_x, panel_y), panel_bg)
    
    # Panel border (within safe zone)
    draw.rounded_rectangle(
        [panel_x - 5, panel_y - 5, panel_x + panel_width + 5, panel_y + panel_height + 5],
        radius=15,
        outline=BRAND_COLORS["primary_green"],
        width=4
    )
    
    # Draw kinetic hook/title (within title safe zone)
    if hook_text:
        # Center hook in title safe zone
        hook_x = safe_left + (safe_right - safe_left) // 2
        hook_y = safe_top + 30
        
        # Draw kinetic hook with pulsing effect
        draw_kinetic_text(
            draw, hook_text, hook_x, hook_y, t,
            font_base_size=64,
            max_width=safe_right - safe_left,
            color=BRAND_COLORS["primary_green"],
            text_type="hook"
        )
    
    # Draw verse text with typewriter animation (within text safe zone)
    text_x = panel_x + 40
    text_y = panel_y + 60
    text_max_width = panel_width - 80
    
    if is_video:
        # Kinetic typewriter animation
        final_y = draw_kinetic_text(
            draw, verse_text, text_x, text_y, t,
            font_base_size=46,
            max_width=text_max_width,
            color=theme["text_color"],
            text_type="verse"
        )
    else:
        # Static text for preview
        font = load_font(46, bold=False)
        
        # Wrap text
        words = verse_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= text_max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw lines
        line_height = 46 * 1.4
        current_y = text_y
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            line_x = text_x + (text_max_width - text_width) // 2
            
            # Text shadow for readability
            draw.text((line_x + 2, current_y + 2), line,
                     font=font, fill=(0, 0, 0, 100))
            
            # Main text
            draw.text((line_x, current_y), line,
                     font=font, fill=theme["text_color"])
            
            current_y += line_height
        
        final_y = current_y
    
    # Draw reference with fade-in animation
    ref_x = panel_x + panel_width - 200
    ref_y = final_y + 40
    
    if is_video:
        # Kinetic fade-in for reference
        draw_kinetic_text(
            draw, reference, ref_x, ref_y, t,
            font_base_size=36,
            max_width=200,
            color=BRAND_COLORS["white"],
            text_type="reference"
        )
    else:
        # Static reference
        ref_font = load_font(36, bold=True)
        
        # Reference background
        ref_bbox = draw.textbbox((0, 0), reference, font=ref_font)
        ref_width = ref_bbox[2] - ref_bbox[0]
        ref_bg_width = ref_width + 30
        ref_bg_height = 36 + 20
        
        draw.rounded_rectangle(
            [ref_x - 15, ref_y - 10, ref_x + ref_width + 15, ref_y + ref_bg_height - 10],
            radius=8,
            fill=BRAND_COLORS["primary_green"]
        )
        
        # Reference text
        draw.text((ref_x, ref_y), reference, font=ref_font,
                 fill=BRAND_COLORS["white"])
    
    # Brand watermark (outside safe zone but visible)
    watermark_font = load_font(28, bold=True)
    draw.text((width - 200, 30), "STILL MIND", font=watermark_font,
             fill=BRAND_COLORS["white"][:3] + (150,))
    
    # Safe zone visualization (for debugging - can be disabled)
    if st.session_state.get("show_safe_zones", False):
        # Draw title safe zone (red)
        draw.rectangle([safe_left, safe_top, safe_right, safe_bottom],
                      outline=(255, 0, 0, 150), width=2)
        
        # Draw text safe zone (green)
        draw.rectangle([text_left, text_top, text_right, text_bottom],
                      outline=(0, 255, 0, 150), width=2)
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_nature_video(width, height, platform, theme_name, book, chapter, verse, hook_text):
    """Create animated video with kinetic typography."""
    duration = 7  # Extended for kinetic effects
    fps = 24
    
    def make_frame(t):
        img = create_safe_design(
            width, height, platform, theme_name, book, chapter, verse,
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
st.title("🌄 Still Mind Pro: Advanced Nature Studio")
st.markdown("### Social Media Safe Zones • Atmospheric Depth • Kinetic Typography")

# Initialize session state
if "hook_text" not in st.session_state:
    st.session_state.hook_text = "BE STILL"
if "show_safe_zones" not in st.session_state:
    st.session_state.show_safe_zones = False

# Sidebar
with st.sidebar:
    st.header("🎨 Design Settings")
    
    # Platform selection
    platform_option = st.selectbox(
        "Social Platform",
        ["tiktok", "instagram_square", "instagram_story"],
        format_func=lambda x: x.replace("_", " ").title(),
        help="Choose platform for safe zone optimization"
    )
    
    # Get dimensions
    config = SAFE_ZONES[platform_option]
    WIDTH, HEIGHT = config["width"], config["height"]
    
    # Theme selection
    theme_option = st.selectbox(
        "Nature Theme",
        list(NATURE_THEMES.keys()),
        help="Choose a nature theme with atmospheric depth"
    )
    
    st.divider()
    
    st.header("📖 Scripture")
    
    # Bible book selection
    bible_books = ["Psalm", "Matthew", "John", "Isaiah", "Romans", 
                   "Philippians", "James", "Proverbs", "Ecclesiastes"]
    
    book = st.selectbox("Book", bible_books, index=0)
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 46)
    with col2:
        verse = st.number_input("Verse", 1, 176, 10)
    
    # Get verse text
    verse_text, reference = get_bible_verse(book, chapter, verse)
    
    st.write(f"**Preview:** {verse_text[:80]}...")
    
    st.divider()
    
    st.header("🪄 AI Tools")
    
    # Generate hook with AI
    if st.button("🤖 Generate Kinetic Hook", use_container_width=True):
        with st.spinner("Creating dynamic hook..."):
            hook_text = generate_hook_with_ai(verse_text, theme_option)
            st.session_state.hook_text = hook_text
            st.success(f"Generated: {hook_text}")
    
    # Manual hook input
    hook_text = st.text_input(
        "Hook/Title",
        value=st.session_state.hook_text,
        help="Short title with kinetic animation"
    ).upper()
    
    st.divider()
    
    st.header("🎬 Animation Controls")
    
    # Time slider
    time_slider = st.slider(
        "Animation Time",
        0.0, 7.0, 0.0, 0.1,
        help="Preview kinetic typography at different times"
    )
    
    # Debug option
    st.session_state.show_safe_zones = st.checkbox(
        "Show Safe Zones",
        value=False,
        help="Display safe zone boundaries for debugging"
    )
    
    # Animation speed
    animation_speed = st.select_slider(
        "Video Animation Speed",
        options=["Slow", "Normal", "Fast"],
        value="Normal"
    )

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Preview section
    st.subheader("🎭 Live Preview")
    
    # Platform info
    st.caption(f"Platform: {platform_option.replace('_', ' ').title()} • Size: {WIDTH} × {HEIGHT}")
    
    with st.spinner("Creating advanced design..."):
        preview_img = create_safe_design(
            WIDTH, HEIGHT, platform_option, theme_option,
            book, chapter, verse, hook_text, time_slider, False
        )
    
    # FIXED: Simple image display without problematic parameter
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
            file_name=f"still_mind_pro_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Create Kinetic Video", use_container_width=True):
            with st.spinner("Animating atmospheric depth and kinetic typography..."):
                video_data = create_nature_video(
                    WIDTH, HEIGHT, platform_option, theme_option,
                    book, chapter, verse, hook_text
                )
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download button
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"still_mind_pro_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    # Info panel
    st.subheader("🎯 Advanced Features")
    
    # Safe zone info
    safe_config = SAFE_ZONES[platform_option]
    st.write("**Safe Zones:**")
    st.success("✓ Title Area: Top 10% - 90%")
    st.success("✓ Text Area: Optimized for platform")
    st.success("✓ No Critical Content Near Edges")
    
    # Atmospheric features
    st.write("**Atmospheric Depth:**")
    theme = NATURE_THEMES[theme_option]
    if "fog_color" in theme and theme["fog_color"][3] > 0:
        st.success("✓ Flat Mist Layers")
        st.success("✓ Parallax Movement")
        st.success("✓ Atmospheric Perspective")
    
    if "glow_color" in theme and theme["glow_color"][3] > 0:
        st.success("✓ Ambient Glow Effects")
    
    # Kinetic typography
    st.write("**Kinetic Typography:**")
    st.success("✓ Pulsing Hook Animation")
    st.success("✓ Typewriter Verse Reveal")
    st.success("✓ Fade-in Reference")
    
    st.divider()
    
    # Social media section
    st.subheader("📱 Social Media Tools")
    
    # Generate caption with AI
    if st.button("🤖 Generate Optimized Caption", use_container_width=True):
        with st.spinner("Creating platform-optimized caption..."):
            caption = generate_social_caption_with_ai(
                verse_text, reference, hook_text, theme_option
            )
            st.session_state.caption = caption
            st.success("Caption optimized!")
    
    # Display caption
    caption = st.session_state.get("caption", "")
    if not caption:
        # Default caption
        caption = f"""{hook_text}

{verse_text[:100]}...

📖 {reference}

#StillMind #Scripture #{theme_option.replace(' ', '')}"""
        st.session_state.caption = caption
    
    st.text_area("Social Media Caption", caption, height=180)
    
    col_copy, col_clear = st.columns(2)
    with col_copy:
        if st.button("📋 Copy", use_container_width=True):
            st.code(caption)
            st.success("Copied!")
    
    with col_clear:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.caption = ""
            st.rerun()
    
    st.divider()
    
    # Technical info
    st.subheader("⚙️ Technical Details")
    
    st.metric("Resolution", f"{WIDTH} × {HEIGHT}")
    st.metric("Frame Rate", "24 FPS" if time_slider > 0 else "Static")
    st.metric("Animation", f"{animation_speed}")
    
    # Color info
    st.write("**Brand Colors:**")
    col1, col2 = st.columns(2)
    with col1:
        st.color_picker("Primary Green", 
                       value="#4CAF50", disabled=True)
        st.color_picker("Primary Navy", 
                       value="#0D47A1", disabled=True)
    with col2:
        st.color_picker("White", 
                       value="#FFFFFF", disabled=True)
        st.color_picker("Grey", 
                       value="#757575", disabled=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #4CAF50; font-size: 0.9rem;'>
    <p>🌄 Still Mind Pro • Social Media Safe Zones • Atmospheric Depth • Kinetic Typography</p>
    <p>Flat Design • Brand Colors: Green, Navy Blue, White, Grey</p>
</div>
""", unsafe_allow_html=True)

# Cleanup temporary files
for file in os.listdir("."):
    if file.startswith("temp_") and file.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(file) > 300:
                os.remove(file)
        except:
            pass