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

This tool uses OAuth 2.0 refresh token authentication, which automatically renews expired access tokens so you won't encounter authentication errors.

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

1. Create a `.env` file in the project directory (or copy from `.env.example` if it exists):
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

# Upload with short destination flag
python dropbox_upload.py document.pdf -d /Documents/document.pdf
```

## Error Handling

The script handles various error cases:

- **File not found**: If the local file doesn't exist
- **Authentication errors**: If credentials are invalid or expired
  - The script automatically refreshes expired access tokens using the refresh token
  - Shows helpful error messages if the refresh token is invalid or revoked
- **API errors**: If Dropbox API returns an error
- **Network errors**: If there's a connection issue
- **Permission errors**: If file permissions are incorrect

## Security Notes

- Never commit your `.env` file to version control
- Keep your app key, app secret, and refresh token secure and private
- The `.env` file is automatically ignored by git (see `.gitignore`)

## File Size Limitations

- Files up to 150 MiB are supported directly
- For larger files, consider implementing upload session API (future enhancement)

## Troubleshooting

### "Dropbox credentials not found"

- Make sure you've created a `.env` file with your credentials
- Set all three required variables: `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, and `DROPBOX_REFRESH_TOKEN`
- Or set the corresponding environment variables
- Run `python dropbox_oauth.py` to obtain a refresh token if you don't have one

### "Authentication error: invalid_access_token" or "Token expired"

This error can occur even with refresh token authentication. Possible causes:

1. **The refresh token is invalid or revoked**
   - Run `python dropbox_oauth.py` to generate a new refresh token
   - Update your `.env` file with the new refresh token

2. **The app key or app secret is incorrect**
   - Verify your App Key and App Secret at [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Make sure they match the app you used to generate the refresh token

3. **The refresh token was generated for a different app**
   - Ensure the App Key and App Secret in your `.env` file match the app used to generate the refresh token
   - If you created a new app, you'll need to generate a new refresh token for that app

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
