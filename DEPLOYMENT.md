# Deployment Guide: Luminate Cookbook to Streamlit Cloud

## Pre-Deployment Checklist

### Files Ready for Deployment
- [x] `app.py` - Main entry point (NEW)
- [x] `pages/1_Email_Banner_Processor.py` - Email Banner tool
- [x] `pages/2_Image_Uploader.py` - Image Uploader tool
- [x] `luminate_uploader_lib.py` - Shared upload library
- [x] `requirements.txt` - All dependencies (includes streamlit>=1.28.0)

### Dependencies Verified
- streamlit>=1.28.0 (supports st.Page and st.navigation)
- Pillow>=10.0.0
- opencv-python-headless>=4.8.0
- numpy>=1.24.0
- playwright>=1.40.0
- python-dotenv>=1.0.0
- requests>=2.28.0

## Deployment Steps

### Step 1: Commit and Push to GitHub

```bash
# Files are already staged. Commit them:
git commit -m "Add unified Luminate Cookbook app with multi-page navigation"

# Push to GitHub:
git push origin main
```

### Step 2: Update Streamlit Cloud Configuration

1. Navigate to https://share.streamlit.io
2. Sign in to your account
3. Find your app: **emailbanners** (https://emailbanners.streamlit.app/)
4. Click on the app to open settings
5. In the **Main file** field, change from:
   - `streamlit_app.py` 
   - to: `app.py`
6. Verify **Branch** is set to `main` (or your default branch)
7. Click **Save** - Streamlit Cloud will automatically redeploy

### Step 3: Monitor Deployment

1. Watch the deployment logs in Streamlit Cloud dashboard
2. Check for any errors, especially:
   - Import errors for pages
   - Playwright browser installation issues
   - Missing dependencies

### Step 4: Verify Deployment

After deployment completes, test:

1. **Home Page**: https://emailbanners.streamlit.app/
   - Should show "Luminate Cookbook" title
   - Navigation menu visible in sidebar
   - Tool cards displayed

2. **Email Banner Processor**: Click "Email Banner Processor" in sidebar
   - Page loads with banner settings
   - File upload works
   - Processing functions correctly

3. **Image Uploader**: Click "Image Uploader" in sidebar
   - Page loads with credential form
   - File upload works
   - Playwright browsers should be available (may take first load to install)

## Playwright Browser Installation

Streamlit Cloud automatically installs Playwright browsers when `playwright>=1.40.0` is in requirements.txt. The first time the Image Uploader page is accessed, browsers may take a moment to install.

If you encounter issues:
- Check Streamlit Cloud logs for Playwright installation errors
- Ensure `playwright>=1.40.0` is in requirements.txt
- Browsers install automatically on first use

## Rollback Plan

If deployment has issues:

1. In Streamlit Cloud dashboard, change **Main file** back to `streamlit_app.py`
2. Save - the old standalone app will be restored
3. Investigate issues and redeploy when fixed

## Post-Deployment

### Old Files Status

The following files are kept in the repository but are no longer used:
- `streamlit_app.py` - Old standalone Email Banner Processor (kept for reference/rollback)
- `luminate_uploader.py` - Old standalone Image Uploader (kept for reference)

These can be removed later if desired, but keeping them provides:
- Easy rollback option
- Reference for standalone deployment if needed
- Historical context

### Next Steps

1. Test all functionality on the deployed app
2. Share the URL with your team: https://emailbanners.streamlit.app/
3. Monitor for any user-reported issues
4. Consider removing old standalone files after confirming stable deployment
