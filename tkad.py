import streamlit as st
import json
import requests
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import tempfile
import os
from moviepy.editor import ImageClip, concatenate_videoclips
import cv2
from functools import lru_cache

# Page configuration
st.set_page_config(
    page_title="Polotno Studio Renderer",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for better UI
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #ff4b4b;
    }
    .preview-container {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hex_to_rgba(color_str, alpha=255):
    """Convert hex or rgba string to RGBA tuple."""
    if not color_str:
        return (0, 0, 0, alpha)
    
    color_str = str(color_str).strip()
    
    # Handle rgba(r,g,b,a) format
    if color_str.startswith('rgba'):
        import re
        match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_str)
        if match:
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            a = int(float(match.group(4)) * 255) if match.group(4) else alpha
            return (r, g, b, a)
    
    # Handle hex format
    color_str = color_str.lstrip('#')
    if len(color_str) == 3:
        color_str = ''.join([c*2 for c in color_str])
    if len(color_str) >= 6:
        r = int(color_str[0:2], 16)
        g = int(color_str[2:4], 16)
        b = int(color_str[4:6], 16)
        a = int(color_str[6:8], 16) if len(color_str) >= 8 else alpha
        return (r, g, b, a)
    
    return (0, 0, 0, alpha)


@st.cache_data(ttl=3600, show_spinner=False)
def download_image(url):
    """
    Cached image downloader to prevent repeated requests.
    Returns PIL Image in RGBA mode or None if failed.
    """
    if not url:
        return None
    
    try:
        # Handle data URLs
        if url.startswith('data:image'):
            import base64
            header, encoded = url.split(',', 1)
            data = base64.b64decode(encoded)
            return Image.open(BytesIO(data)).convert('RGBA')
        
        # Handle HTTP URLs
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert('RGBA')
        
    except Exception as e:
        st.warning(f"⚠️ Failed to load image: {url[:50]}... ({str(e)})")
        return None


def get_video_frame(video_path, timestamp_seconds, target_w, target_h):
    """
    Extract a specific frame from a video file at given timestamp.
    Supports local paths and URLs.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
            
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_no = int(timestamp_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame).convert("RGBA")
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
    except Exception as e:
        st.warning(f"⚠️ Video frame extraction failed: {e}")
    
    return None


def get_font(font_size, font_family="Arial", font_weight="normal"):
    """
    Load font with comprehensive fallback chain.
    """
    # Scale font size for different systems
    scaled_size = max(8, int(font_size))
    
    font_variants = []
    
    # Build font search list based on family and weight
    if font_weight in ('bold', '700', '800', '900'):
        font_variants.extend([
            f"{font_family}-Bold.ttf",
            f"{font_family}-Bold.otf",
            f"{font_family}Bold.ttf",
            f"{font_family}-BoldMT.ttf",
            "arialbd.ttf",
            "Arial Bold.ttf",
        ])
    else:
        font_variants.extend([
            f"{font_family}.ttf",
            f"{font_family}.otf",
            f"{font_family}-Regular.ttf",
            f"{font_family}-Regular.otf",
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
            "LiberationSans-Regular.ttf",
        ])
    
    # System font paths
    font_paths = [
        "",  # Current directory
        "/usr/share/fonts/truetype/",
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/truetype/liberation/",
        "/usr/share/fonts/truetype/msttcorefonts/",
        "/System/Library/Fonts/",
        "/Library/Fonts/",
        "C:/Windows/Fonts/",
        os.path.expanduser("~/.fonts/"),
    ]
    
    # Try to load font
    for variant in font_variants:
        for path in font_paths:
            try:
                font_path = os.path.join(path, variant)
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, scaled_size)
            except:
                continue
    
    # Final fallback
    try:
        return ImageFont.truetype("arial.ttf", scaled_size)
    except:
        return ImageFont.load_default()


def wrap_text(content, font, max_width):
    """
    Wrap text to fit within max_width pixels.
    Returns list of lines.
    """
    if not content:
        return [""]
    
    words = content.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
        except:
            line_width = len(test_line) * scaled_size * 0.6  # Fallback estimate
        
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [content]


# =============================================================================
# RENDERING FUNCTIONS
# =============================================================================

def render_layer(img, layer, canvas_w, canvas_h, progress=1.0, animation_style="none"):
    """
    Render a single Polotno layer onto an image.
    
    Args:
        img: PIL Image to render onto
        layer: Polotno layer dict
        canvas_w, canvas_h: Canvas dimensions
        progress: Animation progress (0.0 to 1.0)
        animation_style: Type of animation to apply
    """
    draw = ImageDraw.Draw(img)
    
    # Extract properties - Polotno uses absolute pixel coordinates
    layer_type = layer.get('type', 'text')
    x = int(layer.get('x', 0))
    y = int(layer.get('y', 0))
    w = int(layer.get('width', 100))
    h = int(layer.get('height', 100))
    opacity = layer.get('opacity', 1.0) * progress
    angle = layer.get('rotation', 0)
    
    # Animation transforms
    if animation_style == "fade":
        opacity = layer.get('opacity', 1.0) * progress
    elif animation_style == "slide_up":
        y_offset = int((1 - progress) * 50)
        y -= y_offset
    elif animation_style == "zoom":
        scale = 0.5 + (0.5 * progress)
        w = int(w * scale)
        h = int(h * scale)
        x = int(x + (layer.get('width', 100) - w) / 2)
    elif animation_style == "typewriter" and layer_type == "text":
        content = layer.get('text', '')
        visible_chars = int(len(content) * progress)
        layer = {**layer, 'text': content[:visible_chars]}
    
    # Render based on type
    if layer_type in ('text', 'badge'):
        render_text_layer(img, layer, x, y, w, h, opacity, angle)
    
    elif layer_type == 'image':
        render_image_layer(img, layer, x, y, w, h, opacity, angle)
    
    elif layer_type == 'video':
        render_video_layer(img, layer, x, y, w, h, opacity, progress)
    
    elif layer_type == 'figure' or layer_type == 'rect':
        render_shape_layer(img, layer, x, y, w, h, opacity, angle)


def render_text_layer(img, layer, x, y, w, h, opacity, angle):
    """Render text layer with wrapping and styling."""
    content = layer.get('text', '')
    if not content:
        return
    
    font_size = int(layer.get('fontSize', 30))
    font_family = layer.get('fontFamily', 'Arial')
    font_weight = layer.get('fontWeight', 'normal')
    fill = layer.get('fill', '#000000')
    align = layer.get('align', 'left')
    line_height = layer.get('lineHeight', 1.2)
    
    # Load font
    font = get_font(font_size, font_family, font_weight)
    
    # Wrap text
    lines = wrap_text(content, font, w)
    
    # Calculate total height
    total_height = len(lines) * font_size * line_height
    
    # Create text layer for rotation/opacity support
    text_layer = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    
    # Color with opacity
    rgba = hex_to_rgba(fill, int(255 * opacity))
    
    # Draw each line
    start_y = (h * 2 - total_height) / 2 if align == 'center' else 0
    
    for i, line in enumerate(lines):
        # Calculate x offset for alignment
        try:
            bbox = font.getbbox(line)
            line_w = bbox[2] - bbox[0]
        except:
            line_w = len(line) * font_size * 0.6
        
        if align == 'center':
            line_x = (w * 2 - line_w) / 2
        elif align == 'right':
            line_x = w * 2 - line_w
        else:
            line_x = 0
        
        line_y = start_y + (i * font_size * line_height)
        text_draw.text((line_x, line_y), line, font=font, fill=rgba)
    
    # Apply rotation if needed
    if angle != 0:
        text_layer = text_layer.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
    
    # Composite onto main image
    paste_x = x - w
    paste_y = y - h
    img.alpha_composite(text_layer, (paste_x, paste_y))


def render_image_layer(img, layer, x, y, w, h, opacity, angle):
    """Render image layer with caching support."""
    src = layer.get('src', '')
    if not src:
        return
    
    # Use cached downloader
    layer_img = download_image(src)
    if not layer_img:
        return
    
    # Resize to target dimensions
    layer_img = layer_img.resize((w, h), Image.Resampling.LANCZOS)
    
    # Apply opacity
    if opacity < 1.0:
        alpha = layer_img.split()[3].point(lambda p: int(p * opacity))
        layer_img.putalpha(alpha)
    
    # Apply rotation
    if angle != 0:
        layer_img = layer_img.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
    
    # Paste onto main image
    img.paste(layer_img, (x, y), layer_img)


def render_video_layer(img, layer, x, y, w, h, opacity, progress):
    """Render video layer by extracting frame at progress time."""
    src = layer.get('src', '')
    if not src:
        return
    
    # Calculate timestamp based on progress
    # Assuming we want to loop or show portion of video
    video_duration = layer.get('duration', 5)  # Default 5s if not specified
    timestamp = (progress * video_duration) % video_duration
    
    frame = get_video_frame(src, timestamp, w, h)
    if frame:
        if opacity < 1.0:
            alpha = frame.split()[3].point(lambda p: int(p * opacity))
            frame.putalpha(alpha)
        img.paste(frame, (x, y), frame)


def render_shape_layer(img, layer, x, y, w, h, opacity, angle):
    """Render shape/rectangle layers."""
    draw = ImageDraw.Draw(img)
    fill = layer.get('fill', '#000000')
    stroke = layer.get('stroke', None)
    stroke_width = layer.get('strokeWidth', 0)
    corner_radius = layer.get('cornerRadius', 0)
    
    rgba = hex_to_rgba(fill, int(255 * opacity))
    
    # Draw rounded rectangle if cornerRadius exists
    if corner_radius > 0:
        draw.rounded_rectangle(
            [x, y, x + w, y + h],
            radius=corner_radius,
            fill=rgba,
            outline=hex_to_rgba(stroke) if stroke else None,
            width=stroke_width
        )
    else:
        draw.rectangle(
            [x, y, x + w, y + h],
            fill=rgba,
            outline=hex_to_rgba(stroke) if stroke else None,
            width=stroke_width
        )


def render_frame(json_data, progress=1.0, scale=1.0, animation_style="none"):
    """
    Render a complete frame at given animation progress.
    
    Args:
        json_data: Polotno JSON
        progress: 0.0 to 1.0 animation progress
        scale: Output scale factor
        animation_style: Animation type
    
    Returns:
        PIL Image
    """
    # Get dimensions
    orig_w = int(json_data.get('width', 1080))
    orig_h = int(json_data.get('height', 1080))
    
    w = int(orig_w * scale)
    h = int(orig_h * scale)
    
    # Background
    bg_color = json_data.get('background', '#ffffff')
    img = Image.new('RGBA', (w, h), hex_to_rgba(bg_color))
    
    # Scale layers proportionally
    scale_x = w / orig_w
    scale_y = h / orig_h
    
    layers = json_data.get('layers', [])
    
    # Sort by z-index if present
    layers = sorted(layers, key=lambda l: l.get('z', 0))
    
    for layer in layers:
        # Scale coordinates
        scaled_layer = layer.copy()
        scaled_layer['x'] = int(layer.get('x', 0) * scale_x)
        scaled_layer['y'] = int(layer.get('y', 0) * scale_y)
        scaled_layer['width'] = int(layer.get('width', 100) * scale_x)
        scaled_layer['height'] = int(layer.get('height', 100) * scale_y)
        scaled_layer['fontSize'] = int(layer.get('fontSize', 30) * scale_x)
        
        render_layer(img, scaled_layer, w, h, progress, animation_style)
    
    return img


# =============================================================================
# VIDEO GENERATION
# =============================================================================

def create_video(frames, fps=30, output_path=None):
    """
    Create MP4 video from PIL frames.
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.mp4')
    
    # Convert PIL images to numpy arrays
    np_frames = [np.array(frame.convert('RGB')) for frame in frames]
    
    # Create video clip
    clip = ImageClip(np_frames[0], duration=1/fps)
    clips = [ImageClip(frame, duration=1/fps) for frame in np_frames]
    
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(
        output_path,
        fps=fps,
        codec='libx264',
        audio=False,
        preset='medium',
        threads=4
    )
    video.close()
    
    return output_path


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_sidebar():
    """Render sidebar controls."""
    with st.sidebar:
        st.title("⚙️ Export Settings")
        
        # Output format
        output_format = st.selectbox(
            "Output Format",
            ["Image (PNG)", "Video (MP4)", "Both"],
            index=2
        )
        
        # Scale settings
        st.subheader("Resolution")
        scale = st.slider(
            "Output Scale",
            min_value=0.25,
            max_value=2.0,
            value=1.0,
            step=0.25,
            help="Scale the output resolution. 0.5 = half size (faster), 1.0 = original, 2.0 = 2x (slower)"
        )
        
        settings = {'format': output_format, 'scale': scale}
        
        # Video settings
        if "Video" in output_format or output_format == "Both":
            st.subheader("Video Settings")
            settings['duration'] = st.slider("Duration (s)", 1, 10, 3)
            settings['fps'] = st.selectbox("FPS", [24, 30, 60], index=1)
            settings['animation'] = st.selectbox(
                "Animation Style",
                ["none", "fade", "slide_up", "zoom", "typewriter", "stagger"],
                index=1,
                help="none: Static, fade: Fade in, slide_up: Slide from bottom, zoom: Scale up, typewriter: Text reveal, stagger: Layered entrance"
            )
        
        # Image settings
        if "Image" in output_format or output_format == "Both":
            st.subheader("Image Settings")
            settings['quality'] = st.slider("PNG Quality", 1, 100, 95)
        
        return settings


def render_input_section():
    """Handle JSON input methods."""
    st.header("📥 Design Input")
    
    tab1, tab2 = st.tabs(["📋 Paste JSON", "📁 Upload File"])
    
    json_data = None
    
    with tab1:
        json_text = st.text_area(
            "Paste Polotno JSON:",
            height=300,
            placeholder='{"width": 1080, "height": 1080, "layers": [...]}'
        )
        if json_text:
            try:
                json_data = json.loads(json_text)
                st.success(f"✅ Loaded: {json_data.get('name', 'Untitled')}")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
    
    with tab2:
        uploaded = st.file_uploader("Upload .json file", type=['json'])
        if uploaded:
            try:
                json_data = json.load(uploaded)
                st.success(f"✅ Loaded: {json_data.get('name', 'Untitled')}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    return json_data


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    st.title("🎨 Polotno Studio Renderer")
    st.caption("Convert Polotno JSON designs to high-quality images and videos")
    
    # Sidebar settings
    settings = render_sidebar()
    
    # Input section
    json_data = render_input_section()
    
    if not json_data:
        st.info("👆 Upload or paste a Polotno JSON to get started")
        return
    
    # Validate JSON structure
    if 'layers' not in json_data:
        st.error("❌ Invalid Polotno JSON: missing 'layers' array")
        return
    
    # Show layer summary
    with st.expander(f"📊 Design Info ({len(json_data.get('layers', []))} layers)"):
        cols = st.columns(3)
        cols[0].metric("Width", json_data.get('width', 1080))
        cols[1].metric("Height", json_data.get('height', 1080))
        cols[2].metric("Layers", len(json_data.get('layers', [])))
        
        st.json({k: v for k, v in json_data.items() if k != 'layers'})
        
        st.write("**Layers:**")
        for i, layer in enumerate(json_data.get('layers', [])):
            st.text(f"{i+1}. {layer.get('type', 'unknown')} - {layer.get('id', 'no-id')}")
    
    # Live preview (fast, low-res)
    st.header("🖼️ Live Preview")
    
    preview_col, controls_col = st.columns([2, 1])
    
    with preview_col:
        # Generate quick preview at 0.5x for speed
        try:
            preview_img = render_frame(json_data, scale=0.5)
            st.image(preview_img, use_column_width=True, caption="Preview (50% scale)")
        except Exception as e:
            st.error(f"Preview error: {e}")
    
    with controls_col:
        st.subheader("Quick Actions")
        
        if st.button("🔄 Refresh Preview", use_container_width=True):
            st.rerun()
        
        st.divider()
        st.markdown("""
        **Tips:**
        - Use 0.5x scale for faster preview
        - Images are cached for 1 hour
        - Video generation may take time
        """)
    
    # Generation section
    st.header("🚀 Generate Export")
    
    if st.button("⚡ Start Generation", type="primary", use_container_width=True):
        
        fmt = settings['format']
        scale = settings['scale']
        
        # Calculate output dimensions
        orig_w = json_data.get('width', 1080)
        orig_h = json_data.get('height', 1080)
        out_w = int(orig_w * scale)
        out_h = int(orig_h * scale)
        
        st.info(f"Output size: {out_w}x{out_h}")
        
        # Create columns for outputs
        if fmt == "Both":
            img_col, vid_col = st.columns(2)
        else:
            img_col = vid_col = st.container()
        
        # Generate Image
        if "Image" in fmt or fmt == "Both":
            with img_col:
                st.subheader("🖼️ Image Export")
                
                with st.spinner("Rendering image..."):
                    try:
                        final_img = render_frame(json_data, scale=scale)
                        
                        # Convert to RGB for display
                        display_img = final_img.convert('RGB')
                        st.image(display_img, use_column_width=True)
                        
                        # Prepare download
                        buf = BytesIO()
                        display_img.save(
                            buf, 
                            format='PNG', 
                            quality=settings.get('quality', 95),
                            optimize=True
                        )
                        buf.seek(0)
                        
                        st.download_button(
                            label=f"⬇️ Download PNG ({out_w}x{out_h})",
                            data=buf,
                            file_name=f"{json_data.get('name', 'design')}_{out_w}x{out_h}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"Image generation failed: {e}")
        
        # Generate Video
        if "Video" in fmt or fmt == "Both":
            with vid_col:
                st.subheader("🎬 Video Export")
                
                duration = settings.get('duration', 3)
                fps = settings.get('fps', 30)
                animation = settings.get('animation', 'fade')
                total_frames = int(duration * fps)
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                frames = []
                
                try:
                    for i in range(total_frames):
                        # Update progress
                        pct = (i + 1) / total_frames
                        progress_bar.progress(pct, text=f"Frame {i+1}/{total_frames}")
                        status_text.text(f"Rendering frame {i+1}/{total_frames} ({int(pct*100)}%)")
                        
                        # Calculate animation progress
                        if animation == "stagger":
                            # Each layer animates with delay
                            frame = render_frame(json_data, progress=pct, scale=scale, animation_style="fade")
                        else:
                            frame = render_frame(json_data, progress=pct, scale=scale, animation_style=animation)
                        
                        frames.append(frame)
                    
                    status_text.text("💾 Compiling video...")
                    
                    # Create video
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                        video_path = create_video(frames, fps, tmp.name)
                        
                        with open(video_path, 'rb') as f:
                            video_bytes = f.read()
                        
                        st.video(video_bytes)
                        
                        st.download_button(
                            label=f"⬇️ Download MP4 ({duration}s @ {fps}fps)",
                            data=video_bytes,
                            file_name=f"{json_data.get('name', 'design')}_{out_w}x{out_h}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                        
                        # Cleanup
                        os.unlink(video_path)
                    
                    progress_bar.empty()
                    status_text.success("✅ Complete!")
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.error(f"Video generation failed: {e}")
                    raise e


if __name__ == "__main__":
    main()
