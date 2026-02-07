#!/usr/bin/env python3
"""
Dropbox File Upload CLI
Uploads a file to Dropbox shared folder using the Dropbox API.
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dropbox
from dropbox.exceptions import AuthError, ApiError, HttpError


def upload_file(file_path, dropbox_path, app_key, app_secret, refresh_token):
    """
    Upload a file to Dropbox.
    
    Args:
        file_path: Path to the local file to upload
        dropbox_path: Destination path in Dropbox (e.g., /SharedFolder/filename.txt)
        app_key: Dropbox app key (client_id) - required for refresh token auth
        app_secret: Dropbox app secret (client_secret) - required for refresh token auth
        refresh_token: Dropbox refresh token (auto-refreshes expired tokens)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Initialize Dropbox client with refresh token authentication
        dbx = dropbox.Dropbox(
            app_key=app_key,
            app_secret=app_secret,
            oauth2_refresh_token=refresh_token
        )
        
        # Read file in binary mode
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Upload file to Dropbox
        print(f"Uploading {file_path} to Dropbox...")
        dbx.files_upload(
            file_data,
            dropbox_path,
            mode=dropbox.files.WriteMode('overwrite'),
            mute=False
        )
        
        # Get file info to confirm upload
        file_info = dbx.files_get_metadata(dropbox_path)
        return True, f"Successfully uploaded to Dropbox: {dropbox_path}"
        
    except AuthError as e:
        error_msg = str(e)
        if 'expired' in error_msg.lower() or 'expired_access_token' in error_msg or 'invalid_access_token' in error_msg:
            return False, (
                f"Authentication error: {error_msg}\n\n"
                "Possible causes:\n"
                "1. The refresh token may be invalid or revoked\n"
                "2. The app key or app secret may be incorrect\n"
                "3. The refresh token may have been generated for a different app\n\n"
                "To fix this:\n"
                "1. Verify your App Key and App Secret at https://www.dropbox.com/developers/apps\n"
                "2. Run 'python dropbox_oauth.py' to generate a new refresh token\n"
                "3. Update your .env file with the new credentials\n"
                "See README.md for detailed instructions."
            )
        return False, f"Authentication error: {error_msg}"
    except ApiError as e:
        return False, f"Dropbox API error: {e.error}"
    except HttpError as e:
        return False, f"HTTP error: {e}"
    except FileNotFoundError:
        return False, f"File not found: {file_path}"
    except PermissionError:
        return False, f"Permission denied: {file_path}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def get_oauth_credentials():
    """
    Get Dropbox OAuth credentials from .env file or environment variables.
    Requires refresh token authentication (app_key, app_secret, and refresh_token).
    
    Returns:
        tuple: (app_key, app_secret, refresh_token) or None if insufficient credentials
    """
    # Load .env file if it exists
    load_dotenv()
    
    # Get refresh token credentials
    # Strip whitespace to handle any formatting issues
    app_key = os.getenv('DROPBOX_APP_KEY', '').strip()
    app_secret = os.getenv('DROPBOX_APP_SECRET', '').strip()
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN', '').strip()
    
    # Check for refresh token setup - all three are required
    if refresh_token and app_key and app_secret:
        return (app_key, app_secret, refresh_token)
    
    # If refresh_token exists but app_key/app_secret are missing, give clear error
    if refresh_token and (not app_key or not app_secret):
        print("Error: Refresh token found but missing required credentials.", file=sys.stderr)
        print("\nFor refresh token authentication, you need ALL of the following:", file=sys.stderr)
        missing = []
        if not app_key:
            missing.append("DROPBOX_APP_KEY")
        if not app_secret:
            missing.append("DROPBOX_APP_SECRET")
        print(f"  Missing: {', '.join(missing)}", file=sys.stderr)
        print("\nTo fix this:", file=sys.stderr)
        print("  1. Get your App Key and App Secret from: https://www.dropbox.com/developers/apps", file=sys.stderr)
        print("  2. Add them to your .env file:", file=sys.stderr)
        print("     DROPBOX_APP_KEY=your_app_key_here", file=sys.stderr)
        print("     DROPBOX_APP_SECRET=your_app_secret_here", file=sys.stderr)
        print("     DROPBOX_REFRESH_TOKEN=your_refresh_token_here", file=sys.stderr)
        return None
    
    # No credentials found
    print("Error: Dropbox credentials not found.", file=sys.stderr)
    print("\nSet the following in your .env file:", file=sys.stderr)
    print("  DROPBOX_APP_KEY=your_app_key_here", file=sys.stderr)
    print("  DROPBOX_APP_SECRET=your_app_secret_here", file=sys.stderr)
    print("  DROPBOX_REFRESH_TOKEN=your_refresh_token_here", file=sys.stderr)
    print("\nRun 'python dropbox_oauth.py' to obtain a refresh token.", file=sys.stderr)
    print("See README.md for detailed setup instructions.", file=sys.stderr)
    return None


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Upload a file to Dropbox shared folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dropbox_upload.py document.pdf
  python dropbox_upload.py document.pdf --destination /SharedFolder/document.pdf
  python dropbox_upload.py /path/to/file.txt --destination /MyFolder/file.txt
        """
    )
    
    parser.add_argument(
        'file',
        type=str,
        help='Path to the local file to upload'
    )
    
    parser.add_argument(
        '--destination', '-d',
        type=str,
        default=None,
        help='Destination path in Dropbox (default: /filename)'
    )
    
    args = parser.parse_args()
    
    # Validate local file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    if not file_path.is_file():
        print(f"Error: Path is not a file: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    # Get OAuth credentials
    credentials = get_oauth_credentials()
    if not credentials:
        sys.exit(1)
    app_key, app_secret, refresh_token = credentials
    
    # Determine Dropbox destination path
    if args.destination:
        dropbox_path = args.destination
        # Ensure path starts with /
        if not dropbox_path.startswith('/'):
            dropbox_path = '/' + dropbox_path
    else:
        # Use filename in root Dropbox folder
        dropbox_path = '/' + file_path.name
    
    # Upload file
    success, message = upload_file(
        str(file_path), 
        dropbox_path,
        app_key=app_key,
        app_secret=app_secret,
        refresh_token=refresh_token
    )
    
    if success:
        print(message)
        sys.exit(0)
    else:
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
