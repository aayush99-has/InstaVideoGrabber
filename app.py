import os
import logging
import instaloader
import tempfile
from flask import Flask, render_template, request, send_file, jsonify
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

def is_valid_instagram_url(url):
    """Validate if the URL is a valid Instagram post/reel URL"""
    parsed = urlparse(url)
    if parsed.netloc not in ['www.instagram.com', 'instagram.com']:
        return False
    path_parts = parsed.path.split('/')
    # Accept both posts (/p/) and reels (/reel/) URLs
    return any(segment in ['p', 'reel'] for segment in path_parts)

def get_post_shortcode(url):
    """Extract the post/reel shortcode from Instagram URL"""
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    try:
        # Check for both post and reel URLs
        if 'p' in path_parts:
            return path_parts[path_parts.index('p') + 1]
        elif 'reel' in path_parts:
            return path_parts[path_parts.index('reel') + 1]
        return None
    except (ValueError, IndexError):
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')

    if not url:
        return jsonify({'error': 'Please provide an Instagram URL'}), 400

    if not is_valid_instagram_url(url):
        return jsonify({'error': 'Invalid Instagram URL. Please provide a valid Instagram post or reel URL'}), 400

    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")

        # Initialize instaloader with the temp directory
        L = instaloader.Instaloader(dirname_pattern=temp_dir)

        # Get post shortcode
        shortcode = get_post_shortcode(url)
        if not shortcode:
            return jsonify({'error': 'Could not extract post ID from URL'}), 400

        # Get post
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Download the post (this will save video/photo in the temp directory)
        L.download_post(post, target=temp_dir)

        # Find the downloaded media file in temp directory
        if post.is_video:
            media_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
            file_extension = '.mp4'
            media_type = 'video'
        else:
            media_files = [f for f in os.listdir(temp_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            file_extension = os.path.splitext(media_files[0])[1] if media_files else '.jpg'
            media_type = 'photo'

        if not media_files:
            raise FileNotFoundError(f"{media_type.capitalize()} file not found in download directory")

        media_path = os.path.join(temp_dir, media_files[0])
        logger.debug(f"Found {media_type} file: {media_path}")

        return send_file(
            media_path,
            as_attachment=True,
            download_name=f'instagram_{media_type}_{shortcode}{file_extension}',
            mimetype=f'{"video" if post.is_video else "image"}/{file_extension[1:]}'
        )

    except instaloader.exceptions.InstaloaderException as e:
        logger.error(f"Instaloader error: {str(e)}")
        return jsonify({'error': 'Failed to download content. Please check the URL and try again.'}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        # Clean up temporary directory if it exists
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory: {str(e)}")

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)