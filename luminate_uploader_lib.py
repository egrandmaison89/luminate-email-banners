#!/usr/bin/env python3
"""
Luminate Online Upload Library

Reusable functions for uploading images to Luminate Online Image Library.
Can be used by both CLI scripts and web applications.
"""

import os
import time
import requests
import subprocess
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

# Luminate Online URLs
LOGIN_URL = "https://secure2.convio.net/dfci/admin/AdminLogin"
IMAGE_LIBRARY_URL = "https://secure2.convio.net/dfci/admin/ImageLibrary"
BASE_URL = "https://danafarber.jimmyfund.org/images/content/pagebuilder/"


def login(page, username, password):
    """Log into Luminate Online with provided credentials."""
    page.goto(LOGIN_URL)
    
    # Wait for the page to fully load
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)  # Extra wait for JS to initialize
    
    # Use role-based selectors which are more reliable
    username_input = page.get_by_role("textbox").first
    password_input = page.get_by_role("textbox").nth(1)
    
    username_input.fill(username)
    password_input.fill(password)
    
    # Submit the form by clicking the Log In button
    page.get_by_role("button", name="Log In").click()
    
    # Wait for navigation after login
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)


def navigate_to_image_library(page):
    """Navigate to the Image Library."""
    page.goto(IMAGE_LIBRARY_URL)
    page.wait_for_load_state("networkidle")
    
    # Wait for the Upload Image button to be visible
    page.wait_for_selector('text=Upload Image', timeout=10000)


def verify_upload(url, max_retries=3, retry_delay=2):
    """Verify that an uploaded image URL is accessible and returns an image.
    
    Args:
        url: The URL to verify
        max_retries: Maximum number of retry attempts
        retry_delay: Seconds to wait between retries
        
    Returns:
        bool: True if URL is accessible and returns an image, False otherwise
    """
    
    for attempt in range(max_retries):
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            # Check if it's a successful response and content type is an image
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if content_type.startswith('image/'):
                    return True
            # If 404, might still be processing - retry
            if response.status_code == 404 and attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return False
        except requests.exceptions.RequestException:
            # Network error - retry if we have attempts left
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return False
        except:
            return False
    
    return False


def check_file_size(image_path, max_size_mb=10):
    """Check if file size is within limits.
    
    Args:
        image_path: Path to the image file
        max_size_mb: Maximum file size in MB (default 10MB)
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    file_size = os.path.getsize(image_path)
    file_size_mb = file_size / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        return (False, f"File too large: {file_size_mb:.1f}MB (max {max_size_mb}MB)")
    
    return (True, None)


def upload_image(page, image_path, verify=True):
    """Upload a single image to the Image Library.
    
    Args:
        page: Playwright page object
        image_path: Path to the image file to upload
        verify: Whether to verify the upload by checking the URL
        
    Returns:
        tuple: (success: bool, filename: str, error: str or None, url: str or None)
    """
    filename = os.path.basename(image_path)
    abs_path = os.path.abspath(image_path)
    
    # Check file size before attempting upload
    size_valid, size_error = check_file_size(abs_path, max_size_mb=10)
    if not size_valid:
        return (False, filename, size_error, None)
    
    try:
        # Click the Upload Image button to open the dialog
        page.get_by_role("link", name="Upload Image").click()
        
        # Wait for the dialog iframe to appear
        page.wait_for_timeout(1500)
        
        # The upload form is inside an iframe - we need to access it
        iframe_locator = page.frame_locator("iframe").last
        
        # Wait for the file input to be ready inside the iframe
        file_input = iframe_locator.locator('#imageFileUpload')
        file_input.wait_for(timeout=10000)
        
        # Check for error messages in the iframe before uploading (like duplicate filename)
        # This is a pre-check, but errors usually appear after upload attempt
        
        # Set the file on the file input
        file_input.set_input_files(abs_path)
        
        # Wait for the file to be selected
        page.wait_for_timeout(1000)
        
        # Click the Upload button inside the iframe
        upload_button = iframe_locator.locator('input[type="submit"][value="Upload"], button:has-text("Upload")')
        upload_button.click()
        
        # Wait for the upload to complete - wait for network activity to finish
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
        # Check for error messages after upload attempt
        # Look for common error patterns in the iframe
        error_detected = False
        error_message = None
        
        try:
            # Check for various error indicators
            error_selectors = [
                'text=/error/i',
                'text=/too large/i',
                'text=/already exists/i',
                'text=/duplicate/i',
                'text=/file size/i',
                'text=/exceed/i',
                '.error',
                '[class*="error"]',
                '[id*="error"]'
            ]
            
            for selector in error_selectors:
                try:
                    error_elements = iframe_locator.locator(selector)
                    if error_elements.count() > 0:
                        # Get the error text
                        error_text = error_elements.first
                        if error_text.is_visible(timeout=1000):
                            error_message = error_text.inner_text(timeout=1000)
                            if error_message and len(error_message.strip()) > 0:
                                error_detected = True
                                break
                except:
                    continue
            
            # Also check the page itself for error messages
            if not error_detected:
                try:
                    page_error = page.locator('text=/error|too large|already exists|duplicate/i')
                    if page_error.count() > 0 and page_error.first.is_visible(timeout=1000):
                        error_message = page_error.first.inner_text(timeout=1000)
                        if error_message and len(error_message.strip()) > 0:
                            error_detected = True
                except:
                    pass
            
        except:
            pass  # Continue with upload verification
        
        if error_detected and error_message:
            # Close dialog if still open
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except:
                pass
            page.reload()
            page.wait_for_load_state("networkidle")
            page.wait_for_selector('text=Upload Image', timeout=10000)
            return (False, filename, f"Upload failed: {error_message.strip()}", None)
        
        # After upload, refresh the page to ensure clean state for next upload
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Wait for the Upload Image link to be visible again
        page.wait_for_selector('text=Upload Image', timeout=10000)
        
        # Generate URL and verify if requested
        url = generate_url(filename)
        if verify:
            # Wait a moment for the image to be processed on the server
            page.wait_for_timeout(3000)
            if not verify_upload(url, max_retries=3, retry_delay=2):
                return (False, filename, "Upload completed but image URL is not accessible. This may indicate: (1) file is still processing, (2) duplicate filename already exists, or (3) upload failed silently.", None)
        
        return (True, filename, None, url)
        
    except PlaywrightTimeout as e:
        return (False, filename, f"Timeout: {str(e)}", None)
    except Exception as e:
        return (False, filename, str(e), None)


def generate_url(filename):
    """Generate the URL for an uploaded image."""
    return BASE_URL + filename


def ensure_playwright_browsers_installed(progress_callback=None):
    """Check if Playwright browsers are installed, and install them if missing.
    
    Args:
        progress_callback: Optional callback function for progress updates
    
    Returns:
        bool: True if browsers are available, False if installation failed
    """
    try:
        # Try to launch a browser to check if it's installed
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        error_str = str(e).lower()
        # Check if it's a browser installation error
        if "executable doesn't exist" in error_str or "browsers" in error_str:
            try:
                # Attempt to install browsers
                if progress_callback:
                    progress_callback(0, 0, "Installing Playwright browsers...", "info")
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                    capture_output=True,
                    timeout=300  # 5 minute timeout
                )
                return True
            except subprocess.TimeoutExpired:
                return False
            except Exception:
                return False
        else:
            # Re-raise if it's a different error
            raise


def upload_images_batch(username, password, image_paths, progress_callback=None):
    """Upload multiple images to Luminate Online.
    
    Args:
        username: Luminate username
        password: Luminate password
        image_paths: List of paths to image files
        progress_callback: Optional callback function(current, total, filename, status)
        
    Returns:
        dict: {
            'successful': list of filenames,
            'failed': list of (filename, error) tuples,
            'urls': list of URLs for successful uploads
        }
    """
    successful = []
    failed = []
    urls = []
    
    # Ensure Playwright browsers are installed before attempting to use them
    try:
        if not ensure_playwright_browsers_installed(progress_callback):
            error_msg = (
                "Playwright browsers are not installed. "
                "Please run: python -m playwright install chromium"
            )
            # Mark all images as failed with this error
            for image_path in image_paths:
                filename = os.path.basename(image_path)
                failed.append((filename, error_msg))
            return {
                'successful': successful,
                'failed': failed,
                'urls': urls
            }
    except Exception as e:
        # If ensure_playwright_browsers_installed raises an unexpected error
        error_msg = f"Playwright setup error: {str(e)}"
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            failed.append((filename, error_msg))
        return {
            'successful': successful,
            'failed': failed,
            'urls': urls
        }
    
    try:
        with sync_playwright() as p:
            # Launch browser in headless mode (better for web apps)
            try:
                browser = p.chromium.launch(headless=True)
            except PlaywrightError as e:
                error_str = str(e)
                if "executable doesn't exist" in error_str.lower() or "browsers" in error_str.lower():
                    # Provide helpful error message
                    raise RuntimeError(
                        "Playwright browser executable not found. "
                        "Please run: python -m playwright install chromium\n"
                        f"Original error: {error_str}"
                    )
                else:
                    raise
            
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Login
                if progress_callback:
                    progress_callback(0, len(image_paths), "Logging in...", "info")
                login(page, username, password)
                
                # Navigate to Image Library
                if progress_callback:
                    progress_callback(0, len(image_paths), "Navigating to Image Library...", "info")
                navigate_to_image_library(page)
                
                # Upload each image
                for i, image_path in enumerate(image_paths, 1):
                    filename = os.path.basename(image_path)
                    
                    if progress_callback:
                        progress_callback(i, len(image_paths), filename, "uploading")
                    
                    success, uploaded_filename, error, url = upload_image(page, image_path, verify=True)
                    
                    if success and url:
                        successful.append(uploaded_filename)
                        urls.append(url)
                        if progress_callback:
                            progress_callback(i, len(image_paths), filename, "success")
                    else:
                        error_msg = error or "Upload verification failed"
                        failed.append((filename, error_msg))
                        if progress_callback:
                            progress_callback(i, len(image_paths), filename, "error")
            
            except Exception as e:
                # If login or navigation fails, mark all as failed
                for image_path in image_paths:
                    filename = os.path.basename(image_path)
                    failed.append((filename, f"Initialization error: {str(e)}"))
            finally:
                browser.close()
    
    except RuntimeError as e:
        # Catch our custom RuntimeError for missing browsers
        error_msg = str(e)
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            failed.append((filename, error_msg))
    except Exception as e:
        # Catch any other unexpected errors during browser launch
        error_msg = f"Browser launch error: {str(e)}"
        if "executable doesn't exist" in str(e).lower():
            error_msg += "\nPlease run: python -m playwright install chromium"
        for image_path in image_paths:
            filename = os.path.basename(image_path)
            failed.append((filename, error_msg))
    
    return {
        'successful': successful,
        'failed': failed,
        'urls': urls
    }
