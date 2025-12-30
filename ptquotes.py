import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, io, json, requests
import numpy as np
import imageio.v3 as iio
from groq import Groq

# ============================================
# 1. BRAND IDENTITY (ParenTeen Kenya Official)
# ============================================
LOGO_URL = "https://parenteenkenya.co.ke/wp-content/uploads/2024/09/cropped-Parenteen-Kenya-Logo-rec.png"
CLINICIAN = "Jane Kariuki"
QUALIFICATION = "Clinical Psychologist"

# Business Colors: Teal (#008080), Navy (#0d1b2a), White (#FFFFFF)
PARENTEEN_STYLES = {
    "ParenTeen Navy (Primary)": {
        "bg": (13, 27, 42), "accent": (0, 128, 128), "text": (255, 255, 255), "glow": (0, 128, 128)
    },
    "ParenTeen Teal (Light)": {
        "bg": (0, 128, 128), "accent": (13, 27, 42), "text": (255, 255, 255), "glow": (255, 255, 255)
    }
}

# ============================================
# 2. THE CONTENT FACTORY
# ============================================
class ContentEngine:
    def __init__(self):
        try:
            resp = requests.get(LOGO_URL, timeout=5)
            self.logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        except:
            self.logo = Image.new("RGBA", (100, 100), (0,0,0,0))

    def generate_frame(self, quote, hook, t, style_name, size=(1080, 1920)):
        w, h = size
        style = PARENTEEN_STYLES[style_name]
        img = Image.new("RGB", size, style["bg"])
        draw = ImageDraw.Draw(img, "RGBA")

        # A. Therapeutic Breathing Pacer (6s total loop)
        # Expansion and contraction to keep users calm/engaged
        breath = (math.sin(t * (math.pi / 3)) + 1) / 2
        pacer_r = 350 + (breath * 100)
        draw.ellipse([w//2-pacer_r, h//2-pacer_r, w//2+pacer_r, h//2+pacer_r], 
                     fill=style["glow"] + (40,))

        # B. Wide Logo Integration (Top Safe Zone)
        logo_w = 550
        aspect = self.logo.height / self.logo.width
        logo_h = int(logo_w * aspect)
        logo_img = self.logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        # Center logo and apply subtle hover
        img.paste(logo_img, (w//2 - logo_w//2, 180 + int(math.sin(t*2)*10)), logo_img)

        # C. Kinetic Typewriter Logic
        char_limit = int(len(quote) * min(t/4.0, 1.0)) # Reveal over 4 seconds
        current_text = quote[:char_limit]

        # Typography Placement
        draw.text((w//2, 600), hook.upper(), fill=style["accent"], anchor="mm")
        draw.multiline_text((w//2, 850), current_text, fill=style["text"], 
                           spacing=40, align="center", anchor="mm")

        # D. Professional Clinician Footer
        footer_y = h - 300
        draw.line([(w//2-200, footer_y), (w//2+200, footer_y)], fill=style["accent"], width=4)
        draw.text((w//2, footer_y + 50), f"{CLINICIAN} | {QUALIFICATION}", fill=style["text"], anchor="mm")
        draw.text((w//2, footer_y + 110), "www.parenteenkenya.co.ke", fill=style["accent"], anchor="mm")

        return img

    def make_video(self, quote, hook, style_name):
        frames = []
        fps, duration = 12, 6 
        for i in range(fps * duration):
            frames.append(np.array(self.generate_frame(quote, hook, i/fps, style_name)))
        
        buf = io.BytesIO()
        iio.imwrite(buf, frames, format='mp4', fps=fps, codec='libx264')
        buf.seek(0)
        return buf

# ============================================
# 3. STREAMLIT INTERFACE (GROQ POWERED)
# ============================================
def main():
    st.set_page_config(page_title="ParenTeen Studio", layout="wide")
    
    if 'engine' not in st.session_state:
        st.session_state.engine = ContentEngine()

    st.title("🌿 ParenTeen Kenya Studio")
    st.info(f"Connected to Groq AI | Content Engine for {CLINICIAN}")

    # Use try/except for the Groq API key safety
    api_key = st.secrets.get("groq_key")
    if not api_key:
        st.error("Please add 'groq_key' to your Streamlit Secrets.")
        st.stop()
    
    client = Groq(api_key=api_key)

    col_ctrl, col_prev = st.columns([1, 1.2])

    with col_ctrl:
        st.header("🧠 Content Generation")
        topic = st.selectbox("Topic", ["Anxiety", "Phone Addiction", "Self-Esteem", "Communication"])
        
        if st.button("✨ Get AI Clinical Insight"):
            prompt = f"As a psychologist for ParenTeen Kenya, give me a 3-word hook and a 15-word teen parenting insight for {topic}. JSON: {{'hook': '...', 'quote': '...'}}"
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], 
                                               model="mixtral-8x7b-32768", 
                                               response_format={"type": "json_object"})
            data = json.loads(res.choices[0].message.content)
            st.session_state.hook = data['hook']
            st.session_state.quote = data['quote']

        h_val = st.text_input("Hook", value=st.session_state.get('hook', 'HEAR THEM OUT'))
        q_val = st.text_area("Insight", value=st.session_state.get('quote', 'Listening is the first step.'))
        s_val = st.selectbox("Style", list(PARENTEEN_STYLES.keys()))
        
        render = st.button("🎬 Render Final MP4", use_container_width=True)

    with col_prev:
        if render:
            with st.spinner("Generating clinical-grade animation..."):
                video = st.session_state.engine.make_video(q_val, h_val, s_val)
                st.video(video)
                st.download_button("📥 Download Post", video, "parenteen_ready.mp4")

if __name__ == "__main__":
    main()
