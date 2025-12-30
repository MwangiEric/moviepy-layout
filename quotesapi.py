import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import io, os, math, time, random, json, requests
import numpy as np
from datetime import datetime
import imageio.v3 as iio
from groq import Groq
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Still Mind | Vectorized Animations",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Brand Configuration
BRAND_COLORS = {
    "primary_green": (76, 175, 80, 255),
    "dark_green": (56, 142, 60, 255),
    "navy_blue": (13, 27, 42, 255),
    "dark_navy": (5, 15, 25, 255),
    "white": (255, 255, 255, 255),
    "light_grey": (224, 224, 224, 255),
    "medium_grey": (158, 158, 158, 255),
    "accent_blue": (25, 118, 210, 255),
    "brand_yellow": (255, 204, 0, 255),
    "sky_blue": (100, 180, 255, 255)
}

SIZES = {
    "Instagram Square (1080x1080)": (1080, 1080),
    "Instagram Story (1080x1920)": (1080, 1920),
    "Twitter Post (1200x675)": (1200, 675),
}

@dataclass
class AnimationConfig:
    duration: int = 8
    fps: int = 15
    total_frames: int = 120
    bitrate: str = "8000k"
    pixel_format: str = "yuv420p"

# ============================================================================
# VECTORIZED BACKGROUND GENERATORS
# ============================================================================
class VectorizedBackgrounds:
    """Vectorized background animations using numpy for speed and quality"""
    
    @staticmethod
    def create_flocking_birds(width: int, height: int, time_offset: float) -> Image.Image:
        """Flocking birds with Boids algorithm simulation"""
        # Create base canvas
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Parameters for flock simulation
        num_birds = 7
        flock_center_x = width // 2
        flock_center_y = height // 3
        
        # Boids parameters
        separation_distance = 80
        alignment_strength = 0.1
        cohesion_strength = 0.05
        
        # Time-based flock movement
        flock_x = flock_center_x + math.sin(time_offset * 0.5) * 200
        flock_y = flock_center_y + math.cos(time_offset * 0.3) * 100
        
        # Generate bird positions using Boids-like logic
        for i in range(num_birds):
            # Base position with separation
            angle = (i / num_birds) * (2 * math.pi)
            radius = 60 + math.sin(time_offset * 2 + i) * 20
            
            # Flock movement calculations
            separation_x = math.cos(angle + time_offset) * separation_distance
            separation_y = math.sin(angle + time_offset) * separation_distance
            
            # Alignment (birds tend to fly in same direction)
            alignment_x = math.cos(time_offset * 1.5) * 100
            alignment_y = math.sin(time_offset * 1.2) * 50
            
            # Cohesion (birds move toward flock center)
            to_center_x = flock_x - (flock_x + separation_x)
            to_center_y = flock_y - (flock_y + separation_y)
            
            # Final position
            x = flock_x + separation_x + alignment_x * alignment_strength + to_center_x * cohesion_strength
            y = flock_y + separation_y + alignment_y * alignment_strength + to_center_y * cohesion_strength
            
            # Ensure birds stay in frame
            x = max(50, min(width - 50, x))
            y = max(100, min(height - 100, y))
            
            # Wing flap animation
            wing_angle = time_offset * 8 + i
            flap_height = 15 * abs(math.sin(wing_angle))
            
            # Draw V-shaped bird (silhouette)
            # Main body line
            body_length = 40
            body_x = x + math.cos(time_offset) * 5
            body_y = y + math.sin(time_offset) * 5
            
            # Wings
            wing_length = 25
            left_wing_end_x = body_x - wing_length * math.cos(math.pi/4)
            left_wing_end_y = body_y - wing_length * math.sin(math.pi/4) - flap_height
            
            right_wing_end_x = body_x + wing_length * math.cos(math.pi/4)
            right_wing_end_y = body_y - wing_length * math.sin(math.pi/4) - flap_height
            
            # Draw bird with gradient opacity for depth
            opacity = int(180 + 75 * math.sin(time_offset + i))
            color = (255, 255, 255, opacity)
            
            # Draw connecting lines for V shape
            draw.line([(left_wing_end_x, left_wing_end_y), (body_x, body_y)], 
                     fill=color, width=3)
            draw.line([(body_x, body_y), (right_wing_end_x, right_wing_end_y)], 
                     fill=color, width=3)
            
            # Optional: Add subtle motion blur trail
            if time_offset > 0.5:
                trail_length = 30
                trail_opacity = int(opacity * 0.3)
                trail_color = (255, 255, 255, trail_opacity)
                draw.line([(x - 10, y), (x - 40, y - 20)], 
                         fill=trail_color, width=2)
        
        # Apply Gaussian blur for motion effect
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        return img
    
    @staticmethod
    def create_geometric_pulse(width: int, height: int, time_offset: float) -> Image.Image:
        """Geometric pulse with Lissajous curves and expanding grids"""
        # Create base with dark navy
        img = Image.new("RGBA", (width, height), BRAND_COLORS["dark_navy"])
        draw = ImageDraw.Draw(img)
        
        center_x, center_y = width // 2, height // 2
        
        # Lissajous curve parameters
        a = 3  # Frequency in x
        b = 2  # Frequency in y
        delta = math.pi / 2  # Phase difference
        
        # Draw Lissajous curve
        points = []
        for i in range(0, 360, 2):
            t = math.radians(i)
            # Calculate Lissajous coordinates
            lx = center_x + 300 * math.sin(a * t + time_offset + delta)
            ly = center_y + 300 * math.sin(b * t + time_offset)
            points.append((lx, ly))
        
        # Draw the curve with gradient opacity
        for i in range(len(points) - 1):
            progress = i / len(points)
            opacity = int(150 + 105 * math.sin(progress * math.pi + time_offset))
            color = BRAND_COLORS["primary_green"][:3] + (opacity,)
            
            # Vary line thickness
            thickness = 1 + int(3 * abs(math.sin(progress * 4 + time_offset)))
            
            draw.line([points[i], points[i+1]], 
                     fill=color, width=thickness)
        
        # Add expanding concentric circles
        num_circles = 8
        for i in range(num_circles):
            # Pulse effect (60 BPM = 1 Hz = circles expand once per second)
            pulse_speed = 1.0  # 1 complete cycle per second for 60 BPM feel
            radius = (i * 80 + time_offset * 100 * pulse_speed) % 500
            
            # Calculate opacity based on radius
            circle_opacity = int(100 * (1 - radius/500))
            if circle_opacity > 0:
                color = BRAND_COLORS["accent_blue"][:3] + (circle_opacity,)
                draw.ellipse([center_x - radius, center_y - radius,
                             center_x + radius, center_y + radius],
                            outline=color, width=1)
        
        # Add mathematical grid
        grid_spacing = 60
        grid_opacity = 30
        
        # Vertical grid lines
        for x in range(0, width, grid_spacing):
            offset = math.sin(time_offset + x * 0.01) * 5
            draw.line([(x + offset, 0), (x + offset, height)],
                     fill=(255, 255, 255, grid_opacity), width=1)
        
        # Horizontal grid lines
        for y in range(0, height, grid_spacing):
            offset = math.cos(time_offset + y * 0.01) * 5
            draw.line([(0, y + offset), (width, y + offset)],
                     fill=(255, 255, 255, grid_opacity), width=1)
        
        return img
    
    @staticmethod
    def create_organic_growth(width: int, height: int, time_offset: float) -> Image.Image:
        """Organic vine growth with procedural leaves"""
        # Create base canvas
        img = Image.new("RGBA", (width, height), BRAND_COLORS["dark_navy"])
        draw = ImageDraw.Draw(img)
        
        # Vine stem position
        stem_x = width * 0.2
        
        # Calculate growth progress (0 to 1 over 8 seconds)
        growth_progress = min(1.0, time_offset / 4)
        
        # Vine height
        vine_height = height * 0.8 * growth_progress
        base_y = height - 50
        
        # Draw main vine stem with gradient thickness
        stem_thickness = 8 + 4 * math.sin(time_offset * 2)
        
        # Stem with slight curve
        points = []
        segments = 20
        for i in range(segments + 1):
            segment_progress = i / segments
            x = stem_x + math.sin(segment_progress * math.pi) * 30
            y = base_y - vine_height * segment_progress
            points.append((x, y))
        
        # Draw the curved stem
        for i in range(len(points) - 1):
            # Vary stem color slightly
            green_shade = int(BRAND_COLORS["dark_green"][1] * (0.8 + 0.2 * math.sin(i * 0.5)))
            stem_color = (BRAND_COLORS["dark_green"][0], green_shade, 
                         BRAND_COLORS["dark_green"][2], 220)
            
            # Draw segment with varying thickness
            segment_thickness = int(stem_thickness * (1 - i/segments * 0.5))
            draw.line([points[i], points[i+1]], 
                     fill=stem_color, width=segment_thickness)
        
        # Draw leaves at intervals along the vine
        if growth_progress > 0.1:
            leaf_count = int(8 * growth_progress)
            for i in range(leaf_count):
                # Position along vine
                leaf_position = (i + 1) / (leaf_count + 1)
                leaf_y = base_y - vine_height * leaf_position
                
                # Leaf x position (alternating sides)
                side = 1 if i % 2 == 0 else -1
                leaf_x = stem_x + side * (40 + math.sin(time_offset * 3 + i) * 15)
                
                # Leaf size and rotation
                leaf_size = 25 + 10 * math.sin(time_offset * 4 + i)
                leaf_angle = side * (30 + math.sin(time_offset * 2 + i) * 15)
                
                # Draw leaf (simplified as ellipse for now, could be more complex)
                leaf_color = BRAND_COLORS["primary_green"][:3] + (200,)
                
                # Create leaf shape (ellipse rotated)
                leaf_img = Image.new("RGBA", (int(leaf_size * 2), int(leaf_size)), (0, 0, 0, 0))
                leaf_draw = ImageDraw.Draw(leaf_img)
                leaf_draw.ellipse([0, 0, leaf_size * 2, leaf_size], 
                                 fill=leaf_color)
                
                # Rotate leaf
                leaf_img = leaf_img.rotate(leaf_angle, expand=True, fillcolor=(0, 0, 0, 0))
                
                # Calculate position to paste
                paste_x = int(leaf_x - leaf_img.width // 2)
                paste_y = int(leaf_y - leaf_img.height // 2)
                
                # Composite leaf onto main image
                img.paste(leaf_img, (paste_x, paste_y), leaf_img)
        
        # Add subtle particles/particulates floating around
        particle_count = 30
        for i in range(particle_count):
            # Particle position with organic movement
            px = (i * 37 + time_offset * 50) % width
            py = (i * 23 + time_offset * 30) % height
            
            # Size and opacity
            size = 1 + math.sin(time_offset * 3 + i) * 0.5
            opacity = int(100 + 100 * abs(math.sin(time_offset * 2 + i)))
            
            # Draw particle (tiny circles)
            color = BRAND_COLORS["primary_green"][:3] + (opacity,)
            draw.ellipse([px-size, py-size, px+size, py+size], fill=color)
        
        return img
    
    @staticmethod
    def create_circle_card(width: int, height: int, time_offset: float) -> Image.Image:
        """Circle card design inspired by your yellow attachment"""
        # Create brand yellow background
        img = Image.new("RGBA", (width, height), BRAND_COLORS["brand_yellow"])
        draw = ImageDraw.Draw(img)
        
        center_x, center_y = width // 2, height // 2
        
        # Pulsing central circle
        pulse_factor = 1.0 + math.sin(time_offset * 2) * 0.02
        base_radius = 400
        current_radius = base_radius * pulse_factor
        
        # Draw central white circle with animated border
        # Create a supersampled version for crisp edges
        supersample_factor = 2
        supersize = (width * supersample_factor, height * supersample_factor)
        super_img = Image.new("RGBA", supersize, BRAND_COLORS["brand_yellow"])
        super_draw = ImageDraw.Draw(super_img)
        
        # Draw circle at supersampled resolution
        super_center_x = center_x * supersample_factor
        super_center_y = center_y * supersample_factor
        super_radius = current_radius * supersample_factor
        
        super_draw.ellipse([super_center_x - super_radius, super_center_y - super_radius,
                           super_center_x + super_radius, super_center_y + super_radius],
                          fill=BRAND_COLORS["white"])
        
        # Draw animated border (pulse follows the circle)
        border_width = 15 * supersample_factor
        border_radius = super_radius + border_width // 2
        
        # Animate border color slightly
        border_brightness = 200 + int(55 * math.sin(time_offset * 3))
        border_color = (border_brightness, border_brightness, border_brightness, 255)
        
        super_draw.arc([super_center_x - border_radius, super_center_y - border_radius,
                       super_center_x + border_radius, super_center_y + border_radius],
                      start=0, end=360, fill=border_color, width=border_width)
        
        # Downscale with Lanczos for crisp edges
        img = super_img.resize((width, height), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        # Add floating geometric elements around the circle
        num_elements = 12
        for i in range(num_elements):
            angle = (i / num_elements) * (2 * math.pi) + time_offset
            distance = current_radius + 80
            
            elem_x = center_x + math.cos(angle) * distance
            elem_y = center_y + math.sin(angle) * distance
            
            # Element size and rotation
            elem_size = 15 + 5 * math.sin(time_offset * 4 + i)
            rotation = time_offset * 100 + i * 30
            
            # Draw small geometric shapes (triangles)
            points = []
            for j in range(3):
                point_angle = rotation + j * (2 * math.pi / 3)
                px = elem_x + elem_size * math.cos(point_angle)
                py = elem_y + elem_size * math.sin(point_angle)
                points.append((px, py))
            
            # Color with brand consistency
            color = BRAND_COLORS["primary_green"][:3] + (180,)
            draw.polygon(points, fill=color)
        
        return img
    
    @staticmethod
    def create_rectangle_card(width: int, height: int, time_offset: float) -> Image.Image:
        """Rectangle card design inspired by your blue attachment"""
        # Create sky blue background
        img = Image.new("RGBA", (width, height), BRAND_COLORS["sky_blue"])
        draw = ImageDraw.Draw(img)
        
        # Card dimensions and animation
        margin = 100
        card_width = width - 2 * margin
        card_height = min(600, height - 2 * margin)
        
        # Floating animation
        float_offset = math.sin(time_offset * 1.5) * 15
        card_y = (height - card_height) // 2 + float_offset
        
        # Card coordinates
        card_coords = [margin, card_y, width - margin, card_y + card_height]
        
        # Create supersampled card for crisp edges
        supersample_factor = 2
        supersize = (width * supersample_factor, height * supersample_factor)
        super_img = Image.new("RGBA", supersize, BRAND_COLORS["sky_blue"])
        super_draw = ImageDraw.Draw(super_img)
        
        # Draw card at supersampled resolution
        super_margin = margin * supersample_factor
        super_card_y = card_y * supersample_factor
        super_card_height = card_height * supersample_factor
        
        super_card_coords = [super_margin, super_card_y,
                           supersize[0] - super_margin, super_card_y + super_card_height]
        
        # Draw white card with rounded corners
        super_draw.rounded_rectangle(super_card_coords, radius=40*supersample_factor,
                                    fill=BRAND_COLORS["white"])
        
        # Draw thick animated border
        border_width = 15 * supersample_factor
        border_color = BRAND_COLORS["dark_navy"][:3] + (220,)
        
        # Animate border thickness slightly
        animated_border_width = int(border_width * (0.9 + 0.1 * math.sin(time_offset * 3)))
        
        # Draw border (rounded rectangle with larger radius for border)
        border_coords = [super_card_coords[0] - animated_border_width//2,
                        super_card_coords[1] - animated_border_width//2,
                        super_card_coords[2] + animated_border_width//2,
                        super_card_coords[3] + animated_border_width//2]
        
        super_draw.rounded_rectangle(border_coords, radius=45*supersample_factor,
                                    outline=border_color, width=animated_border_width)
        
        # Downscale with Lanczos
        img = super_img.resize((width, height), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        # Add decorative elements inside card
        # Horizontal rule lines
        for i in range(3):
            line_y = card_y + 100 + i * 150
            line_opacity = int(100 + 100 * math.sin(time_offset * 2 + i))
            line_color = BRAND_COLORS["medium_grey"][:3] + (line_opacity,)
            
            draw.line([(margin + 50, line_y), (width - margin - 50, line_y)],
                     fill=line_color, width=2)
        
        # Floating dots in corners
        dot_positions = [
            (margin + 40, card_y + 40),
            (width - margin - 40, card_y + 40),
            (margin + 40, card_y + card_height - 40),
            (width - margin - 40, card_y + card_height - 40)
        ]
        
        for i, (dx, dy) in enumerate(dot_positions):
            pulse = 1.0 + math.sin(time_offset * 4 + i) * 0.3
            dot_size = 8 * pulse
            
            dot_color = BRAND_COLORS["primary_green"][:3] + (200,)
            draw.ellipse([dx-dot_size, dy-dot_size, dx+dot_size, dy+dot_size],
                        fill=dot_color)
        
        return img
    
    @staticmethod
    def create_aura_orbs(width: int, height: int, time_offset: float) -> Image.Image:
        """Aura orbs with vectorized compositing and Gaussian blur for seamless gradients"""
        # Create dark navy base canvas
        img = Image.new("RGBA", (width, height), BRAND_COLORS["dark_navy"])
        draw = ImageDraw.Draw(img)
        
        # Create multiple aura orbs
        num_orbs = 5
        orb_colors = [
            BRAND_COLORS["primary_green"],
            BRAND_COLORS["accent_blue"],
            BRAND_COLORS["brand_yellow"],
            (200, 100, 255, 200),  # Purple
            (255, 150, 100, 200)   # Orange
        ]
        
        for i in range(num_orbs):
            # Orb position with orbital movement
            orbit_radius = 300 + i * 50
            orbit_speed = 0.3 + i * 0.1
            
            orb_x = width // 2 + math.cos(time_offset * orbit_speed + i) * orbit_radius
            orb_y = height // 2 + math.sin(time_offset * orbit_speed * 1.3 + i) * orbit_radius
            
            # Orb size and opacity
            orb_size = 150 + 50 * math.sin(time_offset * 2 + i)
            orb_opacity = int(100 + 100 * abs(math.sin(time_offset * 1.5 + i)))
            
            # Get orb color
            base_color = orb_colors[i % len(orb_colors)]
            orb_color = base_color[:3] + (orb_opacity,)
            
            # Draw orb with gradient effect using multiple layers
            layers = 10
            for layer in range(layers, 0, -1):
                layer_size = orb_size * (layer / layers)
                layer_opacity = int(orb_opacity * (layer / layers) * 0.5)
                layer_color = orb_color[:3] + (layer_opacity,)
                
                draw.ellipse([orb_x - layer_size, orb_y - layer_size,
                            orb_x + layer_size, orb_y + layer_size],
                           fill=layer_color)
        
        # Apply high-radius Gaussian blur for seamless liquid gradient
        img = img.filter(ImageFilter.GaussianBlur(radius=15))
        
        # Add subtle grid overlay for structure
        grid_spacing = 80
        grid_opacity = 20
        
        for x in range(0, width, grid_spacing):
            draw.line([(x, 0), (x, height)],
                     fill=(255, 255, 255, grid_opacity), width=1)
        
        for y in range(0, height, grid_spacing):
            draw.line([(0, y), (width, y)],
                     fill=(255, 255, 255, grid_opacity), width=1)
        
        return img

# ============================================================================
# SUPERSAMPLED TEXT RENDERER
# ============================================================================
class SupersampledTextRenderer:
    """Render text with supersampling for retina-level quality"""
    
    @staticmethod
    def render_text(text: str, font_size: int, width: int, height: int, 
                   position: Tuple[float, float] = (0.5, 0.5),
                   color: Tuple[int, int, int, int] = None) -> Image.Image:
        """Render text with 2x supersampling"""
        if color is None:
            color = BRAND_COLORS["white"]
        
        # Calculate supersampled dimensions
        supersample_factor = 2
        super_width = width * supersample_factor
        super_height = height * supersample_factor
        
        # Create supersampled canvas
        super_img = Image.new("RGBA", (super_width, super_height), (0, 0, 0, 0))
        super_draw = ImageDraw.Draw(super_img)
        
        # Load font at supersampled size
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size * supersample_factor)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text_x = position[0] * super_width
        text_y = position[1] * super_height
        
        # Draw text with shadow for depth
        shadow_offset = 4 * supersample_factor
        shadow_color = (0, 0, 0, color[3] // 2)
        
        # Multiple shadow layers for better depth
        for offset in [(shadow_offset, 0), (0, shadow_offset), 
                      (-shadow_offset, 0), (0, -shadow_offset)]:
            super_draw.text((text_x + offset[0], text_y + offset[1]),
                           text, font=font, fill=shadow_color, anchor="mm")
        
        # Main text
        super_draw.text((text_x, text_y), text, font=font, fill=color, anchor="mm")
        
        # Downscale with Lanczos filter for crisp edges
        img = super_img.resize((width, height), Image.Resampling.LANCZOS)
        
        return img

# ============================================================================
# MAIN ANIMATION GENERATOR
# ============================================================================
class VectorizedAnimationGenerator:
    """Generate high-quality vectorized animations"""
    
    def __init__(self):
        self.bg_generator = VectorizedBackgrounds()
        self.text_renderer = SupersampledTextRenderer()
        self.config = AnimationConfig()
    
    def create_frame(self, 
                    quote_text: str,
                    author: str,
                    size: Tuple[int, int],
                    bg_style: str,
                    frame_progress: float,
                    time_offset: float) -> Image.Image:
        """Create a single supersampled frame"""
        width, height = size
        
        # Generate background based on style
        if bg_style == "🪶 Flocking Birds":
            bg = self.bg_generator.create_flocking_birds(width, height, time_offset)
        elif bg_style == "📐 Geometric Pulse":
            bg = self.bg_generator.create_geometric_pulse(width, height, time_offset)
        elif bg_style == "🌿 Organic Growth":
            bg = self.bg_generator.create_organic_growth(width, height, time_offset)
        elif bg_style == "⚪ Circle Card":
            bg = self.bg_generator.create_circle_card(width, height, time_offset)
        elif bg_style == "🟦 Rectangle Card":
            bg = self.bg_generator.create_rectangle_card(width, height, time_offset)
        elif bg_style == "✨ Aura Orbs":
            bg = self.bg_generator.create_aura_orbs(width, height, time_offset)
        else:
            # Default to navy background
            bg = Image.new("RGBA", (width, height), BRAND_COLORS["navy_blue"])
        
        # Convert to RGB for video encoding
        bg_rgb = bg.convert("RGB")
        img = bg_rgb.copy()
        
        # Only render text after 0.2 seconds (allows background to establish)
        if frame_progress > 0.2:
            # Calculate text opacity based on progress
            text_opacity = min(1.0, (frame_progress - 0.2) / 0.3)
            
            # Render quote text with supersampling
            quote_color = BRAND_COLORS["white"][:3] + (int(255 * text_opacity),)
            quote_img = self.text_renderer.render_text(
                quote_text, 
                font_size=60,
                width=width,
                height=height,
                position=(0.5, 0.5),
                color=quote_color
            )
            
            # Composite quote onto background
            img = Image.alpha_composite(img.convert("RGBA"), quote_img).convert("RGB")
            
            # Render author after quote is mostly visible
            if frame_progress > 0.7:
                author_opacity = min(1.0, (frame_progress - 0.7) / 0.2)
                author_color = BRAND_COLORS["light_grey"][:3] + (int(255 * author_opacity),)
                
                author_text = f"— {author}"
                author_img = self.text_renderer.render_text(
                    author_text,
                    font_size=40,
                    width=width,
                    height=height,
                    position=(0.7, 0.8),  # Bottom right
                    color=author_color
                )
                
                img = Image.alpha_composite(img.convert("RGBA"), author_img).convert("RGB")
            
            # Render brand watermark (always visible but subtle)
            brand_opacity = 180
            brand_img = self.text_renderer.render_text(
                "@stillmind",
                font_size=30,
                width=width,
                height=height,
                position=(0.1, 0.9),  # Bottom left
                color=BRAND_COLORS["medium_grey"][:3] + (brand_opacity,)
            )
            
            img = Image.alpha_composite(img.convert("RGBA"), brand_img).convert("RGB")
        
        return img
    
    def create_mp4_video(self,
                        quote_text: str,
                        author: str,
                        size: Tuple[int, int],
                        bg_style: str) -> bytes:
        """Create MP4 video with high-quality encoding"""
        width, height = size
        total_frames = self.config.total_frames
        fps = self.config.fps
        
        # Generate all frames
        frames = []
        for frame_num in range(total_frames):
            time_offset = frame_num / fps
            frame_progress = min(1.0, frame_num / total_frames)
            
            frame = self.create_frame(
                quote_text, author, size, bg_style, frame_progress, time_offset
            )
            
            # Convert to numpy array for video encoding
            frame_np = np.array(frame)
            frames.append(frame_np)
        
        # Encode to MP4 with high-quality settings
        buffer = io.BytesIO()
        iio.imwrite(
            buffer,
            frames,
            format='mp4',
            fps=fps,
            codec='libx264',
            quality=9,  # Higher quality (0-10 scale)
            pixelformat=self.config.pixel_format,
            bitrate=self.config.bitrate
        )
        
        return buffer.getvalue()

# ============================================================================
# QUOTE MANAGER
# ============================================================================
class QuoteManager:
    """Fetch quotes from API with caching"""
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def fetch_quote(category="motivation"):
        """Fetch quote from Quotable API"""
        try:
            if category == "random":
                url = "https://api.quotable.io/random"
            else:
                url = f"https://api.quotable.io/quotes/random?tags={category}&maxLength=120"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    data = data[0]
                
                return {
                    "text": data["content"],
                    "author": data["author"],
                    "category": category,
                    "source": "Quotable API"
                }
        except:
            pass
        
        # Fallback quotes
        fallback_quotes = [
            {"text": "TRUST YOURSELF", "author": "Still Mind"},
            {"text": "TAKE CARE TO WORK HARD", "author": "Still Mind"},
            {"text": "DON'T GIVE UP", "author": "Still Mind"},
        ]
        
        return random.choice(fallback_quotes)

# ============================================================================
# GROQ SOCIAL MEDIA MANAGER
# ============================================================================
class SocialMediaManager:
    """Generate social media content using Groq"""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
    
    def generate_content(self, quote: str, author: str, bg_style: str) -> Dict:
        """Generate social media post content"""
        try:
            prompt = f"""
            Create a social media post for this quote with the visual style: {bg_style}
            
            QUOTE: "{quote}"
            AUTHOR: {author}
            VISUAL STYLE: {bg_style}
            BRAND: @stillmind (mindfulness, wisdom, personal growth)
            
            Generate a JSON with:
            1. caption: Engaging 2-3 line caption with relevant emojis
            2. hashtags: 5-7 relevant hashtags
            3. posting_time: Best time to post (consider global audience)
            4. engagement_hook: One question to ask in comments
            5. visual_description: Describe the animated visual for screen readers
            
            Make it authentic, inspiring, and platform-optimized.
            """
            
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a social media expert for mindfulness and personal growth content."
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
            content["generated_at"] = datetime.now().isoformat()
            
            return content
            
        except Exception as e:
            return self._fallback_content(quote, author, bg_style)
    
    def _fallback_content(self, quote: str, author: str, bg_style: str) -> Dict:
        """Fallback content"""
        return {
            "caption": f'"{quote}"\n\n— {author}\n\n✨ @stillmind\n💭 What does this mean to you?',
            "hashtags": ["#stillmind", "#wisdom", "#quote", "#mindfulness", "#growth"],
            "posting_time": "7-9 PM GMT",
            "engagement_hook": "Which part resonates most with you?",
            "visual_description": f"Animated {bg_style} background with the quote appearing elegantly",
            "is_fallback": True
        }

# ============================================================================
# STREAMLIT UI
# ============================================================================
def main():
    # Custom CSS
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
    .visual-energy-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .energy-high { background: rgba(76, 175, 80, 0.2); color: #4CAF50; border: 1px solid #4CAF50; }
    .energy-medium { background: rgba(25, 118, 210, 0.2); color: #1976D2; border: 1px solid #1976D2; }
    .energy-low { background: rgba(158, 158, 158, 0.2); color: #9E9E9E; border: 1px solid #9E9E9E; }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'current_video' not in st.session_state:
        st.session_state.current_video = None
    if 'social_content' not in st.session_state:
        st.session_state.social_content = None
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: #4CAF50; margin-bottom: 0.5rem;">🧠 Still Mind | Vectorized Animations</h1>
        <p style="color: #EEEEEE; opacity: 0.9; margin-bottom: 0.5rem;">High-quality animated quotes with supersampled rendering</p>
        <p style="color: #9E9E9E; font-size: 0.9rem; margin: 0;">8-second MP4 • 15 FPS • libx264 • yuv420p • 8000k bitrate</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ⚙️ Configuration")
        
        # Quote source
        quote_source = st.radio("Quote Source", ["API", "Custom"], horizontal=True)
        
        if quote_source == "API":
            category = st.selectbox(
                "Category",
                ["motivation", "wisdom", "mindfulness", "success", "random"],
                index=0
            )
        else:
            custom_quote = st.text_area("Your Quote", height=100,
                                       placeholder="Enter your quote...")
            custom_author = st.text_input("Author", value="Still Mind")
        
        # Visual style selection
        st.markdown("### 🎨 Visual Energy")
        
        visual_styles = {
            "🪶 Flocking Birds": {
                "description": "V-shaped silhouettes gliding across the frame",
                "energy": "high",
                "color": "energy-high"
            },
            "📐 Geometric Pulse": {
                "description": "Lissajous curves & expanding grids at 60bpm rhythm",
                "energy": "medium",
                "color": "energy-medium"
            },
            "🌿 Organic Growth": {
                "description": "Procedural vine growth with popping leaves",
                "energy": "low",
                "color": "energy-low"
            },
            "⚪ Circle Card": {
                "description": "Brand yellow with pulsing central circle",
                "energy": "medium",
                "color": "energy-medium"
            },
            "🟦 Rectangle Card": {
                "description": "Sky blue with floating rectangular card",
                "energy": "low",
                "color": "energy-low"
            },
            "✨ Aura Orbs": {
                "description": "Vectorized aura orbs with Gaussian blur gradients",
                "energy": "high",
                "color": "energy-high"
            }
        }
        
        selected_style = st.selectbox("Visual Style", list(visual_styles.keys()), index=0)
        
        # Show style description and energy
        style_info = visual_styles[selected_style]
        st.markdown(f'<div class="visual-energy-badge {style_info["color"]}">{style_info["energy"].title()} Energy</div>', 
                   unsafe_allow_html=True)
        st.caption(style_info["description"])
        
        # Size format
        size_option = st.selectbox("Size Format", list(SIZES.keys()), index=0)
        
        # Generate button
        if st.button("✨ GENERATE VECTORIZED ANIMATION", type="primary"):
            with st.spinner("Rendering supersampled frames..."):
                # Get quote
                if quote_source == "API":
                    quote_data = QuoteManager.fetch_quote(category)
                    quote_text = quote_data["text"]
                    author = quote_data["author"]
                else:
                    quote_text = custom_quote.strip()
                    author = custom_author.strip() or "Still Mind"
                
                if not quote_text:
                    st.error("Please enter a quote")
                    return
                
                # Generate video
                generator = VectorizedAnimationGenerator()
                video_data = generator.create_mp4_video(
                    quote_text,
                    author,
                    SIZES[size_option],
                    selected_style
                )
                
                # Store in session state
                st.session_state.current_video = video_data
                st.session_state.current_quote = {
                    "text": quote_text,
                    "author": author,
                    "style": selected_style
                }
                
                # Generate social media content if API key available
                try:
                    groq_key = st.secrets["groq_key"]
                    sm_manager = SocialMediaManager(groq_key)
                    st.session_state.social_content = sm_manager.generate_content(
                        quote_text, author, selected_style
                    )
                except:
                    st.session_state.social_content = None
                
                st.success("✅ Vectorized animation complete!")
    
    with col2:
        # Preview section
        if st.session_state.current_video:
            st.markdown("### 🎬 Preview")
            
            # Video player
            st.video(st.session_state.current_video, format="video/mp4", start_time=0)
            
            # Technical specs
            col_spec1, col_spec2, col_spec3, col_spec4 = st.columns(4)
            with col_spec1:
                st.metric("Duration", "8s")
            with col_spec2:
                st.metric("FPS", "15")
            with col_spec3:
                st.metric("Codec", "H.264")
            with col_spec4:
                st.metric("Quality", "High")
            
            # Download buttons
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 DOWNLOAD MP4 (High Quality)",
                data=st.session_state.current_video,
                file_name=f"stillmind_{selected_style.replace(' ', '_').lower()}_{timestamp}.mp4",
                mime="video/mp4",
                use_container_width=True
            )
            
            # Social media section
            st.markdown("---")
            st.markdown("### 📱 Social Media Content")
            
            if st.session_state.social_content:
                content = st.session_state.social_content
                
                # Caption
                st.text_area("📝 Caption", content.get("caption", ""), height=150)
                
                # Hashtags
                hashtags = content.get("hashtags", [])
                hashtag_str = ' '.join(f"#{tag}" for tag in hashtags)
                st.code(hashtag_str)
                
                # Additional info
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**⏰ Best Time:** {content.get('posting_time', 'N/A')}")
                with col_info2:
                    st.write(f"**💬 Engagement:** {content.get('engagement_hook', 'N/A')}")
                
                # Visual description for accessibility
                st.write(f"**👁️ Visual Description:** {content.get('visual_description', 'N/A')}")
            else:
                st.info("🔑 Add `groq_key` to Streamlit secrets for AI-powered social content")
                
                # Show basic template
                st.text_area("📝 Caption Template", 
                           f'"{st.session_state.current_quote["text"]}"\n\n— {st.session_state.current_quote["author"]}\n\n✨ @stillmind\n💭 What resonates with you?',
                           height=150)
                st.code("#stillmind #wisdom #quote #mindfulness #growth")
            
            # Quick actions
            st.markdown("---")
            col_action1, col_action2 = st.columns(2)
            with col_action1:
                if st.button("🔄 New Animation", use_container_width=True):
                    st.session_state.current_video = None
                    st.rerun()
            with col_action2:
                if st.button("🎲 Random Style", use_container_width=True):
                    st.rerun()
        
        else:
            # Empty state
            st.markdown("""
            <div style="text-align: center; padding: 4rem; color: #9E9E9E; background: rgba(13, 27, 42, 0.5); border-radius: 16px;">
                <h3>👆 Configure & Generate</h3>
                <p>Select visual energy style and generate your first vectorized animation.</p>
                <p style="font-size: 0.9rem; opacity: 0.7;">Each style uses different mathematical principles for animation</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #616161; padding: 2rem 0; font-size: 0.9rem;">
        <p>🧠 Still Mind • Vectorized Animations • Supersampled Rendering • High-Quality MP4 Export</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">libx264 • yuv420p • 8000k bitrate • Lanczos downscaling • Gaussian blur gradients</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == "__main__":
    main()