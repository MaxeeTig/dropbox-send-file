#!/usr/bin/env python3
"""
Dropbox OAuth 2.0 Helper Script
Helps obtain a refresh token for Dropbox API authentication.
"""

import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import dropbox
from dropbox.oauth import DropboxOAuth2Flow


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server handler to receive OAuth callback."""
    
    def __init__(self, auth_flow, *args, **kwargs):
        self.auth_flow = auth_flow
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle OAuth callback."""
        try:
            # Parse the callback URL
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Convert query params from lists to single values (parse_qs returns lists)
            # finish() expects a dict with string values, not lists
            query_dict = {k: v[0] if v else '' for k, v in query_params.items()}
            
            # Check for authorization code
            if 'code' in query_dict:
                # Exchange authorization code for tokens
                # finish() expects the query parameters as a dictionary
                oauth_result = self.auth_flow.finish(query_dict)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <head><title>Authorization Successful</title></head>
                    <body>
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                        <script>window.close();</script>
                    </body>
                    </html>
                """)
                
                # Store result for main script
                self.server.oauth_result = oauth_result
                return
            
            # Check for error
            if 'error' in query_dict:
                error = query_dict['error']
                error_description = query_dict.get('error_description', 'Unknown error')
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                    <html>
                    <head><title>Authorization Failed</title></head>
                    <body>
                        <h1>Authorization Failed</h1>
                        <p>Error: {error}</p>
                        <p>{error_description}</p>
                    </body>
                    </html>
                """.encode())
                
                self.server.oauth_error = f"{error}: {error_description}"
                return
            
            # Default response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Waiting for Authorization</title></head>
                <body>
                    <h1>Waiting for authorization...</h1>
                </body>
                </html>
            """)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html>
                <head><title>Error</title></head>
                <body>
                    <h1>Error</h1>
                    <p>{str(e)}</p>
                </body>
                </html>
            """.encode())
            self.server.oauth_error = str(e)
    
    def log_message(self, format, *args):
        """Suppress HTTP server log messages."""
        pass


def get_refresh_token(app_key, app_secret, redirect_uri='http://localhost:8080'):
    """
    Perform OAuth 2.0 flow to obtain refresh token.
    
    Args:
        app_key: Dropbox app key (client_id)
        app_secret: Dropbox app secret (client_secret)
        redirect_uri: OAuth redirect URI (default: http://localhost:8080)
        
    Returns:
        dict: OAuth result containing refresh_token and access_token
    """
    # Create OAuth flow with offline access to get refresh token
    auth_flow = DropboxOAuth2Flow(
        app_key,
        redirect_uri,
        session={},
        csrf_token_session_key='csrf-token',
        consumer_secret=app_secret,
        token_access_type='offline'  # Request refresh token
    )
    
    # Get authorization URL
    authorize_url = auth_flow.start()
    
    print("\n" + "="*70)
    print("Dropbox OAuth 2.0 Authorization")
    print("="*70)
    print(f"\n1. Opening browser to authorize this application...")
    print(f"   If the browser doesn't open automatically, visit this URL:")
    print(f"\n   {authorize_url}\n")
    
    # Try to open browser automatically
    try:
        import webbrowser
        webbrowser.open(authorize_url)
        print("   Browser opened successfully.")
    except Exception:
        print("   Could not open browser automatically.")
        print("   Please copy and paste the URL above into your browser.\n")
    
    print("2. After authorizing, you will be redirected back to this application.")
    print("3. Waiting for authorization callback...\n")
    
    # Start local HTTP server to receive callback
    server_address = ('localhost', 8080)
    
    # Create custom handler factory
    def handler_factory(*args, **kwargs):
        return OAuthCallbackHandler(auth_flow, *args, **kwargs)
    
    httpd = HTTPServer(server_address, handler_factory)
    
    try:
        # Handle one request (the OAuth callback)
        httpd.handle_request()
        
        # Check for result
        if hasattr(httpd, 'oauth_result'):
            return httpd.oauth_result
        elif hasattr(httpd, 'oauth_error'):
            raise Exception(f"OAuth error: {httpd.oauth_error}")
        else:
            raise Exception("No OAuth result received. Authorization may have been cancelled.")
            
    except KeyboardInterrupt:
        print("\n\nAuthorization cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during OAuth flow: {e}", file=sys.stderr)
        raise
    finally:
        httpd.server_close()


def main():
    """Main entry point for OAuth helper script."""
    print("Dropbox OAuth 2.0 Refresh Token Helper")
    print("="*70)
    print("\nThis script will help you obtain a refresh token for Dropbox API access.")
    print("Refresh tokens allow automatic renewal of expired access tokens.\n")
    
    # Get app credentials
    print("Step 1: Enter your Dropbox App Credentials")
    print("-" * 70)
    print("Get these from: https://www.dropbox.com/developers/apps")
    print("1. Go to your app's settings page")
    print("2. Find 'App key' (client_id) and 'App secret' (client_secret)\n")
    
    app_key = input("Enter your App Key (client_id): ").strip()
    if not app_key:
        print("Error: App Key is required.", file=sys.stderr)
        sys.exit(1)
    
    app_secret = input("Enter your App Secret (client_secret): ").strip()
    if not app_secret:
        print("Error: App Secret is required.", file=sys.stderr)
        sys.exit(1)
    
    # Check if redirect URI is configured in app settings
    redirect_uri = 'http://localhost:8080'
    print(f"\nUsing redirect URI: {redirect_uri}")
    print("Make sure this redirect URI is added to your Dropbox app settings:")
    print("  https://www.dropbox.com/developers/apps -> Your App -> Settings -> OAuth 2")
    print("  Add redirect URI: http://localhost:8080\n")
    
    input("Press Enter to continue with authorization...")
    
    try:
        # Perform OAuth flow
        oauth_result = get_refresh_token(app_key, app_secret, redirect_uri)
        
        # Extract tokens
        refresh_token = oauth_result.refresh_token
        access_token = oauth_result.access_token
        
        if not refresh_token:
            print("\nWarning: No refresh token received. The access token may expire.", file=sys.stderr)
            print("Make sure 'token_access_type=offline' is set in your OAuth flow.", file=sys.stderr)
        
        # Display results
        print("\n" + "="*70)
        print("Authorization Successful!")
        print("="*70)
        print("\nAdd these credentials to your .env file:\n")
        print(f"DROPBOX_APP_KEY={app_key}")
        print(f"DROPBOX_APP_SECRET={app_secret}")
        if refresh_token:
            print(f"DROPBOX_REFRESH_TOKEN={refresh_token}")
        else:
            print("# DROPBOX_REFRESH_TOKEN= (not available)")
            print(f"DROPBOX_ACCESS_TOKEN={access_token}")
            print("\nNote: Access token will expire. Consider re-running this script")
            print("      with proper OAuth configuration to get a refresh token.")
        
        print("\n" + "="*70)
        print("\nYour .env file should look like this:\n")
        print("# Dropbox OAuth 2.0 Credentials")
        print(f"DROPBOX_APP_KEY={app_key}")
        print(f"DROPBOX_APP_SECRET={app_secret}")
        if refresh_token:
            print(f"DROPBOX_REFRESH_TOKEN={refresh_token}")
        else:
            print(f"DROPBOX_ACCESS_TOKEN={access_token}")
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
