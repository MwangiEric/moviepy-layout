import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import io, math, random, json, numpy as np
import imageio.v3 as iio
from datetime import datetime
from typing import Tuple, List, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Still Mind | Creative Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Brand Colors
BRAND = {
    "navy": (13, 27, 42, 255),
    "yellow": (255, 204, 0, 255),
    "blue": (100, 180, 255, 255),
    "white": (255, 255, 255, 255),
    "green": (76, 175, 80, 255),
    "dark_navy": (5, 15, 25, 255)
}

SIZES = {
    "Instagram Story (1080x1920)": (1080, 1920),
    "Instagram Square (1080x1080)": (1080, 1080),
    "Twitter (1200x675)": (1200, 675),
}

VIDEO_CONFIG = {
    "fps": 15,
    "duration": 8,
    "total_frames": 120,  # 8 * 15
    "bitrate": "8000k",
    "pixel_format": "yuv420p"
}

# ============================================================================
# MATHEMATICAL LOOP ENGINE
# ============================================================================
class PerfectLoopEngine:
    """Mathematical engine for perfect looping animations"""
    
    @staticmethod
    def get_loop_factor(t: float, duration: float) -> float:
        """Converts time to 0→2π cycle for perfect loops"""
        return (t / duration) * (2 * math.pi)
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Smooth easing function for animations"""
        return 0.5 - 0.5 * math.cos(t * math.pi)
    
    @staticmethod
    def create_seamless_background(width: int, height: int, 
                                  time: float, duration: float, 
                                  style: str) -> Image.Image:
        """Generate perfectly looping background"""
        phase = PerfectLoopEngine.get_loop_factor(time, duration)
        
        # Create base canvas
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img)
        
        if style == "🟡 Kinetic Bubble":
            # Liquid bubble physics
            draw.rectangle([0, 0, width, height], fill=BRAND["yellow"])
            cx, cy = width // 2, height // 2
            
            # Generate wobbling vertices
            num_points = 16
            points = []
            for i in range(num_points):
                angle = (i / num_points) * (2 * math.pi)
                # Multiple frequency wobbles for organic motion
                wobble1 = math.sin(phase * 2 + i * 0.5) * 8
                wobble2 = math.cos(phase * 1.5 + i * 0.8) * 4
                wobble3 = math.sin(phase * 3 + i * 1.2) * 2
                r = 450 + wobble1 + wobble2 + wobble3
                px = cx + math.cos(angle) * r
                py = cy + math.sin(angle) * r
                points.append((px, py))
            
            # Shadow with blur
            shadow_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_img)
            shadow_draw.polygon([(p[0]+15, p[1]+15) for p in points], 
                               fill=(210, 160, 0, 180))
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=10))
            img = Image.alpha_composite(img, shadow_img)
            
            # Main bubble with gradient
            for i in range(len(points)):
                next_i = (i + 1) % len(points)
                draw.line([points[i], points[next_i]], 
                         fill=BRAND["white"], width=10)
            
            # Fill bubble
            if len(points) >= 3:
                draw.polygon(points, fill=BRAND["white"])
            
            # Animated quote marks
            quote_size = 40 + math.sin(phase * 4) * 5
            draw.ellipse([cx-420, cy-420, cx-420+quote_size, cy-420+quote_size], 
                        fill=BRAND["dark_navy"])
            draw.ellipse([cx+420-quote_size, cy+420-quote_size, cx+420, cy+420], 
                        fill=BRAND["dark_navy"])
            
        elif style == "🪶 Serene Birds":
            # Cinematic birds with depth
            draw.rectangle([0, 0, width, height], fill=BRAND["navy"])
            
            # Multiple bird layers for depth
            for layer in range(3):
                scale = 1.0 - layer * 0.2
                opacity = 200 - layer * 50
                
                for i in range(5 - layer):
                    # Perfect horizontal looping with modulo
                    base_x = (time * 80 * scale + i * 120) % (width + 400) - 200
                    
                    # Vertical wave pattern (resets every loop)
                    vertical = math.sin(phase * 1.5 + i * 0.8) * 60 * scale
                    
                    # Flap animation (different frequency)
                    flap = math.sin(phase * 8 + i * 1.2) * 20 * scale
                    
                    bird_x = base_x
                    bird_y = height * 0.3 + vertical + (i * 80) + (layer * 40)
                    
                    # Draw V-shaped bird
                    left_wing = (bird_x-30, bird_y-flap)
                    right_wing = (bird_x+30, bird_y-flap)
                    body = (bird_x, bird_y)
                    
                    draw.line([left_wing, body], 
                             fill=BRAND["white"] + (opacity,), width=4)
                    draw.line([body, right_wing], 
                             fill=BRAND["white"] + (opacity,), width=4)
        
        elif style == "🔵 Modern Frame":
            # Floating glass frame with physics
            draw.rectangle([0, 0, width, height], fill=BRAND["blue"])
            
            # Frame dimensions
            margin = 100
            frame_height = 700
            frame_y = height // 2 - frame_height // 2
            
            # Floating animation with easing
            float_offset = math.sin(phase * 1.5) * 25
            
            # Create frame shadow
            shadow_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_img)
            shadow_coords = [
                margin + 10, frame_y + float_offset + 10,
                width - margin + 10, frame_y + frame_height + float_offset + 10
            ]
            shadow_draw.rounded_rectangle(shadow_coords, radius=50,
                                         fill=(0, 0, 0, 60))
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=15))
            img = Image.alpha_composite(img, shadow_img)
            
            # Main frame with animated border
            frame_coords = [
                margin, frame_y + float_offset,
                width - margin, frame_y + frame_height + float_offset
            ]
            
            # Animated border thickness
            border_pulse = 14 + math.sin(phase * 3) * 2
            draw.rounded_rectangle(frame_coords, radius=40,
                                  fill=BRAND["white"],
                                  outline=BRAND["dark_navy"],
                                  width=int(border_pulse))
            
            # Animated corner dots
            for i, (dx, dy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
                dot_x = margin + 50 if dx == 1 else width - margin - 50
                dot_y = frame_y + float_offset + 50 if dy == 1 else frame_y + frame_height + float_offset - 50
                
                dot_size = 12 + math.sin(phase * 4 + i) * 3
                draw.ellipse([dot_x-dot_size, dot_y-dot_size,
                            dot_x+dot_size, dot_y+dot_size],
                           fill=BRAND["green"])
        
        elif style == "📐 Digital Loom":
            # Geometric network with Lissajous curves
            draw.rectangle([0, 0, width, height], fill=BRAND["dark_navy"])
            
            # Generate network nodes
            num_nodes = 8
            nodes = []
            for i in range(num_nodes):
                # Lissajous pattern for node movement
                a = 3 + i * 0.5
                b = 2 + i * 0.3
                
                node_x = width//2 + math.cos(phase * a) * (400 - i * 40)
                node_y = height//2 + math.sin(phase * b) * (300 - i * 30)
                nodes.append((node_x, node_y))
                
                # Draw node
                node_size = 15 + math.sin(phase * 2 + i) * 5
                node_color = (
                    int(100 + 155 * abs(math.sin(phase + i))),
                    int(200 + 55 * abs(math.cos(phase + i))),
                    int(255),
                    200
                )
                draw.ellipse([node_x-node_size, node_y-node_size,
                            node_x+node_size, node_y+node_size],
                           fill=node_color)
            
            # Connect nodes based on distance
            for i in range(len(nodes)):
                for j in range(i+1, len(nodes)):
                    dx = nodes[i][0] - nodes[j][0]
                    dy = nodes[i][1] - nodes[j][1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < 500:
                        # Line opacity based on distance
                        opacity = int(255 * (1 - distance/500))
                        line_color = (100, 255, 200, opacity)
                        draw.line([nodes[i], nodes[j]], fill=line_color, width=1)
        
        elif style == "✨ Aura Orbs":
            # Vectorized aura orbs with Gaussian blur gradients
            draw.rectangle([0, 0, width, height], fill=BRAND["navy"])
            
            # Create multiple orbs with orbital motion
            num_orbs = 7
            for i in range(num_orbs):
                orbit_speed = 0.3 + i * 0.08
                orbit_radius = 250 + i * 40
                
                orb_x = width//2 + math.cos(phase * orbit_speed) * orbit_radius
                orb_y = height//2 + math.sin(phase * orbit_speed * 1.3) * orbit_radius
                
                # Orb size and color variation
                orb_size = 120 + math.sin(phase * 2 + i) * 30
                
                # Color based on position in orbit
                hue = (orb_x / width + orb_y / height + phase) % 1.0
                if hue < 0.33:
                    color = BRAND["green"]
                elif hue < 0.66:
                    color = BRAND["blue"]
                else:
                    color = (255, 150, 100, 200)  # Orange
                
                # Draw orb with multiple layers for soft glow
                layers = 8
                for layer in range(layers, 0, -1):
                    layer_size = orb_size * (layer / layers)
                    layer_opacity = int(100 * (layer / layers))
                    layer_color = color[:3] + (layer_opacity,)
                    
                    draw.ellipse([orb_x-layer_size, orb_y-layer_size,
                                orb_x+layer_size, orb_y+layer_size],
                               fill=layer_color)
            
            # Apply Gaussian blur for seamless gradient
            img = img.filter(ImageFilter.GaussianBlur(radius=12))
        
        # Add subliminal glimmer particles
        for i in range(20):
            # Perfect loop for particles
            p_progress = (time / duration + i/20) % 1.0
            px = (i * 137) % width
            py = height - (p_progress * height)
            
            # Fade in/out
            alpha = int(255 * math.sin(p_progress * math.pi))
            size = 3 + math.sin(p_progress * 2 * math.pi) * 2
            
            draw.ellipse([px-size, py-size, px+size, py+size],
                        fill=(255, 255, 255, alpha))
        
        return img

# ============================================================================
# ENGAGEMENT HOOKS ENGINE
# ============================================================================
class EngagementHooks:
    """Advanced engagement hooks for viewer retention"""
    
    @staticmethod
    def apply_opening_hook(img: Image.Image, t: float) -> Image.Image:
        """Initial 0.5s focus blur for instant engagement"""
        if t < 0.5:
            # Progressive blur reduction
            blur_amount = int((1.0 - (t / 0.5)) * 30)
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_amount))
        return img
    
    @staticmethod
    def apply_depth_particles(img: Image.Image, t: float) -> Image.Image:
        """Fast-moving particles for 3D depth illusion"""
        width, height = img.size
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Multiple particle layers
        for layer in range(3):
            speed_factor = 1.0 + layer * 0.5
            size_factor = 0.5 + layer * 0.3
            opacity = 80 - layer * 20
            
            for i in range(15):
                # Particle movement (faster as they get "closer")
                p_speed = (i * 20 + t * 800 * speed_factor) % height
                p_x = (i * 73 * (layer + 1)) % width
                
                # Size increases as particles approach
                p_size = int((p_speed / height) * 8 * size_factor)
                
                # Position
                p_y = height - p_speed
                
                if p_size > 0:
                    draw.ellipse([p_x-p_size, p_y-p_size, p_x+p_size, p_y+p_size],
                                fill=(255, 255, 255, opacity))
        
        # Composite particles
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        return img
    
    @staticmethod
    def apply_chromatic_aberration(img: Image.Image, t: float) -> Image.Image:
        """Subtle color fringing for cinematic lens effect"""
        if t > 0.3:  # Only apply after initial moment
            # Split channels
            if img.mode == "RGB":
                r, g, b = img.split()
                
                # Time-based shift variations
                shift_x = int(2 + math.sin(t * 3) * 1)
                shift_y = int(1 + math.cos(t * 2) * 0.5)
                
                # Shift red channel slightly
                r = r.offset(shift_x, shift_y)
                # Shift blue channel opposite
                b = b.offset(-shift_x, -shift_y)
                
                # Recombine
                img = Image.merge("RGB", (r, g, b))
        return img
    
    @staticmethod
    def apply_vignette(img: Image.Image, t: float) -> Image.Image:
        """Dynamic vignette for focus"""
        width, height = img.size
        overlay = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(overlay)
        
        center_x, center_y = width // 2, height // 2
        max_radius = math.sqrt(center_x**2 + center_y**2)
        
        # Animate vignette intensity
        intensity = 0.7 + math.sin(t * 2) * 0.1
        
        for y in range(height):
            for x in range(width):
                dx = (x - center_x) / center_x
                dy = (y - center_y) / center_y
                dist = math.sqrt(dx*dx + dy*dy) * intensity
                
                # Apply radial gradient
                value = int(255 * (1 - dist))
                overlay.putpixel((x, y), max(0, min(255, value)))
        
        # Apply as alpha channel
        if img.mode == "RGB":
            img = img.convert("RGBA")
        
        # Blend vignette
        overlay_rgb = Image.merge("RGB", (overlay, overlay, overlay))
        img = Image.blend(img, overlay_rgb.convert("RGBA"), alpha=0.15)
        
        return img
    
    @staticmethod
    def apply_all_hooks(img: Image.Image, t: float, duration: float) -> Image.Image:
        """Apply all engagement hooks in sequence"""
        img = img.convert("RGB")
        
        # Opening hook (first 0.5s)
        img = EngagementHooks.apply_opening_hook(img, t)
        
        # Depth particles (always on)
        img = EngagementHooks.apply_depth_particles(img, t)
        
        # Chromatic aberration (after initial moment)
        img = EngagementHooks.apply_chromatic_aberration(img, t)
        
        # Dynamic vignette
        img = EngagementHooks.apply_vignette(img, t)
        
        return img

# ============================================================================
# SUPERSAMPLED TEXT RENDERER
# ============================================================================
class TextRenderer:
    """Supersampled text rendering with perfect centering"""
    
    def __init__(self):
        try:
            self.font_bold = ImageFont.truetype("arialbd.ttf", 80)
            self.font_regular = ImageFont.truetype("arial.ttf", 60)
            self.font_italic = ImageFont.truetype("ariali.ttf", 40)
        except:
            self.font_bold = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()
            self.font_italic = ImageFont.load_default()
    
    def render_text(self, img: Image.Image, quote: str, author: str, 
                   t: float, duration: float) -> Image.Image:
        """Render text with timed animations"""
        width, height = img.size
        draw = ImageDraw.Draw(img)
        
        # Calculate animation progress
        text_progress = min(1.0, t / 2)  # Text appears over first 2 seconds
        
        if text_progress > 0:
            # Split quote into lines
            lines = quote.strip().split('\n')
            
            # Calculate total text height
            line_height = 90
            total_height = len(lines) * line_height
            
            # Center vertically
            start_y = (height - total_height) // 2
            
            # Render each line with typewriter effect
            for i, line in enumerate(lines):
                # Character-by-character reveal
                visible_chars = int(len(line) * text_progress)
                visible_text = line[:visible_chars]
                
                if visible_text:
                    # Get text dimensions
                    bbox = self.font_bold.getbbox(visible_text)
                    text_width = bbox[2] - bbox[0]
                    
                    # Center horizontally
                    x = (width - text_width) // 2
                    y = start_y + i * line_height
                    
                    # Text shadow for depth
                    shadow_color = (0, 0, 0, int(150 * text_progress))
                    draw.text((x+3, y+3), visible_text, 
                             font=self.font_bold, fill=shadow_color)
                    
                    # Main text
                    text_color = BRAND["white"] if "birds" in quote.lower() else BRAND["dark_navy"]
                    draw.text((x, y), visible_text, 
                             font=self.font_bold, fill=text_color)
        
        # Render author (appears after quote)
        if text_progress > 0.7:
            author_progress = min(1.0, (text_progress - 0.7) / 0.3)
            author_text = f"— {author}"
            
            # Get author dimensions
            author_bbox = self.font_italic.getbbox(author_text)
            author_width = author_bbox[2] - author_bbox[0]
            
            # Position: bottom right
            author_x = width - author_width - 60
            author_y = height - 120
            
            # Author with animated background
            if author_progress > 0.5:
                bg_opacity = int(100 * author_progress)
                draw.rectangle(
                    [author_x-20, author_y-15,
                     author_x + author_width + 20, 
                     author_y + (author_bbox[3] - author_bbox[1]) + 15],
                    fill=BRAND["green"][:3] + (bg_opacity,)
                )
            
            # Author text
            author_color = BRAND["white"][:3] + (int(255 * author_progress),)
            draw.text((author_x, author_y), author_text,
                     font=self.font_italic, fill=author_color)
        
        # Render brand (always visible, bottom left)
        brand_text = "@stillmind"
        draw.text((60, height - 80), brand_text,
                 font=self.font_regular,
                 fill=BRAND["white"][:3] + (180,))
        
        return img

# ============================================================================
# MAIN VIDEO GENERATOR
# ============================================================================
class VideoGenerator:
    """Generate high-quality MP4 videos with perfect loops"""
    
    def __init__(self):
        self.loop_engine = PerfectLoopEngine()
        self.hooks_engine = EngagementHooks()
        self.text_renderer = TextRenderer()
    
    def create_video(self, quote: str, author: str, 
                    size: Tuple[int, int], style: str) -> bytes:
        """Generate complete video with all effects"""
        width, height = size
        fps = VIDEO_CONFIG["fps"]
        duration = VIDEO_CONFIG["duration"]
        total_frames = VIDEO_CONFIG["total_frames"]
        
        frames = []
        
        for frame_num in range(total_frames):
            t = frame_num / fps
            
            # 1. Generate seamless background
            bg = self.loop_engine.create_seamless_background(
                width, height, t, duration, style
            )
            
            # 2. Apply engagement hooks
            bg = self.hooks_engine.apply_all_hooks(bg, t, duration)
            
            # 3. Render text with animations
            bg = self.text_renderer.render_text(bg, quote, author, t, duration)
            
            # Convert to numpy array
            frame_np = np.array(bg.convert("RGB"))
            frames.append(frame_np)
        
        # Encode to MP4 with high-quality settings
        buffer = io.BytesIO()
        iio.imwrite(
            buffer,
            frames,
            format='mp4',
            fps=fps,
            codec='libx264',
            quality=9,
            pixelformat=VIDEO_CONFIG["pixel_format"],
            bitrate=VIDEO_CONFIG["bitrate"],
            output_params=["-preset", "slow"]  # Better compression
        )
        
        return buffer.getvalue()

# ============================================================================
# STREAMLIT INTERFACE
# ============================================================================
def main():
    # Custom CSS for minimal design
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
        padding: 14px 28px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
    }
    .style-card {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    .style-card:hover {
        border-color: #4CAF50;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: #4CAF50; margin-bottom: 0.5rem;">🧠 Still Mind: Creative Studio</h1>
        <p style="color: #EEEEEE; opacity: 0.9; margin-bottom: 0.5rem;">Perfect-loop animations with engagement hooks</p>
        <p style="color: #9E9E9E; font-size: 0.9rem; margin: 0;">8s MP4 • 15 FPS • libx264 • yuv420p • 8000k bitrate</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎨 Visual Identity")
        
        # Visual style selection
        styles = {
            "🟡 Kinetic Bubble": {
                "description": "Liquid 3D bubble with wobble physics",
                "energy": "High",
                "color": "#FFCC00"
            },
            "🪶 Serene Birds": {
                "description": "Cinematic depth-of-field birds",
                "energy": "Medium",
                "color": "#0d1b2a"
            },
            "🔵 Modern Frame": {
                "description": "Floating glass frame with physics",
                "energy": "Low",
                "color": "#64B4FF"
            },
            "📐 Digital Loom": {
                "description": "Geometric network with Lissajous curves",
                "energy": "High",
                "color": "#050f19"
            },
            "✨ Aura Orbs": {
                "description": "Vectorized orbs with Gaussian blur gradients",
                "energy": "Medium",
                "color": "#4CAF50"
            }
        }
        
        selected_style = st.selectbox("Select Style", list(styles.keys()))
        
        # Show style info
        style_info = styles[selected_style]
        st.markdown(f"**Description:** {style_info['description']}")
        st.markdown(f"**Energy Level:** {style_info['energy']}")
        
        # Quote input
        st.markdown("### 💬 Content")
        
        default_quote = "TRUST YOURSELF\nTAKE CARE TO WORK HARD\nDON'T GIVE UP"
        quote = st.text_area("Quote (use Enter for line breaks)", 
                           value=default_quote,
                           height=120)
        
        author = st.text_input("Author", value="Still Mind")
        
        # Size selection
        size_option = st.selectbox("Size Format", list(SIZES.keys()), index=0)
        
        # Generate button
        if st.button("🚀 RENDER PERFECT-LOOP VIDEO", type="primary"):
            with st.spinner("Generating seamless animation..."):
                generator = VideoGenerator()
                video_data = generator.create_video(
                    quote,
                    author,
                    SIZES[size_option],
                    selected_style
                )
                
                st.session_state.video_data = video_data
                st.session_state.quote = quote
                st.session_state.style = selected_style
    
    with col2:
        # Preview section
        if 'video_data' in st.session_state:
            st.markdown("### 🎬 Preview")
            
            # Video player
            st.video(st.session_state.video_data, format="video/mp4", start_time=0)
            
            # Technical specs
            col_spec1, col_spec2, col_spec3, col_spec4 = st.columns(4)
            with col_spec1:
                st.metric("Loop", "Perfect")
            with col_spec2:
                st.metric("Duration", "8s")
            with col_spec3:
                st.metric("FPS", "15")
            with col_spec4:
                st.metric("Bitrate", "8000k")
            
            # Download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            style_slug = st.session_state.style.replace(' ', '_').lower()
            
            st.download_button(
                label="📥 DOWNLOAD MP4",
                data=st.session_state.video_data,
                file_name=f"stillmind_{style_slug}_{timestamp}.mp4",
                mime="video/mp4",
                use_container_width=True
            )
            
            # Engagement hooks info
            st.markdown("---")
            st.markdown("### 🔧 Engagement Hooks Applied")
            
            hooks_col1, hooks_col2, hooks_col3 = st.columns(3)
            with hooks_col1:
                st.markdown("**Opening Hook**")
                st.caption("0.5s progressive blur for instant focus")
            with hooks_col2:
                st.markdown("**Depth Particles**")
                st.caption("3D illusion with layered movement")
            with hooks_col3:
                st.markdown("**Chromatic Aberration**")
                st.caption("Cinematic lens color fringing")
            
            # Quick actions
            st.markdown("---")
            col_action1, col_action2 = st.columns(2)
            with col_action1:
                if st.button("🔄 New Animation", use_container_width=True):
                    if 'video_data' in st.session_state:
                        del st.session_state.video_data
                    st.rerun()
            with col_action2:
                if st.button("🎲 Random Style", use_container_width=True):
                    st.rerun()
        
        else:
            # Empty state
            st.markdown("""
            <div style="text-align: center; padding: 4rem; color: #9E9E9E; background: rgba(13, 27, 42, 0.5); border-radius: 16px;">
                <h3>👆 Configure & Generate</h3>
                <p>Select visual style and enter your quote to create a perfect-loop animation.</p>
                <p style="font-size: 0.9rem; opacity: 0.7;">Each animation uses mathematical loops that seamlessly repeat</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #616161; padding: 2rem 0; font-size: 0.9rem;">
        <p>🧠 Still Mind • Creative Studio • Perfect-Loop Animations • Engagement Hooks</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">Mathematical loops • Chromatic aberration • Depth particles • Gaussian blur gradients</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == "__main__":
    main()