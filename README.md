# Dropbox File Upload CLI

A simple command-line tool to upload files to Dropbox shared folders using the Dropbox API.

## Features

- Upload files to Dropbox from the command line
- Support for custom destination paths
- Secure token management via `.env` file
- Comprehensive error handling

## Installation

### 1. Install Python Dependencies

```bash
pip install dropbox python-dotenv
```

### 2. Set Up Dropbox Access Token

#### Option 1: Using .env file (Recommended)

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac: `cp .env.example .env`)

2. Edit `.env` and add your Dropbox access token:
   ```
   DROPBOX_ACCESS_TOKEN=your_access_token_here
   ```

#### Option 2: Using Environment Variable

```bash
# Windows PowerShell
$env:DROPBOX_ACCESS_TOKEN="your_access_token_here"

# Linux/Mac
export DROPBOX_ACCESS_TOKEN="your_access_token_here"
```

**Note**: The script will first check for `.env` file, then fall back to environment variable if `.env` is not found.

## Dropbox App Registration Instructions

### Step 1: Create Dropbox Account

1. Go to [https://www.dropbox.com/](https://www.dropbox.com/)
2. Sign up for a free account if you don't have one

### Step 2: Create App in Dropbox App Console

1. Navigate to [https://www.dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
2. Click **"Create app"**
3. Choose app configuration:
   - **Choose an API**: Select **"Dropbox API"**
   - **Choose the type of access**: Select **"Full Dropbox"** (or "App folder" if you want to restrict access)
   - **Name your app**: Enter a descriptive name (e.g., "File Upload CLI")
4. Click **"Create app"**

### Step 3: Get App Credentials

1. In your app's settings page, you'll see:
   - **App key** (also called `client_id`)
   - **App secret** (also called `client_secret`)
2. These are your API credentials (you may need these for OAuth flow, but not for simple access token)

### Step 4: Generate Access Token

1. In your app's settings page, scroll to **"OAuth 2"** section
2. Under **"Generated access token"**, click **"Generate"**
3. Copy the generated access token (this is what you'll use in the script)
4. **Important**: Keep this token secure and don't share it publicly

### Step 5: Set Permissions (if needed)

- Ensure your app has **"files.content.write"** permission
- This is usually enabled by default for Full Dropbox access

### Step 6: Configure Redirect URI (for OAuth flow)

- If using OAuth flow (not needed for generated access token):
  - Add redirect URI: `http://localhost:8080` or `http://localhost:5000`
  - This is only needed if implementing full OAuth flow

## Usage

### Basic Usage

Upload a file to Dropbox (will be placed in root folder with original filename):

```bash
python dropbox_upload.py document.pdf
```

### Specify Destination Path

Upload a file to a specific Dropbox folder:

```bash
python dropbox_upload.py document.pdf --destination /SharedFolder/document.pdf
```

Or use the short form:

```bash
python dropbox_upload.py document.pdf -d /SharedFolder/document.pdf
```

### Override Access Token

You can override the access token from command line:

```bash
python dropbox_upload.py document.pdf --token your_token_here
```

Or use the short form:

```bash
python dropbox_upload.py document.pdf -t your_token_here
```

### Help

View all available options:

```bash
python dropbox_upload.py --help
```

## Examples

```bash
# Upload a local file to Dropbox root
python dropbox_upload.py /path/to/myfile.txt

# Upload to a shared folder
python dropbox_upload.py report.pdf --destination /Shared/Reports/report.pdf

# Upload to a subfolder
python dropbox_upload.py image.jpg --destination /Photos/2024/image.jpg
```

## Error Handling

The script handles various error cases:

- **File not found**: If the local file doesn't exist
- **Authentication errors**: If the access token is invalid
- **API errors**: If Dropbox API returns an error
- **Network errors**: If there's a connection issue
- **Permission errors**: If file permissions are incorrect

## Security Notes

- Never commit your `.env` file to version control
- Keep your access token secure and private
- The `.env` file is automatically ignored by git (see `.gitignore`)

## File Size Limitations

- Files up to 150 MiB are supported directly
- For larger files, consider implementing upload session API (future enhancement)

## Troubleshooting

### "DROPBOX_ACCESS_TOKEN not found"
- Make sure you've created a `.env` file with your token, or
- Set the `DROPBOX_ACCESS_TOKEN` environment variable

### "Authentication error"
- Verify your access token is correct
- Check if the token has expired (generate a new one if needed)
- Ensure your app has the correct permissions

### "File not found"
- Check that the file path is correct
- Use absolute paths if relative paths don't work
- On Windows, use forward slashes or escaped backslashes

## License

This script is provided as-is for personal use.
