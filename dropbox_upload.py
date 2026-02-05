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


def upload_file(file_path, dropbox_path, app_key=None, app_secret=None, refresh_token=None, access_token=None):
    """
    Upload a file to Dropbox.
    
    Args:
        file_path: Path to the local file to upload
        dropbox_path: Destination path in Dropbox (e.g., /SharedFolder/filename.txt)
        app_key: Dropbox app key (client_id) - required for refresh token auth
        app_secret: Dropbox app secret (client_secret) - required for refresh token auth
        refresh_token: Dropbox refresh token - preferred method (auto-refreshes expired tokens)
        access_token: Dropbox access token - legacy method (expires, use refresh_token instead)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Initialize Dropbox client
        # Prefer refresh token authentication (auto-refreshes expired tokens)
        if refresh_token and app_key and app_secret:
            dbx = dropbox.Dropbox(
                app_key=app_key,
                app_secret=app_secret,
                oauth2_refresh_token=refresh_token
            )
        elif access_token:
            # Legacy mode: using access token directly (will expire)
            print("Warning: Using access token directly. Tokens expire and cannot be refreshed.", file=sys.stderr)
            print("Consider migrating to refresh token authentication. See README.md for details.", file=sys.stderr)
            dbx = dropbox.Dropbox(access_token)
        else:
            return False, "Authentication error: Either refresh_token+app_key+app_secret or access_token must be provided"
        
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
        if 'expired' in error_msg.lower() or 'expired_access_token' in error_msg:
            return False, (
                f"Authentication error: Token expired. {error_msg}\n"
                "To fix this, set up refresh token authentication:\n"
                "1. Get your app_key and app_secret from https://www.dropbox.com/developers/apps\n"
                "2. Run: python dropbox_oauth.py\n"
                "3. Add the credentials to your .env file\n"
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
    Supports both refresh token (recommended) and legacy access token methods.
    
    Returns:
        tuple: (app_key, app_secret, refresh_token, access_token) or None if insufficient credentials
    """
    # Load .env file if it exists
    load_dotenv()
    
    # Try to get refresh token credentials (preferred method)
    app_key = os.getenv('DROPBOX_APP_KEY')
    app_secret = os.getenv('DROPBOX_APP_SECRET')
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
    
    # Try to get legacy access token (fallback)
    access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
    
    # Check for refresh token setup (recommended)
    if refresh_token and app_key and app_secret:
        return (app_key, app_secret, refresh_token, None)
    
    # Fallback to legacy access token
    if access_token:
        print("Warning: Using legacy access token authentication.", file=sys.stderr)
        print("Access tokens expire and cannot be refreshed automatically.", file=sys.stderr)
        print("Consider migrating to refresh token authentication. See README.md for details.", file=sys.stderr)
        return (None, None, None, access_token)
    
    # No credentials found
    print("Error: Dropbox credentials not found.", file=sys.stderr)
    print("\nFor refresh token authentication (recommended):", file=sys.stderr)
    print("  Set DROPBOX_APP_KEY, DROPBOX_APP_SECRET, and DROPBOX_REFRESH_TOKEN in .env", file=sys.stderr)
    print("  Run 'python dropbox_oauth.py' to obtain a refresh token", file=sys.stderr)
    print("\nFor legacy access token authentication:", file=sys.stderr)
    print("  Set DROPBOX_ACCESS_TOKEN in .env (note: tokens expire)", file=sys.stderr)
    print("\nSee README.md for detailed setup instructions.", file=sys.stderr)
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
    
    parser.add_argument(
        '--token', '-t',
        type=str,
        default=None,
        help='Dropbox access token (legacy, overrides .env - tokens expire)'
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
    if args.token:
        # Legacy mode: use provided access token
        app_key, app_secret, refresh_token, access_token = None, None, None, args.token
    else:
        credentials = get_oauth_credentials()
        if not credentials:
            sys.exit(1)
        app_key, app_secret, refresh_token, access_token = credentials
    
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
        refresh_token=refresh_token,
        access_token=access_token
    )
    
    if success:
        print(message)
        sys.exit(0)
    else:
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
