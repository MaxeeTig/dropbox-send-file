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


def upload_file(file_path, dropbox_path, access_token):
    """
    Upload a file to Dropbox.
    
    Args:
        file_path: Path to the local file to upload
        dropbox_path: Destination path in Dropbox (e.g., /SharedFolder/filename.txt)
        access_token: Dropbox API access token
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Initialize Dropbox client
        dbx = dropbox.Dropbox(access_token)
        
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
        return False, f"Authentication error: {e}"
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


def get_access_token():
    """
    Get Dropbox access token from .env file or environment variable.
    
    Returns:
        str: Access token or None if not found
    """
    # Load .env file if it exists
    load_dotenv()
    
    # Try to get token from environment (loaded from .env or system env)
    token = os.getenv('DROPBOX_ACCESS_TOKEN')
    
    if not token:
        print("Error: DROPBOX_ACCESS_TOKEN not found.", file=sys.stderr)
        print("Please create a .env file with DROPBOX_ACCESS_TOKEN=your_token", file=sys.stderr)
        print("or set the DROPBOX_ACCESS_TOKEN environment variable.", file=sys.stderr)
        return None
    
    return token


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
        help='Dropbox access token (overrides .env and environment variable)'
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
    
    # Get access token
    if args.token:
        access_token = args.token
    else:
        access_token = get_access_token()
        if not access_token:
            sys.exit(1)
    
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
    success, message = upload_file(str(file_path), dropbox_path, access_token)
    
    if success:
        print(message)
        sys.exit(0)
    else:
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
