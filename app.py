# app.py
import os
import io
import base64
from PIL import Image, ImageOps
import streamlit as st

# Optional: Use OpenAI image generation if API key provided
with st.spinner("Generating image from prompt..."):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=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)

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        b64 = result.data[0].b64_json
        image_bytes = base64.b64decode(b64)
        gen_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        st.success("Image generated.")
        st.image(gen_image, caption="Generated graphic (preview)", use_column_width=False)

    except Exception as e:
        st.error(f"Image generation failed: {e}")


# Sidebar for API key (optional)
st.sidebar.header("Optional: Image generation (OpenAI)")
openai_key = st.sidebar.text_input("OpenAI API key (optional)", type="password")
use_openai = False
if openai_key:
    if not OPENAI_AVAILABLE:
        st.sidebar.error("`openai` package not installed. See requirements.txt.")
    else:
        openai.api_key = openai_key
        use_openai = True

# --- Upload shirt image ---
st.header("1) Upload plain shirt photo")
shirt_file = st.file_uploader("Upload shirt photo (JPG/PNG). Straight-on shot works best.", type=["png", "jpg", "jpeg"])

if shirt_file:
    shirt_img = Image.open(shirt_file).convert("RGBA")
    st.image(shirt_img, caption="Uploaded shirt", use_column_width=True)
else:
    st.info("Pehle shirt ki photo upload karo.")

st.markdown("---")

# --- Get graphic: either generate from prompt or upload ---
st.header("2) Graphic for print")
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("A) Generate from prompt (optional)")
    prompt = st.text_area("Enter prompt to generate a graphic (e.g., 'vintage floral emblem, high contrast, transparent background')", max_chars=1000, height=120)
    generate_btn = st.button("Generate image from prompt (OpenAI)") if use_openai else st.button("Generate (OpenAI unavailable)", disabled=True)
    gen_image = None
    if generate_btn and use_openai:
        if not prompt.strip():
            st.error("Prompt required.")
        else:
            with st.spinner("Generating image from prompt..."):
                try:
                    # Using OpenAI Image API (creates a PNG)
                    result = openai.Image.create(
                        model="gpt-image-1",
                        prompt=prompt,
                        size="1024x1024",
                        n=1,
                        response_format="b64_json"
                    )
                    b64 = result['data'][0]['b64_json']
                    image_bytes = base64.b64decode(b64)
                    gen_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                    st.success("Image generated.")
                    st.image(gen_image, caption="Generated graphic (preview)", use_column_width=False)
                except Exception as e:
                    st.error(f"Image generation failed: {e}")

with col2:
    st.subheader("B) Or upload a graphic image (PNG recommended with transparent background)")
    graphic_file = st.file_uploader("Upload graphic (PNG/JPG). For best results upload PNG with transparency.", type=["png", "jpg", "jpeg"], key="graphic_upload")
    upload_image = None
    if graphic_file:
        upload_image = Image.open(graphic_file).convert("RGBA")
        st.image(upload_image, caption="Uploaded graphic", use_column_width=False)

# Decide which graphic to use
graphic = gen_image if (gen_image is not None) else upload_image

if not graphic:
    st.info("Aap ya to prompt se graphic generate karo (OpenAI key chahiye) ya khud graphic upload karo.")
st.markdown("---")

# --- Overlay settings ---
st.header("3) Overlay settings (adjust position, size, rotation, opacity)")
scale_pct = st.slider("Scale (percentage of shirt width)", min_value=10, max_value=100, value=45)
x_offset_pct = st.slider("Horizontal offset (left/right)", min_value=-50, max_value=50, value=0)
y_offset_pct = st.slider("Vertical offset (move up/down)", min_value=-50, max_value=50, value=0)
rotation = st.slider("Rotation (degrees)", min_value=-45, max_value=45, value=0)
opacity = st.slider("Opacity (0 = transparent, 100 = fully opaque)", min_value=0, max_value=100, value=100)

st.markdown("---")

# --- Compose and show result ---
st.header("4) Preview & Download")
if shirt_file and graphic:
    # Prepare base shirt
    base = shirt_img.copy().convert("RGBA")

    # Compute target size for graphic: a percent of shirt width
    shirt_w, shirt_h = base.size
    target_w = int(shirt_w * (scale_pct / 100.0))

    # Maintain aspect ratio for graphic
    gw, gh = graphic.size
    ratio = gw / gh if gh != 0 else 1
    target_h = int(target_w / ratio)

    # Resize graphic
    graphic_resized = graphic.copy().resize((target_w, target_h), Image.LANCZOS)

    # Apply rotation
    if rotation != 0:
        graphic_resized = graphic_resized.rotate(rotation, expand=True)

    # Apply opacity
    if opacity < 100:
        alpha = graphic_resized.split()[-1].point(lambda p: int(p * (opacity / 100.0)))
        graphic_resized.putalpha(alpha)

    # Compute position: center chest by default: 35% from top
    default_y = int(shirt_h * 0.35)
    xpos = int((shirt_w - graphic_resized.width) / 2 + (x_offset_pct / 100.0) * shirt_w)
    ypos = int(default_y - (graphic_resized.height // 2) + (y_offset_pct / 100.0) * shirt_h)

    # Compose
    composed = base.copy()
    composed.paste(graphic_resized, (xpos, ypos), graphic_resized)

    st.image(composed, caption="Preview (PNG)", use_column_width=True)

    # Offer download
    buf = io.BytesIO()
    composed.save(buf, format="PNG")
    byte_im = buf.getvalue()

    b64 = base64.b64encode(byte_im).decode()
    href = f'<a href="data:file/png;base64,{b64}" download="shirt_print.png">Download PNG</a>'
    st.markdown(href, unsafe_allow_html=True)
else:
    st.info("Shirt photo aur graphic dono chahiye preview ke liye.")

st.markdown("---")
st.write("Notes:")
st.write("- App simple overlay karta hai (folds ya realistic warp nahi).")
st.write("- Best result ke liye shirt straight-on, plain aur graphic PNG with transparency use karo.")
st.write("- Agar OpenAI key provide karoge to prompt se graphic generate karne ka option milega.")
