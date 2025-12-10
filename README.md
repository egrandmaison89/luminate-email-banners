# Luminate Email Banner Processor

Transform photos into perfectly-sized email banners with intelligent face detection that avoids cropping heads.

## 🎯 Two Ways to Use

### Option 1: Web App (Recommended for Teams)
A user-friendly web interface - no coding required!

**Try it locally:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

**Deploy to share with your team:**
1. Push this folder to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Share the URL with your team!

### Option 2: Command Line Script (For Power Users)
Process images in batch from the terminal.

```bash
# Install dependencies
pip install -r requirements.txt

# Put your images in the 'originals/' folder
# Then run:
python process_banners.py
```

Output will be saved to the `resized/` folder.

---

## 📐 Features

- **Smart Face Detection** - Automatically detects faces and crops intelligently to avoid cutting off heads
- **Customizable Dimensions** - Set your own width and height (default: 600×340px)
- **Filename Prefix** - Add a custom prefix to organize banners by program (e.g., "AGEM123_email_banner_600.jpg")
- **Retina Support** - Optionally generate 2x resolution images for high-DPI displays
- **Optimized File Sizes** - JPEG compression tuned for fast email loading
- **Batch Processing** - Process multiple images at once

---

## 📁 Project Structure

```
email_banners/
├── streamlit_app.py      # Web app (share with team)
├── process_banners.py    # CLI script (for local batch processing)
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── originals/           # Source images (for CLI)
└── resized/             # Output images (from CLI)
```

---

## ⚙️ Configuration

### Web App Settings (sidebar)
- **Width**: 400-1000px (default: 600px)
- **Height**: 150-600px (default: 340px)
- **JPEG Quality**: 60-95 (default: 82)
- **Filename Prefix**: Optional prefix for output files
- **Retina versions**: On/Off

### CLI Script Settings (edit `process_banners.py`)
```python
TARGET_WIDTH = 600
TARGET_HEIGHT = 340
RETINA_WIDTH = 1200
RETINA_HEIGHT = 680
JPEG_QUALITY = 82
```

---

## 🚀 Deploying to Streamlit Cloud (Free)

1. **Create a GitHub repository** and push this folder

2. **Go to** [share.streamlit.io](https://share.streamlit.io)

3. **Click "New app"** and select:
   - Your GitHub repo
   - Branch: `main`
   - Main file: `streamlit_app.py`

4. **Click Deploy!**

5. **Share the URL** with your team (e.g., `https://your-app.streamlit.app`)

Your teammates can now:
- Visit the URL from any device
- Upload images via drag-and-drop
- Adjust settings with sliders
- Add a filename prefix for their program
- Download processed banners

---

## 📋 Requirements

- Python 3.8+
- See `requirements.txt` for packages

---

## 🏃 About

Built by the Luminate team to easily create email banners from event photos.

