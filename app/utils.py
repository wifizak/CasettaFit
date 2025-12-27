"""Utility functions for the application"""
import os
import uuid
from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename, allowed_extensions=ALLOWED_IMAGE_EXTENSIONS):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder, allowed_extensions=ALLOWED_IMAGE_EXTENSIONS):
    """
    Safely save an uploaded file with security checks
    
    Args:
        file: FileStorage object from Flask request
        upload_folder: Directory to save the file (relative to app root)
        allowed_extensions: Set of allowed file extensions
    
    Returns:
        str: Generated filename if successful, None otherwise
    
    Security features:
        - Validates file extension
        - Uses UUID for filename (prevents overwrites and path traversal)
        - Sanitizes extension with secure_filename
        - Creates upload directory if needed
    """
    if not file or not allowed_file(file.filename, allowed_extensions):
        return None
    
    # Extract and sanitize extension
    ext = file.filename.rsplit('.', 1)[1].lower()
    ext = secure_filename(ext)  # Additional sanitization
    
    # Generate unique filename using UUID
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Construct safe filepath (no user input in path)
    filepath = os.path.join(upload_folder, filename)
    
    # Additional security: ensure path is within upload folder
    # (prevents directory traversal attacks)
    abs_upload_folder = os.path.abspath(upload_folder)
    abs_filepath = os.path.abspath(filepath)
    
    if not abs_filepath.startswith(abs_upload_folder):
        raise ValueError("Invalid file path - potential directory traversal attack")
    
    # Save file
    file.save(filepath)
    
    return filename


def delete_uploaded_file(filename, upload_folder):
    """
    Safely delete an uploaded file
    
    Args:
        filename: Name of the file to delete
        upload_folder: Directory where file is stored
    
    Returns:
        bool: True if deleted, False if file doesn't exist or error
    """
    if not filename:
        return False
    
    try:
        # Construct filepath
        filepath = os.path.join(upload_folder, filename)
        
        # Security check: ensure path is within upload folder
        abs_upload_folder = os.path.abspath(upload_folder)
        abs_filepath = os.path.abspath(filepath)
        
        if not abs_filepath.startswith(abs_upload_folder):
            raise ValueError("Invalid file path - potential directory traversal attack")
        
        # Delete if exists
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {filename}: {e}")
        return False
