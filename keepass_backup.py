#!/usr/bin/env python3
"""
KeePass Dropbox Backup Script
Safely backs up a KeePass kdbx file to Dropbox with verification and rollback capability.
"""

import argparse
import hashlib
import logging
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import dropbox
from dropbox.exceptions import AuthError, ApiError, HttpError

# Configuration variables
DEFAULT_SOURCE_FILE = ""  # Set your KeePass file path here, e.g., "C:/Users/User/Documents/keepass.kdbx"
DEFAULT_DROPBOX_FOLDER = "/KeepassBackups"  # Dropbox folder for backups
LOG_FILE = "keepass_backup.log"  # Log file path


def setup_logging(log_file_path=None):
    """
    Setup logging to both file and console.
    
    Args:
        log_file_path: Path to log file (default: LOG_FILE)
    
    Returns:
        logger: Configured logger instance
    """
    if log_file_path is None:
        log_file_path = LOG_FILE
    
    # Create logger
    logger = logging.getLogger('keepass_backup')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Format for log messages
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    
    # File handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def init_dropbox_client(app_key, app_secret, refresh_token):
    """
    Initialize Dropbox client with refresh token authentication.
    
    Args:
        app_key: Dropbox app key (client_id)
        app_secret: Dropbox app secret (client_secret)
        refresh_token: Dropbox refresh token
    
    Returns:
        dropbox.Dropbox: Initialized Dropbox client
    """
    return dropbox.Dropbox(
        app_key=app_key,
        app_secret=app_secret,
        oauth2_refresh_token=refresh_token
    )


def get_oauth_credentials():
    """
    Get Dropbox OAuth credentials from .env file or environment variables.
    Reused from dropbox_upload.py
    
    Returns:
        tuple: (app_key, app_secret, refresh_token) or None if insufficient credentials
    """
    load_dotenv()
    
    app_key = os.getenv('DROPBOX_APP_KEY', '').strip()
    app_secret = os.getenv('DROPBOX_APP_SECRET', '').strip()
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN', '').strip()
    
    if refresh_token and app_key and app_secret:
        return (app_key, app_secret, refresh_token)
    
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
    
    print("Error: Dropbox credentials not found.", file=sys.stderr)
    print("\nSet the following in your .env file:", file=sys.stderr)
    print("  DROPBOX_APP_KEY=your_app_key_here", file=sys.stderr)
    print("  DROPBOX_APP_SECRET=your_app_secret_here", file=sys.stderr)
    print("  DROPBOX_REFRESH_TOKEN=your_refresh_token_here", file=sys.stderr)
    print("\nRun 'python dropbox_oauth.py' to obtain a refresh token.", file=sys.stderr)
    print("See README.md for detailed setup instructions.", file=sys.stderr)
    return None


def calculate_checksum(file_path):
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        str: Hexadecimal SHA256 checksum
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_backup_filename(original_name):
    """
    Generate backup filename with date and time.
    Format: filename_YYYY-MM-DD_HH-MM-SS.kdbx
    
    Args:
        original_name: Original filename (with or without path)
    
    Returns:
        str: Backup filename
    """
    # Extract base name and extension
    path_obj = Path(original_name)
    base_name = path_obj.stem
    extension = path_obj.suffix
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Construct backup filename
    backup_name = f"{base_name}_{timestamp}{extension}"
    return backup_name


def check_file_exists(dbx, dropbox_path):
    """
    Check if a file exists in Dropbox.
    
    Args:
        dbx: Dropbox client
        dropbox_path: Path to check in Dropbox
    
    Returns:
        bool: True if file exists, False otherwise
    """
    try:
        dbx.files_get_metadata(dropbox_path)
        return True
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            return False
        raise
    except Exception:
        raise


def create_backup_copy(dbx, dropbox_path, backup_path, logger):
    """
    Create a backup copy of an existing file in Dropbox.
    
    Args:
        dbx: Dropbox client
        dropbox_path: Path to the original file in Dropbox
        backup_path: Path for the backup copy
        logger: Logger instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Creating backup copy: {backup_path}")
        # Download the original file
        metadata, response = dbx.files_download(dropbox_path)
        file_data = response.content
        
        # Upload as backup
        dbx.files_upload(
            file_data,
            backup_path,
            mode=dropbox.files.WriteMode('overwrite'),
            mute=False
        )
        logger.info(f"Backup copy created successfully: {backup_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to create backup copy: {e}")
        return False


def upload_file_temp(dbx, local_path, temp_path, logger):
    """
    Upload a file to Dropbox with temporary name.
    
    Args:
        dbx: Dropbox client
        local_path: Path to local file
        temp_path: Temporary path in Dropbox
        logger: Logger instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Uploading file with temporary name: {temp_path}")
        with open(local_path, 'rb') as f:
            file_data = f.read()
        
        dbx.files_upload(
            file_data,
            temp_path,
            mode=dropbox.files.WriteMode('overwrite'),
            mute=False
        )
        logger.info(f"File uploaded successfully to temporary location: {temp_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return False


def verify_upload(dbx, dropbox_path, local_path, logger):
    """
    Verify uploaded file by comparing checksums.
    
    Args:
        dbx: Dropbox client
        dropbox_path: Path to file in Dropbox
        local_path: Path to local file
        logger: Logger instance
    
    Returns:
        bool: True if checksums match, False otherwise
    """
    try:
        logger.info("Verifying file integrity...")
        
        # Calculate local file checksum
        local_checksum = calculate_checksum(local_path)
        logger.debug(f"Local file checksum: {local_checksum}")
        
        # Download file from Dropbox to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            try:
                metadata, response = dbx.files_download(dropbox_path)
                temp_file.write(response.content)
                temp_file.flush()
                
                # Calculate downloaded file checksum
                remote_checksum = calculate_checksum(temp_path)
                logger.debug(f"Remote file checksum: {remote_checksum}")
                
                # Compare checksums
                if local_checksum == remote_checksum:
                    logger.info("File integrity verified: checksums match")
                    return True
                else:
                    logger.error("File integrity check failed: checksums do not match")
                    return False
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False


def rename_file(dbx, old_path, new_path, logger):
    """
    Rename a file in Dropbox.
    
    Args:
        dbx: Dropbox client
        old_path: Current path in Dropbox
        new_path: New path in Dropbox
        logger: Logger instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Renaming file from {old_path} to {new_path}")
        dbx.files_move_v2(old_path, new_path)
        logger.info("File renamed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to rename file: {e}")
        return False


def delete_file(dbx, dropbox_path, logger):
    """
    Delete a file from Dropbox.
    
    Args:
        dbx: Dropbox client
        dropbox_path: Path to file in Dropbox
        logger: Logger instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Deleting file: {dropbox_path}")
        dbx.files_delete_v2(dropbox_path)
        logger.info("File deleted successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete file: {e}")
        return False


def rollback(dbx, state, logger):
    """
    Rollback changes in case of error.
    
    Args:
        dbx: Dropbox client
        state: Dictionary tracking operations performed
        logger: Logger instance
    
    Returns:
        bool: True if rollback successful, False otherwise
    """
    logger.warning("Starting rollback procedure...")
    success = True
    
    # Delete temporary file if it was created
    if state.get('temp_file_created'):
        temp_path = state.get('temp_path')
        if temp_path:
            logger.info(f"Deleting temporary file: {temp_path}")
            if not delete_file(dbx, temp_path, logger):
                success = False
    
    # Restore original file name if it was renamed
    if state.get('file_renamed'):
        old_path = state.get('old_path')
        new_path = state.get('new_path')
        if old_path and new_path:
            logger.info(f"Restoring original file name: {new_path} -> {old_path}")
            if not rename_file(dbx, new_path, old_path, logger):
                success = False
    
    # If old file was deleted and rename failed, restore from backup if available
    if state.get('old_file_deleted') and not state.get('file_renamed'):
        backup_path = state.get('backup_path')
        dropbox_file_path = state.get('dropbox_file_path')
        if backup_path and dropbox_file_path and check_file_exists(dbx, backup_path):
            logger.info(f"Restoring original file from backup: {backup_path} -> {dropbox_file_path}")
            # Restore by copying backup back to original location
            try:
                metadata, response = dbx.files_download(backup_path)
                file_data = response.content
                dbx.files_upload(
                    file_data,
                    dropbox_file_path,
                    mode=dropbox.files.WriteMode('overwrite'),
                    mute=False
                )
                logger.info("Original file restored from backup")
            except Exception as e:
                logger.error(f"Failed to restore from backup: {e}")
                success = False
                logger.warning(f"Backup copy is still available at: {backup_path}")
    
    if success:
        logger.info("Rollback completed successfully")
    else:
        logger.error("Rollback completed with some errors")
    
    return success


def backup_keepass(source_file, dropbox_folder, app_key, app_secret, refresh_token, logger):
    """
    Main backup function implementing the full backup algorithm.
    
    Args:
        source_file: Path to local KeePass file
        dropbox_folder: Dropbox folder for backups
        app_key: Dropbox app key
        app_secret: Dropbox app secret
        refresh_token: Dropbox refresh token
        logger: Logger instance
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Initialize state tracking for rollback
    state = {
        'temp_file_created': False,
        'temp_path': None,
        'file_renamed': False,
        'old_path': None,
        'new_path': None,
        'old_file_deleted': False,
        'backup_path': None
    }
    
    try:
        # Validate local file
        source_path = Path(source_file)
        if not source_path.exists():
            return False, f"Source file not found: {source_file}"
        if not source_path.is_file():
            return False, f"Path is not a file: {source_file}"
        
        logger.info(f"Starting backup of {source_file} to Dropbox")
        logger.info(f"File size: {source_path.stat().st_size} bytes")
        
        # Initialize Dropbox client
        dbx = init_dropbox_client(app_key, app_secret, refresh_token)
        
        # Construct Dropbox paths
        filename = source_path.name
        dropbox_file_path = f"{dropbox_folder.rstrip('/')}/{filename}"
        temp_file_path = f"{dropbox_file_path}.tmp"
        
        # Store paths in state for rollback
        state['dropbox_file_path'] = dropbox_file_path
        
        logger.info(f"Target Dropbox path: {dropbox_file_path}")
        
        # Check if file exists in Dropbox
        file_exists = check_file_exists(dbx, dropbox_file_path)
        
        if file_exists:
            logger.info("File exists in Dropbox, creating backup copy...")
            backup_filename = generate_backup_filename(filename)
            backup_path = f"{dropbox_folder.rstrip('/')}/{backup_filename}"
            state['backup_path'] = backup_path
            
            # Create backup copy (non-critical, log warning if fails)
            create_backup_copy(dbx, dropbox_file_path, backup_path, logger)
        else:
            logger.info("File does not exist in Dropbox, proceeding with upload")
        
        # Upload file with temporary name
        if not upload_file_temp(dbx, str(source_path), temp_file_path, logger):
            return False, "Failed to upload file to Dropbox"
        
        state['temp_file_created'] = True
        state['temp_path'] = temp_file_path
        
        # Verify upload integrity
        if not verify_upload(dbx, temp_file_path, str(source_path), logger):
            rollback(dbx, state, logger)
            return False, "File integrity verification failed"
        
        # Rename temporary file to final name
        if file_exists:
            # If original file exists, delete it first (we have backup copy)
            logger.info("Removing old file before renaming temporary file...")
            if delete_file(dbx, dropbox_file_path, logger):
                state['old_file_deleted'] = True
        
        if not rename_file(dbx, temp_file_path, dropbox_file_path, logger):
            rollback(dbx, state, logger)
            return False, "Failed to rename temporary file to final name"
        
        state['file_renamed'] = True
        state['old_path'] = temp_file_path
        state['new_path'] = dropbox_file_path
        
        # Clear temp_file_created since we've renamed it
        state['temp_file_created'] = False
        # Clear old_file_deleted since rename succeeded
        state['old_file_deleted'] = False
        
        logger.info("Backup completed successfully")
        return True, f"Successfully backed up {source_file} to {dropbox_file_path}"
        
    except AuthError as e:
        error_msg = str(e)
        logger.error(f"Authentication error: {error_msg}")
        rollback(dbx, state, logger)
        return False, f"Authentication error: {error_msg}"
    except ApiError as e:
        logger.error(f"Dropbox API error: {e.error}")
        rollback(dbx, state, logger)
        return False, f"Dropbox API error: {e.error}"
    except HttpError as e:
        logger.error(f"HTTP error: {e}")
        rollback(dbx, state, logger)
        return False, f"HTTP error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        rollback(dbx, state, logger)
        return False, f"Unexpected error: {e}"


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Backup KeePass kdbx file to Dropbox with verification and rollback',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python keepass_backup.py
  python keepass_backup.py --source C:/Users/User/Documents/keepass.kdbx
  python keepass_backup.py --source keepass.kdbx --dropbox-folder /MyBackups
  python keepass_backup.py -s keepass.kdbx -f /KeepassBackups -l backup.log
        """
    )
    
    parser.add_argument(
        '--source', '-s',
        type=str,
        default=DEFAULT_SOURCE_FILE,
        help=f'Path to local KeePass file (default: {DEFAULT_SOURCE_FILE or "not set"})'
    )
    
    parser.add_argument(
        '--dropbox-folder', '-f',
        type=str,
        default=DEFAULT_DROPBOX_FOLDER,
        help=f'Dropbox folder for backups (default: {DEFAULT_DROPBOX_FOLDER})'
    )
    
    parser.add_argument(
        '--log-file', '-l',
        type=str,
        default=None,
        help=f'Path to log file (default: {LOG_FILE})'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_file)
    
    # Validate source file is specified
    if not args.source:
        logger.error("Source file not specified. Use --source or set DEFAULT_SOURCE_FILE in script.")
        print("Error: Source file not specified.", file=sys.stderr)
        print("Use --source argument or set DEFAULT_SOURCE_FILE in the script.", file=sys.stderr)
        sys.exit(1)
    
    # Validate Dropbox folder format
    dropbox_folder = args.dropbox_folder
    if not dropbox_folder.startswith('/'):
        dropbox_folder = '/' + dropbox_folder
    
    # Get OAuth credentials
    credentials = get_oauth_credentials()
    if not credentials:
        logger.error("Failed to get OAuth credentials")
        sys.exit(1)
    app_key, app_secret, refresh_token = credentials
    
    # Perform backup
    success, message = backup_keepass(
        args.source,
        dropbox_folder,
        app_key,
        app_secret,
        refresh_token,
        logger
    )
    
    if success:
        logger.info(message)
        print(message)
        sys.exit(0)
    else:
        logger.error(message)
        print(f"Error: {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
