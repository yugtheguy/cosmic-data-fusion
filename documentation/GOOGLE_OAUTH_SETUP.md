# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for the COSMIC Data Fusion application.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top and select "New Project"
3. Enter a project name (e.g., "COSMIC Data Fusion")
4. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it and press "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace)
3. Click "Create"
4. Fill in the required information:
   - **App name**: COSMIC Data Fusion
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Add these scopes:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
8. Click "Update" then "Save and Continue"
9. On "Test users", add your email for testing
10. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Configure the OAuth client:
   - **Name**: COSMIC Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:5173` (frontend)
     - `http://localhost:8000` (backend)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/google/callback`
5. Click "Create"
6. Copy your **Client ID** and **Client Secret**

## Step 5: Update Environment Variables

1. Open your `.env` file in the project root
2. Update these variables with your credentials:

```env
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
FRONTEND_URL=http://localhost:5173
```

## Step 6: Install Dependencies

Make sure you have the required packages installed:

```bash
pip install authlib httpx fastapi-mail
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Step 7: Restart Your Backend Server

After updating the environment variables, restart your FastAPI server:

```bash
# Stop the current server (Ctrl+C)
# Then restart it
uvicorn app.main:app --reload
```

## Step 8: Test OAuth Login

1. Start your frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

2. Navigate to `http://localhost:5173/login`
3. Click the "Google" button
4. You should be redirected to Google's consent screen
5. After authorizing, you'll be redirected back and logged in

## Troubleshooting

### Error: "redirect_uri_mismatch"
- Make sure the redirect URI in your Google Cloud Console exactly matches: `http://localhost:8000/auth/google/callback`
- No trailing slashes!

### Error: "invalid_client"
- Double-check your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file
- Make sure there are no extra spaces or quotes

### Error: "Access blocked: This app's request is invalid"
- Make sure you've enabled the Google+ API
- Check that you've added the correct scopes in the OAuth consent screen

### Users can't access after first time
- Make sure your app is in "Testing" mode in the OAuth consent screen
- Add users as "Test users" in the OAuth consent screen

## Production Deployment

When deploying to production:

1. Update authorized origins and redirect URIs to include your production domain:
   - Authorized JavaScript origins: `https://yourdomain.com`
   - Authorized redirect URIs: `https://yourdomain.com/auth/google/callback`

2. Update your `.env` file:
   ```env
   FRONTEND_URL=https://yourdomain.com
   ```

3. Publish your OAuth consent screen (move from "Testing" to "In production")

## Security Best Practices

1. **Never commit your `.env` file** - It contains sensitive credentials
2. **Rotate secrets regularly** - Generate new credentials periodically
3. **Use different credentials** for development and production
4. **Monitor usage** - Check the Google Cloud Console for unusual activity

## Features

- ✅ Sign up with Google
- ✅ Login with Google
- ✅ Automatic email verification (Google emails are pre-verified)
- ✅ Automatic user creation on first login
- ✅ Seamless integration with existing email/password authentication

## File Structure

```
app/
├── oauth.py                          # OAuth configuration
└── api/
    └── auth_endpoints.py             # OAuth endpoints (/auth/google/login, /auth/google/callback)

frontend/
└── src/
    ├── pages/
    │   ├── LoginPage.jsx             # Google Sign In button
    │   ├── SignUpPage.jsx            # Google Sign Up button
    │   └── OAuthCallbackPage.jsx     # Handles OAuth redirect
    └── App.jsx                       # OAuth callback route
```

## Support

If you encounter any issues, check:
1. Browser console for frontend errors
2. Backend terminal for API errors
3. Google Cloud Console > APIs & Services > Credentials for configuration issues
