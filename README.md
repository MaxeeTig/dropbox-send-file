# Dropbox File Upload CLI

A simple command-line tool to upload files to Dropbox shared folders using the Dropbox API.

## Features

- Upload files to Dropbox from the command line
- Support for custom destination paths
- Secure token management via `.env` file
- **OAuth 2.0 refresh token support** - automatic token renewal (no more expired tokens!)
- Comprehensive error handling

## Installation

### 1. Install Python Dependencies

```bash
pip install dropbox python-dotenv
```

### 2. Set Up Dropbox Authentication

#### Option 1: OAuth 2.0 Refresh Token (Recommended)

Refresh tokens automatically renew expired access tokens, so you won't encounter authentication errors.

**Step 1: Get App Credentials**

1. Navigate to [https://www.dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
2. Create a new app or select an existing one
3. In your app's settings page, find:
   - **App key** (also called `client_id`)
   - **App secret** (also called `client_secret`)
4. Copy these values - you'll need them in the next step

**Step 2: Configure Redirect URI**

1. In your app's settings page, scroll to **"OAuth 2"** section
2. Under **"Redirect URIs"**, click **"Add"**
3. Add: `http://localhost:8080`
4. Click **"Add"** to save

**Step 3: Obtain Refresh Token**

Run the OAuth helper script:

```bash
python dropbox_oauth.py
```

The script will:
1. Prompt you for your App Key and App Secret
2. Open a browser window for authorization
3. Guide you through the OAuth flow
4. Display your credentials to add to `.env`

**Step 4: Add Credentials to .env**

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac: `cp .env.example .env`)

2. Edit `.env` and add the credentials shown by the OAuth helper:
   ```
   DROPBOX_APP_KEY=your_app_key_here
   DROPBOX_APP_SECRET=your_app_secret_here
   DROPBOX_REFRESH_TOKEN=your_refresh_token_here
   ```

That's it! The script will now automatically refresh expired tokens.

#### Option 2: Legacy Access Token (Not Recommended)

Access tokens expire and cannot be refreshed automatically. Use refresh token authentication instead.

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac: `cp .env.example .env`)

2. Edit `.env` and add your Dropbox access token:
   ```
   DROPBOX_ACCESS_TOKEN=your_access_token_here
   ```

**Note**: The script will first check for `.env` file, then fall back to environment variables if `.env` is not found.

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
2. These are your OAuth credentials needed for refresh token authentication

### Step 4: Configure OAuth Settings

1. In your app's settings page, scroll to **"OAuth 2"** section
2. Under **"Redirect URIs"**, click **"Add"**
3. Add: `http://localhost:8080`
4. Click **"Add"** to save
5. Ensure your app has **"files.content.write"** permission (usually enabled by default for Full Dropbox access)

### Step 5: Obtain Refresh Token

Use the provided `dropbox_oauth.py` helper script to obtain a refresh token (see "Set Up Dropbox Authentication" section above).

**Note**: For legacy access token authentication (not recommended), you can generate a temporary access token in the app settings, but it will expire and cannot be refreshed automatically.

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

### Override Access Token (Legacy)

You can override the access token from command line (legacy mode, tokens expire):

```bash
python dropbox_upload.py document.pdf --token your_token_here
```

Or use the short form:

```bash
python dropbox_upload.py document.pdf -t your_token_here
```

**Note**: Using `--token` bypasses refresh token authentication. The token will expire and cannot be refreshed automatically.

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
- **Authentication errors**: If credentials are invalid or expired
  - With refresh token: Automatically refreshes expired access tokens
  - With legacy access token: Shows helpful error message with migration instructions
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

### "Unable to refresh access token without refresh token and app key"

This error occurs when using a temporary access token that has expired. To fix:

1. **Migrate to refresh token authentication** (recommended):
   - Get your App Key and App Secret from [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Run `python dropbox_oauth.py` to obtain a refresh token
   - Add `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, and `DROPBOX_REFRESH_TOKEN` to your `.env` file

2. **Or use legacy access token** (temporary fix):
   - Generate a new access token from your app settings
   - Add `DROPBOX_ACCESS_TOKEN` to your `.env` file
   - Note: This token will expire again and you'll need to repeat this process

### "Dropbox credentials not found"

- Make sure you've created a `.env` file with your credentials
- For refresh token auth: Set `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, and `DROPBOX_REFRESH_TOKEN`
- For legacy auth: Set `DROPBOX_ACCESS_TOKEN`
- Or set the corresponding environment variables

### "Authentication error: Token expired"

- If using refresh token: The script should auto-refresh. If this error appears, check that your refresh token, app key, and app secret are correct
- If using legacy access token: Generate a new access token from your app settings, or migrate to refresh token authentication

### "File not found"
- Check that the file path is correct
- Use absolute paths if relative paths don't work
- On Windows, use forward slashes or escaped backslashes

### OAuth Helper Script Issues

**"Authorization Failed" or "No OAuth result received"**
- Make sure `http://localhost:8080` is added to your app's redirect URIs
- Check that your App Key and App Secret are correct
- Ensure no firewall is blocking localhost:8080
- Try running the script again

**Browser doesn't open automatically**
- Copy the authorization URL from the terminal
- Paste it into your browser manually

## License

This script is provided as-is for personal use.
