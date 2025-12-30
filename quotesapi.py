import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, math, time, random, json
import numpy as np
from datetime import datetime
from typing import Tuple, List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Still Mind | Modern Quote Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"  # Minimal UI
)

# Brand Configuration
BRAND_NAME = "@stillmind"
BRAND_COLORS = {
    "primary_green": (76, 175, 80, 255),     # #4CAF50
    "dark_green": (56, 142, 60, 255),        # #388E3C
    "navy_blue": (13, 27, 42, 255),          # #0d1b2a
    "dark_navy": (5, 15, 25, 255),           # #050f19
    "white": (255, 255, 255, 255),
    "light_grey": (224, 224, 224, 255),      # #E0E0E0
    "medium_grey": (158, 158, 158, 255),     # #9E9E9E
    "accent_blue": (25, 118, 210, 255),      # #1976D2
}

SIZES = {
    "Instagram Square (1080x1080)": (1080, 1080),
    "Instagram Story (1080x1920)": (1080, 1920),
    "Twitter Header (1500x500)": (1500, 500),
    "Desktop Wallpaper (1920x1080)": (1920, 1080),
}

ANIMATION_SETTINGS = {
    "duration": 8,      # seconds
    "fps": 15,          # frames per second
    "total_frames": 120 # 8 * 15
}

# ============================================================================
# ANIMATED BACKGROUND GENERATORS
# ============================================================================
class AnimatedBackground:
    """Generate modern animated backgrounds"""
    
    @staticmethod
    def create_wave_gradient(width: int, height: int, time_offset: float) -> Image.Image:
        """Create wave-like gradient animation"""
        img = Image.new("RGBA", (width, height))
        
        for y in range(height):
            # Calculate wave offset
            wave = math.sin(y * 0.01 + time_offset) * 20
            
            # Interpolate between navy and dark navy with wave effect
            ratio = (y + wave) / height
            ratio = max(0, min(1, ratio))
            
            # Dark to light gradient (bottom to top)
            r = int(BRAND_COLORS["navy_blue"][0] * (1 - ratio) + BRAND_COLORS["dark_navy"][0] * ratio)
            g = int(BRAND_COLORS["navy_blue"][1] * (1 - ratio) + BRAND_COLORS["dark_navy"][1] * ratio)
            b = int(BRAND_COLORS["navy_blue"][2] * (1 - ratio) + BRAND_COLORS["dark_navy"][2] * ratio)
            
            for x in range(width):
                # Add subtle horizontal variation
                x_ratio = math.sin(x * 0.005 + time_offset * 0.5) * 0.1
                final_ratio = max(0, min(1, ratio + x_ratio))
                
                pixel_r = int(r * (1 - final_ratio) + BRAND_COLORS["navy_blue"][0] * final_ratio)
                pixel_g = int(g * (1 - final_ratio) + BRAND_COLORS["navy_blue"][1] * final_ratio)
                pixel_b = int(b * (1 - final_ratio) + BRAND_COLORS["navy_blue"][2] * final_ratio)
                
                img.putpixel((x, y), (pixel_r, pixel_g, pixel_b, 255))
        
        return img
    
    @staticmethod
    def create_particle_field(width: int, height: int, time_offset: float) -> Image.Image:
        """Create floating particle animation"""
        img = Image.new("RGBA", (width, height), BRAND_COLORS["navy_blue"])
        draw = ImageDraw.Draw(img)
        
        # Create particles
        num_particles = 100
        for i in range(num_particles):
            # Particle position with time-based movement
            x = (i * 37) % width + math.sin(time_offset * 2 + i) * 50
            y = (i * 19) % height + math.cos(time_offset * 1.5 + i) * 30
            
            # Particle size and opacity
            size = 1 + math.sin(time_offset * 3 + i) * 0.5
            opacity = int(100 + 155 * abs(math.sin(time_offset + i)))
            
            # Draw particle
            draw.ellipse([x-size, y-size, x+size, y+size],
                        fill=BRAND_COLORS["light_grey"][:3] + (opacity,))
        
        # Add subtle vignette
        for y in range(height):
            for x in range(width):
                # Distance from center
                dx = (x - width/2) / width
                dy = (y - height/2) / height
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Vignette effect
                vignette = max(0, 1 - dist * 1.5)
                r, g, b, a = img.getpixel((x, y))
                r = int(r * vignette)
                g = int(g * vignette)
                b = int(b * vignette)
                
                img.putpixel((x, y), (r, g, b, a))
        
        return img
    
    @staticmethod
    def create_geometric_lines(width: int, height: int, time_offset: float) -> Image.Image:
        """Create animated geometric lines background"""
        img = Image.new("RGBA", (width, height), BRAND_COLORS["dark_navy"])
        draw = ImageDraw.Draw(img)
        
        # Draw animated lines
        num_lines = 20
        for i in range(num_lines):
            # Line position with animation
            offset = time_offset * 50
            x1 = (i * width / num_lines + offset) % width
            y1 = 0
            x2 = x1 + height * math.tan(math.radians(30))
            y2 = height
            
            # Wrap around
            if x2 > width:
                x2 -= width
            
            # Line color and opacity
            opacity = int(50 + 50 * math.sin(time_offset + i))
            color = BRAND_COLORS["medium_grey"][:3] + (opacity,)
            
            # Draw line
            draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
        
        # Add center glow
        center_size = min(width, height) // 3
        for size in range(center_size, 0, -10):
            opacity = int(30 * (size / center_size))
            draw.ellipse([width//2 - size, height//2 - size,
                         width//2 + size, height//2 + size],
                        outline=BRAND_COLORS["primary_green"][:3] + (opacity,),
                        width=1)
        
        return img

# ============================================================================
# QUOTE MANAGER
# ============================================================================
class QuoteManager:
    """Manage quotes and categories"""
    
    QUOTES = {
        "motivation": [
            {"text": "TRUST YOURSELF", "author": "Still Mind"},
            {"text": "TAKE CARE TO WORK HARD", "author": "Still Mind"},
            {"text": "DON'T GIVE UP", "author": "Still Mind"},
            {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
            {"text": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
        ],
        "wisdom": [
            {"text": "The mind is everything. What you think you become.", "author": "Buddha"},
            {"text": "Knowing yourself is the beginning of all wisdom.", "author": "Aristotle"},
            {"text": "The only true wisdom is in knowing you know nothing.", "author": "Socrates"},
            {"text": "Wisdom is not a product of schooling but of the lifelong attempt to acquire it.", "author": "Albert Einstein"},
        ],
        "success": [
            {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"},
            {"text": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney"},
            {"text": "Don't be afraid to give up the good to go for the great.", "author": "John D. Rockefeller"},
            {"text": "Success usually comes to those who are too busy to be looking for it.", "author": "Henry David Thoreau"},
        ],
        "mindfulness": [
            {"text": "Be present in all things and thankful for all things.", "author": "Maya Angelou"},
            {"text": "The present moment is the only moment available to us.", "author": "Thich Nhat Hanh"},
            {"text": "Mindfulness is the aware, balanced acceptance of the present experience.", "author": "Sylvia Boorstein"},
            {"text": "Feelings come and go like clouds in a windy sky. Conscious breathing is my anchor.", "author": "Thich Nhat Hanh"},
        ]
    }
    
    @classmethod
    def get_random_quote(cls, category: str = "motivation") -> dict:
        """Get a random quote from specified category"""
        if category in cls.QUOTES:
            return random.choice(cls.QUOTES[category])
        return random.choice(cls.QUOTES["motivation"])
    
    @classmethod
    def get_all_quotes(cls) -> List[str]:
        """Get all quotes for display"""
        all_quotes = []
        for category in cls.QUOTES.values():
            all_quotes.extend([q["text"] for q in category])
        return all_quotes

# ============================================================================
# IMAGE GENERATOR
# ============================================================================
class ModernQuoteGenerator:
    """Generate modern quote images with animated backgrounds"""
    
    def __init__(self):
        self.bg_generator = AnimatedBackground()
        
    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines[:4]  # Maximum 4 lines
    
    def create_quote_image(self, 
                          quote_text: str, 
                          author: str, 
                          size: Tuple[int, int],
                          bg_style: str = "wave",
                          time_offset: float = 0) -> Image.Image:
        """Create a modern quote image"""
        width, height = size
        
        # Create background based on style
        if bg_style == "particle":
            bg = self.bg_generator.create_particle_field(width, height, time_offset)
        elif bg_style == "geometric":
            bg = self.bg_generator.create_geometric_lines(width, height, time_offset)
        else:  # wave gradient
            bg = self.bg_generator.create_wave_gradient(width, height, time_offset)
        
        # Create a clean copy for drawing
        img = bg.copy()
        draw = ImageDraw.Draw(img)
        
        # Try to load modern font, fallback to default
        try:
            # Try to use a sans-serif font for modern look
            title_font = ImageFont.truetype("arialbd.ttf", 80)
            quote_font = ImageFont.truetype("arial.ttf", 60)
            author_font = ImageFont.truetype("ariali.ttf", 40)
            brand_font = ImageFont.truetype("arial.ttf", 30)
        except:
            # Fallback to default
            title_font = ImageFont.load_default()
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
            brand_font = ImageFont.load_default()
        
        # Draw quote text
        max_text_width = width - 200
        lines = self.wrap_text(quote_text, quote_font, max_text_width)
        
        # Calculate total text height
        line_height = 80
        total_text_height = len(lines) * line_height + 40
        
        # Center vertically
        start_y = (height - total_text_height) // 2
        
        # Draw each line
        for i, line in enumerate(lines):
            bbox = quote_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + i * line_height
            
            # Text shadow for depth
            draw.text((x + 3, y + 3), line, 
                     font=quote_font, 
                     fill=BRAND_COLORS["dark_navy"][:3] + (100,))
            
            # Main text
            draw.text((x, y), line,
                     font=quote_font,
                     fill=BRAND_COLORS["white"])
        
        # Draw author
        author_text = f"— {author}"
        author_bbox = author_font.getbbox(author_text)
        author_x = (width - (author_bbox[2] - author_bbox[0])) // 2
        author_y = start_y + total_text_height + 20
        
        draw.text((author_x, author_y), author_text,
                 font=author_font,
                 fill=BRAND_COLORS["light_grey"])
        
        # Draw subtle divider line
        line_length = 300
        line_x = (width - line_length) // 2
        line_y = author_y + 60
        
        # Gradient line (green to transparent)
        for i in range(line_length):
            alpha = int(255 * (1 - i / line_length))
            color = BRAND_COLORS["primary_green"][:3] + (alpha,)
            draw.line([(line_x + i, line_y), (line_x + i, line_y + 3)],
                     fill=color, width=3)
        
        # Draw brand in corner (minimal)
        brand_text = BRAND_NAME
        draw.text((width - 200, height - 40), brand_text,
                 font=brand_font,
                 fill=BRAND_COLORS["medium_grey"])
        
        return img
    
    def create_animation_frames(self, 
                               quote_text: str, 
                               author: str, 
                               size: Tuple[int, int],
                               bg_style: str = "wave") -> List[Image.Image]:
        """Create frames for animation"""
        frames = []
        total_frames = ANIMATION_SETTINGS["total_frames"]
        
        for frame in range(total_frames):
            time_offset = frame / ANIMATION_SETTINGS["fps"]
            
            # Create frame
            frame_img = self.create_quote_image(
                quote_text, author, size, bg_style, time_offset
            )
            
            # Convert to RGB (no alpha for video)
            frames.append(frame_img.convert("RGB"))
        
        return frames

# ============================================================================
# VIDEO GENERATOR (using PIL only)
# ============================================================================
class VideoGenerator:
    """Generate MP4 video using only PIL (no external dependencies)"""
    
    @staticmethod
    def frames_to_video_bytes(frames: List[Image.Image]) -> bytes:
        """Convert frames to MP4 video bytes"""
        # Note: In production, you might want to use a proper video encoder
        # For Streamlit Cloud compatibility, we'll create an animated WebP
        # which can be displayed as video-like content
        
        # Create animated WebP (plays like video in browsers)
        buffer = io.BytesIO()
        
        # Save as WebP animation (supported in modern browsers)
        frames[0].save(
            buffer,
            format='WEBP',
            save_all=True,
            append_images=frames[1:],
            duration=1000 // ANIMATION_SETTINGS["fps"],  # ms per frame
            loop=0,
            quality=90
        )
        
        return buffer.getvalue()

# ============================================================================
# MINIMAL STREAMLIT UI
# ============================================================================
def main():
    # Hide Streamlit default elements for minimal UI
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {background: #0d1b2a;}
        .stButton > button {
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s;
            width: 100%;
        }
        .stButton > button:hover {
            background: #388E3C;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        }
        .stSelectbox > div > div {
            background: white;
            border-radius: 8px;
        }
        .stTextInput > div > div > input {
            background: white;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .quote-preview {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin: 0 auto;
        }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_quote' not in st.session_state:
        st.session_state.current_quote = QuoteManager.get_random_quote()
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'current_frames' not in st.session_state:
        st.session_state.current_frames = None
    
    # Minimal header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #4CAF50; margin-bottom: 0.5rem;">🧠 STILL MIND</h1>
            <p style="color: #E0E0E0; opacity: 0.8;">Modern quote generator for focused minds</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content - minimal controls
    col_left, col_main, col_right = st.columns([1, 2, 1])
    
    with col_main:
        # Minimal controls in expander
        with st.expander("⚙️ SETTINGS", expanded=False):
            col_set1, col_set2 = st.columns(2)
            
            with col_set1:
                quote_category = st.selectbox(
                    "Category",
                    ["motivation", "wisdom", "success", "mindfulness"],
                    index=0,
                    label_visibility="collapsed"
                )
            
            with col_set2:
                bg_style = st.selectbox(
                    "Background",
                    ["wave", "particle", "geometric"],
                    index=0,
                    label_visibility="collapsed"
                )
            
            col_set3, col_set4 = st.columns(2)
            with col_set3:
                size_option = st.selectbox(
                    "Size",
                    list(SIZES.keys()),
                    index=0,
                    label_visibility="collapsed"
                )
            
            with col_set4:
                custom_quote = st.text_input(
                    "Custom Quote",
                    placeholder="Enter your own quote...",
                    label_visibility="collapsed"
                )
            
            # Generate button
            if st.button("✨ GENERATE", type="primary"):
                if custom_quote:
                    st.session_state.current_quote = {
                        "text": custom_quote,
                        "author": BRAND_NAME
                    }
                else:
                    st.session_state.current_quote = QuoteManager.get_random_quote(quote_category)
                
                # Generate image
                generator = ModernQuoteGenerator()
                img = generator.create_quote_image(
                    st.session_state.current_quote["text"],
                    st.session_state.current_quote["author"],
                    SIZES[size_option],
                    bg_style
                )
                
                # Generate frames for animation
                frames = generator.create_animation_frames(
                    st.session_state.current_quote["text"],
                    st.session_state.current_quote["author"],
                    SIZES[size_option],
                    bg_style
                )
                
                st.session_state.current_image = img
                st.session_state.current_frames = frames
                st.session_state.current_size = size_option
                
                st.success("Generated!")
    
    # Display area (full width below controls)
    st.markdown("---")
    
    if st.session_state.current_image:
        # Preview
        col_preview1, col_preview2, col_preview3 = st.columns([1, 3, 1])
        
        with col_preview2:
            st.markdown(f'<div class="quote-preview">', unsafe_allow_html=True)
            st.image(st.session_state.current_image, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Minimal info
            st.caption(f"📐 {st.session_state.current_size} • 🎨 {bg_style.title()} • ⏱️ {ANIMATION_SETTINGS['duration']}s")
            
            # Download buttons
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                # JPEG Download
                img_buffer = io.BytesIO()
                st.session_state.current_image.save(
                    img_buffer, 
                    format='JPEG', 
                    quality=95,
                    optimize=True
                )
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="📥 DOWNLOAD JPEG",
                    data=img_buffer.getvalue(),
                    file_name=f"stillmind_quote_{timestamp}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            with col_dl2:
                # Video Download
                if st.session_state.current_frames:
                    video_data = VideoGenerator.frames_to_video_bytes(
                        st.session_state.current_frames
                    )
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="🎬 DOWNLOAD ANIMATION",
                        data=video_data,
                        file_name=f"stillmind_quote_{timestamp}.webp",
                        mime="image/webp",
                        use_container_width=True
                    )
            
            # Quick actions
            st.markdown("---")
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if st.button("🔄 NEW QUOTE", use_container_width=True):
                    # Clear and regenerate
                    st.session_state.current_image = None
                    st.session_state.current_frames = None
                    st.rerun()
            
            with col_action2:
                if st.button("🎲 RANDOM STYLE", use_container_width=True):
                    # Keep quote, change style
                    st.rerun()
    
    else:
        # Empty state
        col_empty1, col_empty2, col_empty3 = st.columns([1, 2, 1])
        with col_empty2:
            st.markdown("""
            <div style="text-align: center; padding: 4rem; color: #9E9E9E;">
                <h3>👆 Configure & Generate</h3>
                <p>Select your preferences and click GENERATE to create your first quote.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Minimal footer
    st.markdown("""
    <div style="text-align: center; color: #616161; padding: 2rem 0; font-size: 0.9rem;">
        <p>🧠 {brand} • Modern minimal design • Focus on what matters</p>
    </div>
    """.format(brand=BRAND_NAME), unsafe_allow_html=True)

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == "__main__":
    # No external dependencies required
    main()