#!/usr/bin/env python3
"""
Email Banner Processor - Luminate Cookbook Tool

Transform photos into perfectly-sized email banners with intelligent face detection.
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import zipfile
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Email Banner Processor",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .upload-text {
        font-size: 1.2em;
        color: #666;
    }
    .success-box {
        padding: 1em;
        background-color: #d4edda;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_face_detector():
    """Load OpenCV's pre-trained face detector (cached)."""
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    return cv2.CascadeClassifier(cascade_path)


def detect_faces(image_array, face_cascade):
    """Detect faces in the image and return bounding boxes."""
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return faces


def calculate_safe_crop_region(img_width, img_height, faces, target_aspect_ratio):
    """Calculate optimal crop region that preserves faces."""
    target_height = int(img_width / target_aspect_ratio)
    
    if img_height <= target_height:
        return 0, 0, img_width, img_height
    
    if len(faces) > 0:
        head_padding = 0.5
        min_face_y = float('inf')
        max_face_bottom = 0
        
        for (x, y, w, h) in faces:
            face_top = max(0, y - int(h * head_padding))
            min_face_y = min(min_face_y, face_top)
            face_bottom = y + h
            max_face_bottom = max(max_face_bottom, face_bottom)
        
        face_region_height = max_face_bottom - min_face_y
        
        if face_region_height <= target_height:
            face_center_y = min_face_y + face_region_height // 2
            crop_top = face_center_y - target_height // 2
            
            if crop_top < 0:
                crop_top = 0
            elif crop_top + target_height > img_height:
                crop_top = img_height - target_height
        else:
            crop_top = min_face_y
            if crop_top + target_height > img_height:
                crop_top = img_height - target_height
    else:
        crop_top = (img_height - target_height) // 2
    
    return 0, crop_top, img_width, crop_top + target_height


def process_single_image(pil_image, settings, face_cascade):
    """Process a single image with the given settings."""
    # Convert PIL to numpy for face detection
    img_array = np.array(pil_image)
    img_height, img_width = img_array.shape[:2]
    
    # Detect faces
    faces = detect_faces(img_array, face_cascade)
    
    # Calculate crop region
    target_aspect_ratio = settings['width'] / settings['height']
    x1, y1, x2, y2 = calculate_safe_crop_region(
        img_width, img_height, faces, target_aspect_ratio
    )
    
    # Crop
    cropped = pil_image.crop((x1, y1, x2, y2))
    
    results = []
    
    # Process standard size
    resized = cropped.resize(
        (settings['width'], settings['height']), 
        Image.LANCZOS
    )
    if resized.mode in ('RGBA', 'P'):
        resized = resized.convert('RGB')
    
    # Save to bytes
    buffer = io.BytesIO()
    resized.save(buffer, format='JPEG', quality=settings['quality'], optimize=True)
    buffer.seek(0)
    
    results.append({
        'image': resized,
        'bytes': buffer.getvalue(),
        'width': settings['width'],
        'height': settings['height'],
        'size_kb': len(buffer.getvalue()) / 1024,
        'suffix': f"_{settings['width']}"
    })
    
    # Process retina size if enabled
    if settings['include_retina']:
        retina_width = settings['width'] * 2
        retina_height = settings['height'] * 2
        resized_retina = cropped.resize(
            (retina_width, retina_height), 
            Image.LANCZOS
        )
        if resized_retina.mode in ('RGBA', 'P'):
            resized_retina = resized_retina.convert('RGB')
        
        buffer_retina = io.BytesIO()
        resized_retina.save(buffer_retina, format='JPEG', quality=settings['quality'], optimize=True)
        buffer_retina.seek(0)
        
        results.append({
            'image': resized_retina,
            'bytes': buffer_retina.getvalue(),
            'width': retina_width,
            'height': retina_height,
            'size_kb': len(buffer_retina.getvalue()) / 1024,
            'suffix': f"_{retina_width}"
        })
    
    return {
        'faces_detected': len(faces),
        'original_size': (img_width, img_height),
        'results': results
    }


def create_zip_download(processed_images, filenames, settings):
    """Create a ZIP file containing all processed images."""
    zip_buffer = io.BytesIO()
    prefix = settings.get('filename_prefix', '')
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, (proc_data, original_name) in enumerate(zip(processed_images, filenames)):
            for result in proc_data['results']:
                # Build filename: [prefix_]email_banner[N]_[width].jpg
                if len(processed_images) > 1:
                    base = f"email_banner{i+1}"
                else:
                    base = "email_banner"
                
                if prefix:
                    filename = f"{prefix}_{base}{result['suffix']}.jpg"
                else:
                    filename = f"{base}{result['suffix']}.jpg"
                
                zip_file.writestr(filename, result['bytes'])
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def main():
    # Header
    st.title("🏃 Email Banner Processor")
    st.markdown("""
    Transform your photos into perfectly-sized email banners. 
    Upload images, adjust settings, and download optimized banners ready for your email templates.
    """)
    
    # Sidebar - Settings
    st.sidebar.header("⚙️ Banner Settings")
    
    st.sidebar.subheader("Dimensions")
    target_width = st.sidebar.slider(
        "Width (pixels)", 
        min_value=400, 
        max_value=1000, 
        value=600, 
        step=50,
        help="Standard email width is 600px"
    )
    
    target_height = st.sidebar.slider(
        "Height (pixels)", 
        min_value=150, 
        max_value=600, 
        value=340, 
        step=10,
        help="Adjust for desired banner proportions"
    )
    
    st.sidebar.markdown(f"**Aspect ratio:** {target_width/target_height:.2f}:1")
    
    st.sidebar.subheader("Quality")
    jpeg_quality = st.sidebar.slider(
        "JPEG Quality", 
        min_value=60, 
        max_value=95, 
        value=82,
        help="Higher = better quality but larger file size"
    )
    
    include_retina = st.sidebar.checkbox(
        "Include 2x Retina versions", 
        value=True,
        help="Creates additional high-resolution versions for Retina displays"
    )
    
    # Filename settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("📝 Filename")
    filename_prefix = st.sidebar.text_input(
        "Filename prefix (optional)",
        value="",
        placeholder="e.g., AGEM123",
        help="Add a prefix to all output filenames. Leave blank for default naming."
    )
    
    # Show filename preview
    preview_name = f"{filename_prefix}_email_banner" if filename_prefix else "email_banner"
    st.sidebar.markdown(f"**Preview:** `{preview_name}_{target_width}.jpg`")
    
    # Preview dimensions
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 Output Preview")
    st.sidebar.markdown(f"""
    **Standard:** {target_width} × {target_height} px  
    {"**Retina:** " + str(target_width*2) + " × " + str(target_height*2) + " px" if include_retina else ""}
    """)
    
    # Build settings dict
    settings = {
        'width': target_width,
        'height': target_height,
        'quality': jpeg_quality,
        'include_retina': include_retina,
        'filename_prefix': filename_prefix
    }
    
    # Main content - File Upload
    st.markdown("---")
    st.subheader("📤 Upload Images")
    
    uploaded_files = st.file_uploader(
        "Drag and drop your images here",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Upload JPG or PNG images. You can select multiple files at once."
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} image(s) uploaded")
        
        # Load face detector
        face_cascade = load_face_detector()
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            process_button = st.button(
                "🚀 Process All Images", 
                type="primary", 
                use_container_width=True
            )
        
        if process_button:
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_images = []
            filenames = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Load image
                pil_image = Image.open(uploaded_file)
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Process
                result = process_single_image(pil_image, settings, face_cascade)
                processed_images.append(result)
                filenames.append(uploaded_file.name)
                
                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.text("✅ Processing complete!")
            
            # Store results in session state
            st.session_state['processed_images'] = processed_images
            st.session_state['filenames'] = filenames
            st.session_state['settings'] = settings
        
        # Display results if available
        if 'processed_images' in st.session_state:
            processed_images = st.session_state['processed_images']
            filenames = st.session_state['filenames']
            
            st.markdown("---")
            st.subheader("📸 Processed Banners")
            
            # Summary stats
            total_faces = sum(p['faces_detected'] for p in processed_images)
            total_files = len(processed_images) * (2 if settings['include_retina'] else 1)
            total_size = sum(
                sum(r['size_kb'] for r in p['results']) 
                for p in processed_images
            )
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Images Processed", len(processed_images))
            col2.metric("Faces Detected", total_faces)
            col3.metric("Total Size", f"{total_size:.1f} KB")
            
            # Download button
            st.markdown("---")
            zip_data = create_zip_download(processed_images, filenames, settings)
            
            # Build zip filename
            prefix = settings.get('filename_prefix', '')
            zip_filename = f"{prefix}_email_banners.zip" if prefix else "email_banners.zip"
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Download All Banners (ZIP)",
                    data=zip_data,
                    file_name=zip_filename,
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            
            # Preview images
            st.markdown("---")
            st.subheader("🖼️ Preview")
            
            for i, (proc_data, filename) in enumerate(zip(processed_images, filenames)):
                with st.expander(f"**{filename}** — {proc_data['faces_detected']} faces detected", expanded=(i < 3)):
                    # Show standard version
                    standard = proc_data['results'][0]
                    st.image(
                        standard['image'], 
                        caption=f"Standard: {standard['width']}×{standard['height']}px ({standard['size_kb']:.1f} KB)",
                        use_container_width=True
                    )
                    
                    # Build download filename
                    prefix = settings.get('filename_prefix', '')
                    if len(processed_images) > 1:
                        base = f"email_banner{i+1}"
                    else:
                        base = "email_banner"
                    
                    # Individual download
                    col1, col2 = st.columns(2)
                    with col1:
                        dl_name = f"{prefix}_{base}_{standard['width']}.jpg" if prefix else f"{base}_{standard['width']}.jpg"
                        st.download_button(
                            f"Download {standard['width']}px",
                            standard['bytes'],
                            dl_name,
                            "image/jpeg",
                            key=f"dl_standard_{i}"
                        )
                    
                    if settings['include_retina'] and len(proc_data['results']) > 1:
                        retina = proc_data['results'][1]
                        with col2:
                            dl_name_retina = f"{prefix}_{base}_{retina['width']}.jpg" if prefix else f"{base}_{retina['width']}.jpg"
                            st.download_button(
                                f"Download {retina['width']}px (Retina)",
                                retina['bytes'],
                                dl_name_retina,
                                "image/jpeg",
                                key=f"dl_retina_{i}"
                            )
    
    else:
        # Empty state
        st.markdown("""
        <div style="text-align: center; padding: 60px; color: #888;">
            <h3>👆 Upload images to get started</h3>
            <p>Supported formats: JPG, JPEG, PNG</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9em;">
        <p>Luminate Cookbook • Email Banner Processor</p>
        <p>Tip: Adjust the settings in the sidebar before processing</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
