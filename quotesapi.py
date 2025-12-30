import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io, os, math, time, random, json, requests
import numpy as np
from datetime import datetime
import base64
from typing import Tuple, List, Dict, Optional
import imageio.v3 as iio
from groq import Groq

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Still Mind | Animated Quotes",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Brand Configuration
BRAND_NAME = "@stillmind"
BRAND_COLORS = {
    "primary": (76, 175, 80, 255),       # #4CAF50 - Green
    "primary_dark": (56, 142, 60, 255),   # #388E3C
    "primary_light": (129, 199, 132, 255), # #81C784
    "navy": (13, 27, 42, 255),           # #0d1b2a
    "navy_dark": (5, 15, 25, 255),       # #050f19
    "navy_light": (32, 49, 68, 255),     # #203144
    "white": (255, 255, 255, 255),
    "grey_light": (238, 238, 238, 255),   # #EEEEEE
    "grey_medium": (158, 158, 158, 255),  # #9E9E9E
    "accent": (25, 118, 210, 255),       # #1976D2 - Blue
}

SIZES = {
    "Instagram Square (1080x1080)": (1080, 1080),
    "Instagram Story (1080x1920)": (1080, 1920),
    "Twitter Post (1200x675)": (1200, 675),
    "YouTube Shorts (1080x1920)": (1080, 1920),
}

ANIMATION_SETTINGS = {
    "duration": 8,
    "fps": 15,
    "total_frames": 120  # 8 * 15
}

# ============================================================================
# QUOTE API MANAGER
# ============================================================================
class QuoteAPIManager:
    """Fetch and manage quotes from API"""
    
    QUOTABLE_API = "https://api.quotable.io"
    LOCAL_QUOTES = {
        "motivation": [
            "TRUST YOURSELF",
            "TAKE CARE TO WORK HARD",
            "DON'T GIVE UP",
            "The only way to do great work is to love what you do",
            "Believe you can and you're halfway there"
        ],
        "wisdom": [
            "The mind is everything. What you think you become",
            "Knowing yourself is the beginning of all wisdom",
            "The only true wisdom is in knowing you know nothing",
            "Wisdom is not a product of schooling but of the lifelong attempt to acquire it"
        ],
        "mindfulness": [
            "Be present in all things and thankful for all things",
            "The present moment is the only moment available to us",
            "Mindfulness is the aware, balanced acceptance of the present experience",
            "Feelings come and go like clouds in a windy sky"
        ],
        "success": [
            "Success is not final, failure is not fatal: it is the courage to continue that counts",
            "The way to get started is to quit talking and begin doing",
            "Don't be afraid to give up the good to go for the great",
            "Success usually comes to those who are too busy to be looking for it"
        ]
    }
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_quote_from_api(category="motivation"):
        """Fetch quote from Quotable API with fallback"""
        try:
            # Try to fetch from Quotable API
            if category == "random":
                response = requests.get(f"{QuoteAPIManager.QUOTABLE_API}/random", timeout=5)
            else:
                response = requests.get(
                    f"{QuoteAPIManager.QUOTABLE_API}/quotes/random",
                    params={"tags": category, "maxLength": 120},
                    timeout=5
                )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "text": data["content"],
                    "author": data["author"],
                    "category": category,
                    "source": "Quotable API"
                }
        except:
            pass
        
        # Fallback to local quotes
        if category in QuoteAPIManager.LOCAL_QUOTES:
            quotes = QuoteAPIManager.LOCAL_QUOTES[category]
        else:
            quotes = QuoteAPIManager.LOCAL_QUOTES["motivation"]
        
        return {
            "text": random.choice(quotes),
            "author": "Still Mind",
            "category": category,
            "source": "Local Database"
        }
    
    @staticmethod
    def get_all_categories():
        """Get all available quote categories"""
        return list(QuoteAPIManager.LOCAL_QUOTES.keys()) + ["random"]

# ============================================================================
# ANIMATED BACKGROUND GENERATORS
# ============================================================================
class AnimatedBackground:
    """Generate animated backgrounds with different styles"""
    
    @staticmethod
    def create_wave_gradient(width: int, height: int, time_offset: float) -> Image.Image:
        """Wave gradient animation"""
        img = Image.new("RGBA", (width, height))
        pixels = img.load()
        
        for y in range(height):
            # Wave effect
            wave = math.sin(y * 0.01 + time_offset * 2) * 30
            wave += math.cos(y * 0.005 + time_offset) * 15
            
            for x in range(width):
                # Distance from center with wave
                dx = (x - width/2) / width
                dy = (y - height/2 + wave) / height
                dist = math.sqrt(dx*dx + dy*dy) * 2
                
                # Color gradient with wave
                r = int(BRAND_COLORS["navy"][0] * (1 - dist) + BRAND_COLORS["navy_dark"][0] * dist)
                g = int(BRAND_COLORS["navy"][1] * (1 - dist) + BRAND_COLORS["navy_dark"][1] * dist)
                b = int(BRAND_COLORS["navy"][2] * (1 - dist) + BRAND_COLORS["navy_dark"][2] * dist)
                
                # Add subtle green tint in center
                if dist < 0.5:
                    green_factor = (0.5 - dist) * 0.3
                    g = min(255, g + int(100 * green_factor))
                
                pixels[x, y] = (r, g, b, 255)
        
        return img
    
    @staticmethod
    def create_particle_field(width: int, height: int, time_offset: float) -> Image.Image:
        """Floating particle animation"""
        img = Image.new("RGBA", (width, height), BRAND_COLORS["navy"])
        draw = ImageDraw.Draw(img)
        
        # Generate particles
        particle_count = 150
        for i in range(particle_count):
            # Animated position
            x = (i * 37 + time_offset * 100) % width
            y = (i * 23 + time_offset * 80) % height
            
            # Size and opacity animation
            size = 1 + math.sin(time_offset * 3 + i) * 2
            opacity = int(50 + 100 * abs(math.sin(time_offset * 2 + i)))
            
            # Draw particle
            color = BRAND_COLORS["grey_light"][:3] + (opacity,)
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color)
        
        # Add center glow
        center_radius = min(width, height) // 4
        for r in range(center_radius, 0, -20):
            opacity = int(30 * (r / center_radius))
            draw.ellipse(
                [width//2 - r, height//2 - r, width//2 + r, height//2 + r],
                outline=BRAND_COLORS["primary"][:3] + (opacity,),
                width=2
            )
        
        return img
    
    @staticmethod
    def create_geometric_lines(width: int, height: int, time_offset: float) -> Image.Image:
        """Geometric line animation"""
        img = Image.new("RGBA", (width, height), BRAND_COLORS["navy_dark"])
        draw = ImageDraw.Draw(img)
        
        # Animated lines from center
        line_count = 24
        center_x, center_y = width // 2, height // 2
        
        for i in range(line_count):
            angle = (i / line_count) * (2 * math.pi) + time_offset
            length = min(width, height) // 2
            
            # Calculate end point
            end_x = center_x + math.cos(angle) * length
            end_y = center_y + math.sin(angle) * length
            
            # Animated color
            hue = (i / line_count + time_offset) % 1.0
            if hue < 0.33:
                color = BRAND_COLORS["primary"]
            elif hue < 0.66:
                color = BRAND_COLORS["accent"]
            else:
                color = BRAND_COLORS["grey_light"]
            
            # Draw line
            draw.line([(center_x, center_y), (end_x, end_y)], 
                     fill=color[:3] + (150,), width=2)
        
        return img
    
    @staticmethod
    def create_gradient_shift(width: int, height: int, time_offset: float) -> Image.Image:
        """Shifting gradient animation"""
        img = Image.new("RGBA", (width, height))
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                # Animated gradients
                x_norm = x / width
                y_norm = y / height
                
                # Time-based shifting
                shift = time_offset * 0.5
                
                # Calculate colors with shifting
                r = int(
                    BRAND_COLORS["navy"][0] * (1 - x_norm) + 
                    BRAND_COLORS["primary"][0] * x_norm * math.sin(shift)
                )
                g = int(
                    BRAND_COLORS["navy"][1] * (1 - y_norm) + 
                    BRAND_COLORS["primary"][1] * y_norm * math.cos(shift)
                )
                b = int(
                    BRAND_COLORS["navy_dark"][2] * (1 - (x_norm + y_norm)/2) + 
                    100 * math.sin(x_norm * 10 + shift)
                )
                
                pixels[x, y] = (r, g, b, 255)
        
        return img

# ============================================================================
# TEXT ANIMATION GENERATORS
# ============================================================================
class TextAnimation:
    """Generate text animations with different effects"""
    
    @staticmethod
    def typewriter_effect(text: str, progress: float, font: ImageFont.FreeTypeFont, 
                         max_width: int) -> Tuple[List[str], float]:
        """Typewriter animation effect"""
        # Calculate how many characters to show
        total_chars = len(text)
        visible_chars = int(total_chars * progress)
        
        # Wrap text with visible characters
        visible_text = text[:visible_chars]
        words = visible_text.split()
        
        lines = []
        current_line = []
        current_line_text = ""
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
                current_line_text = test_line
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_line_text = word
        
        if current_line:
            lines.append(current_line_text)
        
        return lines, progress
    
    @staticmethod
    def fade_in_effect(text: str, progress: float, font: ImageFont.FreeTypeFont,
                      max_width: int) -> Tuple[List[str], float]:
        """Fade in animation effect"""
        # Always show full text
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Opacity based on progress
        opacity = min(1.0, progress * 2)
        return lines, opacity
    
    @staticmethod
    def slide_up_effect(text: str, progress: float, font: ImageFont.FreeTypeFont,
                       max_width: int) -> Tuple[List[str], float]:
        """Slide up animation effect"""
        # Wrap text
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Vertical offset based on progress
        offset = (1 - progress) * 100
        return lines, offset
    
    @staticmethod
    def word_by_word_effect(text: str, progress: float, font: ImageFont.FreeTypeFont,
                           max_width: int) -> Tuple[List[str], float]:
        """Word by word reveal animation"""
        words = text.split()
        total_words = len(words)
        visible_words = int(total_words * progress)
        
        visible_text = ' '.join(words[:visible_words])
        
        # Wrap visible text
        visible_words_list = visible_text.split()
        lines = []
        current_line = []
        
        for word in visible_words_list:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines, progress

# ============================================================================
# MAIN QUOTE GENERATOR
# ============================================================================
class QuoteGenerator:
    """Generate animated quote videos with text hierarchy"""
    
    def __init__(self):
        self.bg_generator = AnimatedBackground()
        self.text_animator = TextAnimation()
        
    def create_frame(self, 
                    quote_text: str,
                    author: str,
                    size: Tuple[int, int],
                    bg_style: str,
                    text_animation: str,
                    frame_progress: float,
                    time_offset: float) -> Image.Image:
        """Create a single frame with animated elements"""
        width, height = size
        
        # Generate background
        if bg_style == "particle":
            bg = self.bg_generator.create_particle_field(width, height, time_offset)
        elif bg_style == "geometric":
            bg = self.bg_generator.create_geometric_lines(width, height, time_offset)
        elif bg_style == "gradient":
            bg = self.bg_generator.create_gradient_shift(width, height, time_offset)
        else:  # wave
            bg = self.bg_generator.create_wave_gradient(width, height, time_offset)
        
        # Prepare for drawing
        img = bg.copy()
        draw = ImageDraw.Draw(img)
        
        # Load fonts (hierarchy)
        try:
            # Main quote font (largest)
            quote_font = ImageFont.truetype("arialbd.ttf", 72)
            # Author font (medium)
            author_font = ImageFont.truetype("ariali.ttf", 42)
            # Brand font (smallest)
            brand_font = ImageFont.truetype("arial.ttf", 32)
        except:
            # Fallback
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            brand_font = ImageFont.load_default()
        
        # TEXT HIERARCHY:
        # 1. Main quote (center)
        # 2. Author (bottom right)
        # 3. Brand (bottom left)
        
        max_quote_width = width - 200
        
        # Apply text animation
        if text_animation == "typewriter":
            lines, text_progress = self.text_animator.typewriter_effect(
                quote_text, frame_progress, quote_font, max_quote_width
            )
            text_opacity = 255
            text_offset = 0
        elif text_animation == "fade":
            lines, text_opacity_factor = self.text_animator.fade_in_effect(
                quote_text, frame_progress, quote_font, max_quote_width
            )
            text_opacity = int(255 * text_opacity_factor)
            text_offset = 0
        elif text_animation == "slide":
            lines, text_offset = self.text_animator.slide_up_effect(
                quote_text, frame_progress, quote_font, max_quote_width
            )
            text_opacity = 255
        elif text_animation == "word":
            lines, text_progress = self.text_animator.word_by_word_effect(
                quote_text, frame_progress, quote_font, max_quote_width
            )
            text_opacity = 255
            text_offset = 0
        else:  # none
            lines, _ = self.text_animator.fade_in_effect(
                quote_text, 1.0, quote_font, max_quote_width
            )
            text_opacity = 255
            text_offset = 0
        
        # Calculate total text height
        line_height = 90
        total_text_height = len(lines) * line_height
        
        # Center quote vertically with optional offset
        start_y = (height - total_text_height) // 2 + text_offset
        
        # Draw quote lines with hierarchy
        for i, line in enumerate(lines):
            bbox = quote_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + i * line_height
            
            # Text shadow for depth
            shadow_color = BRAND_COLORS["navy_dark"][:3] + (text_opacity // 2,)
            draw.text((x + 3, y + 3), line, font=quote_font, fill=shadow_color)
            
            # Main text with animation opacity
            text_color = BRAND_COLORS["white"][:3] + (text_opacity,)
            draw.text((x, y), line, font=quote_font, fill=text_color)
        
        # Draw author (bottom right) - appears after quote is mostly shown
        if frame_progress > 0.7:
            author_opacity = int(255 * ((frame_progress - 0.7) / 0.3))
            author_text = f"— {author}"
            author_bbox = author_font.getbbox(author_text)
            author_width = author_bbox[2] - author_bbox[0]
            
            # Position: bottom right, with padding
            author_x = width - author_width - 60
            author_y = height - 120
            
            # Author with subtle background
            if author_opacity > 100:
                bg_padding = 15
                draw.rectangle(
                    [author_x - bg_padding, author_y - bg_padding,
                     author_x + author_width + bg_padding, 
                     author_y + (author_bbox[3] - author_bbox[1]) + bg_padding],
                    fill=BRAND_COLORS["primary"][:3] + (author_opacity // 3,)
                )
            
            draw.text(
                (author_x, author_y), author_text,
                font=author_font,
                fill=BRAND_COLORS["white"][:3] + (author_opacity,)
            )
        
        # Draw brand (bottom left) - always visible
        brand_text = BRAND_NAME
        draw.text(
            (60, height - 80), brand_text,
            font=brand_font,
            fill=BRAND_COLORS["grey_medium"][:3] + (200,)
        )
        
        return img
    
    def create_animated_video(self,
                             quote_text: str,
                             author: str,
                             size: Tuple[int, int],
                             bg_style: str,
                             text_animation: str) -> bytes:
        """Create MP4 video from animated frames"""
        width, height = size
        total_frames = ANIMATION_SETTINGS["total_frames"]
        fps = ANIMATION_SETTINGS["fps"]
        
        # Generate all frames
        frames = []
        for frame_num in range(total_frames):
            time_offset = frame_num / fps
            frame_progress = min(1.0, frame_num / total_frames)
            
            frame = self.create_frame(
                quote_text, author, size, bg_style, 
                text_animation, frame_progress, time_offset
            )
            
            # Convert to numpy array for video encoding
            frame_np = np.array(frame.convert("RGB"))
            frames.append(frame_np)
        
        # Encode to MP4
        buffer = io.BytesIO()
        iio.imwrite(
            buffer,
            frames,
            format='mp4',
            fps=fps,
            codec='libx264',
            quality=8,
            pixelformat='yuv420p'
        )
        
        return buffer.getvalue()

# ============================================================================
# GROQ SOCIAL MEDIA MANAGER
# ============================================================================
class SocialMediaManager:
    """Generate social media content using Groq AI"""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
    
    def generate_post_content(self, quote: str, author: str, platform: str) -> Dict:
        """Generate platform-specific social media content"""
        try:
            prompt = f"""
            Create a social media post for the quote platform.
            
            QUOTE: "{quote}"
            AUTHOR: {author}
            PLATFORM: {platform}
            BRAND: @stillmind (mindfulness, wisdom, personal growth)
            
            Generate a JSON with:
            1. caption: Engaging caption (2-3 lines with relevant emojis)
            2. hashtags: 5-8 relevant hashtags
            3. best_time: Best time to post (consider global audience)
            4. engagement_tip: One tip to increase engagement
            5. visual_tip: Tip for accompanying visual
            
            Make it authentic, inspiring, and platform-appropriate.
            """
            
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a social media expert specializing in mindfulness and personal growth content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = json.loads(response.choices[0].message.content)
            content["platform"] = platform
            content["generated_at"] = datetime.now().isoformat()
            
            return content
            
        except Exception as e:
            # Fallback content
            return self._generate_fallback_content(quote, author, platform)
    
    def _generate_fallback_content(self, quote: str, author: str, platform: str) -> Dict:
        """Generate fallback social media content"""
        base_caption = f'"{quote}"\n\n— {author}\n\n💭 What does this mean to you?'
        
        if platform == "instagram":
            caption = f"{base_caption}\n\n✨ Follow @stillmind for daily wisdom\n👇 Double tap if this resonates!"
            hashtags = ["#stillmind", "#wisdom", "#quote", "#mindfulness", "#growth"]
        elif platform == "twitter":
            caption = f'{base_caption}\n\n✨ @stillmind'
            hashtags = ["#Quote", "#Wisdom", "#Mindfulness"]
        elif platform == "tiktok":
            caption = f"{base_caption}\n\n📌 Save for later!\n🔔 Follow for more wisdom!"
            hashtags = ["#stillmind", "#wisdom", "#fyp", "#foryou"]
        else:
            caption = base_caption
            hashtags = ["#stillmind", "#quote", "#wisdom"]
        
        return {
            "caption": caption,
            "hashtags": hashtags,
            "best_time": "7-9 PM GMT",
            "engagement_tip": "Ask a question in comments to encourage discussion",
            "visual_tip": "Use clean, minimalist design with good contrast",
            "platform": platform,
            "is_fallback": True
        }

# ============================================================================
# STREAMLIT APP
# ============================================================================
def main():
    # Custom CSS for minimal modern design
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0d1b2a 0%, #050f19 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        border-left: 5px solid #4CAF50;
    }
    .stButton > button {
        background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
    }
    .quote-preview {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 0 auto;
    }
    .section-header {
        color: #4CAF50;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_quote' not in st.session_state:
        st.session_state.current_quote = None
    if 'current_video' not in st.session_state:
        st.session_state.current_video = None
    if 'social_content' not in st.session_state:
        st.session_state.social_content = {}
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="color: #4CAF50; margin-bottom: 0.5rem;">🧠 {BRAND_NAME}</h1>
        <p style="color: #EEEEEE; opacity: 0.9; margin-bottom: 0;">Animated Quote Generator</p>
        <p style="color: #9E9E9E; font-size: 0.9rem; margin: 0;">Create stunning animated quotes with text hierarchy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="section-header">⚙️ SETTINGS</div>', unsafe_allow_html=True)
        
        # Quote Source
        quote_source = st.selectbox(
            "Quote Source",
            ["API (Quotable.io)", "Custom"],
            index=0
        )
        
        if quote_source == "API (Quotable.io)":
            category = st.selectbox(
                "Category",
                QuoteAPIManager.get_all_categories(),
                index=0
            )
        else:
            custom_quote = st.text_area(
                "Your Quote",
                placeholder="Enter your custom quote here...",
                height=100
            )
            custom_author = st.text_input("Author", value="Still Mind")
        
        # Design Settings
        size_option = st.selectbox("Size Format", list(SIZES.keys()), index=0)
        
        bg_style = st.selectbox(
            "Background Animation",
            ["wave", "particle", "geometric", "gradient"],
            format_func=lambda x: x.title(),
            index=0
        )
        
        text_animation = st.selectbox(
            "Text Animation",
            ["typewriter", "fade", "slide", "word", "none"],
            format_func=lambda x: x.title() + " Effect",
            index=0
        )
        
        # Generate Button
        if st.button("✨ GENERATE ANIMATED QUOTE", type="primary"):
            with st.spinner("Creating your animated quote..."):
                # Get quote
                if quote_source == "API (Quotable.io)":
                    quote_data = QuoteAPIManager.fetch_quote_from_api(category)
                    quote_text = quote_data["text"]
                    author = quote_data["author"]
                else:
                    quote_text = custom_quote.strip()
                    author = custom_author.strip() or "Still Mind"
                
                if not quote_text:
                    st.error("Please enter a quote")
                    return
                
                # Generate video
                generator = QuoteGenerator()
                video_data = generator.create_animated_video(
                    quote_text,
                    author,
                    SIZES[size_option],
                    bg_style,
                    text_animation
                )
                
                # Store in session state
                st.session_state.current_quote = {
                    "text": quote_text,
                    "author": author,
                    "size": size_option,
                    "bg_style": bg_style,
                    "text_animation": text_animation
                }
                st.session_state.current_video = video_data
                
                st.success("✅ Video generated successfully!")
    
    with col2:
        # Preview Section
        if st.session_state.current_video:
            st.markdown('<div class="section-header">🎬 PREVIEW</div>', unsafe_allow_html=True)
            
            # Video preview
            st.markdown('<div class="quote-preview">', unsafe_allow_html=True)
            st.video(st.session_state.current_video, format="video/mp4", start_time=0)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download buttons
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 DOWNLOAD MP4",
                    data=st.session_state.current_video,
                    file_name=f"stillmind_quote_{timestamp}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            
            with col_dl2:
                # Export as JPEG (single frame)
                if st.button("🖼️ EXPORT AS JPEG", use_container_width=True):
                    generator = QuoteGenerator()
                    frame = generator.create_frame(
                        st.session_state.current_quote["text"],
                        st.session_state.current_quote["author"],
                        SIZES[st.session_state.current_quote["size"]],
                        st.session_state.current_quote["bg_style"],
                        "none",  # No animation for JPEG
                        1.0,  # Full progress
                        0  # No time offset
                    )
                    
                    jpeg_buffer = io.BytesIO()
                    frame.save(jpeg_buffer, format='JPEG', quality=95, optimize=True)
                    
                    st.download_button(
                        label="📥 DOWNLOAD JPEG",
                        data=jpeg_buffer.getvalue(),
                        file_name=f"stillmind_quote_{timestamp}.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
            
            # Social Media Section
            st.markdown("---")
            st.markdown('<div class="section-header">📱 SOCIAL MEDIA</div>', unsafe_allow_html=True)
            
            # Check for Groq API key
            try:
                groq_key = st.secrets["groq_key"]
                sm_manager = SocialMediaManager(groq_key)
                
                platform = st.selectbox(
                    "Platform",
                    ["instagram", "twitter", "tiktok", "linkedin", "facebook"],
                    index=0
                )
                
                if st.button("🤖 GENERATE SOCIAL POST", use_container_width=True):
                    with st.spinner("Generating AI-powered content..."):
                        social_content = sm_manager.generate_post_content(
                            st.session_state.current_quote["text"],
                            st.session_state.current_quote["author"],
                            platform
                        )
                        
                        st.session_state.social_content = social_content
                
                if st.session_state.social_content:
                    content = st.session_state.social_content
                    
                    # Display generated content
                    st.text_area("📝 Caption", content["caption"], height=150)
                    
                    st.write("**🏷️ Hashtags:**")
                    st.code(' '.join(f"#{tag}" for tag in content.get("hashtags", [])))
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"**⏰ Best Time:** {content.get('best_time', 'N/A')}")
                    with col_info2:
                        st.write(f"**💡 Tip:** {content.get('engagement_tip', 'N/A')}")
                    
                    st.write(f"**🎨 Visual Tip:** {content.get('visual_tip', 'N/A')}")
            
            except (KeyError, Exception) as e:
                st.info("🔑 Add `groq_key` to Streamlit secrets for AI-powered social media content")
                
                # Show basic social media info
                st.write("**Basic Social Media Info:**")
                st.write("• **Caption Idea:** Add quote with relevant emojis")
                st.write("• **Hashtags:** #stillmind #wisdom #quote #mindfulness")
                st.write("• **Best Time:** 7-9 PM (Global)")
            
            # Quick Actions
            st.markdown("---")
            st.markdown('<div class="section-header">🔄 QUICK ACTIONS</div>', unsafe_allow_html=True)
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("🔄 NEW QUOTE", use_container_width=True):
                    st.session_state.current_quote = None
                    st.session_state.current_video = None
                    st.rerun()
            
            with col_act2:
                if st.button("🎲 RANDOM STYLE", use_container_width=True):
                    st.rerun()
        
        else:
            # Empty state
            st.markdown("""
            <div style="text-align: center; padding: 4rem; color: #9E9E9E;">
                <h3>👆 Configure & Generate</h3>
                <p>Select your preferences and click GENERATE to create your first animated quote.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #616161; padding: 2rem 0; font-size: 0.9rem;">
        <p>🧠 {BRAND_NAME} • Animated Quote Generator • Modern Design with Text Hierarchy</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">MP4 Video • Background Animations • Text Effects • Social Media Integration</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == "__main__":
    # Check for required dependencies
    try:
        import imageio.v3 as iio
        main()
    except ImportError as e:
        st.error(f"Missing dependency: {e}")
        st.info("Please add to requirements.txt: imageio[ffmpeg]>=2.31.0")