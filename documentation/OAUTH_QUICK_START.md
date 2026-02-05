# Quick Start: Testing Google OAuth

## Prerequisites
- Python 3.9+ installed
- Node.js 16+ installed
- Google Cloud account

## Setup (5-10 minutes)

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure:
   - Application type: Web application
   - Authorized JavaScript origins: `http://localhost:5173`, `http://localhost:8000`
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
6. Copy your Client ID and Client Secret

### 2. Configure Environment Variables

Create/update `.env` file in project root:

```env
# Existing variables...
DATABASE_URL=sqlite:///./cosmic_data_fusion.db
SECRET_KEY=your-secret-key-here

# Add these for OAuth
GOOGLE_CLIENT_ID=paste_your_client_id_here
GOOGLE_CLIENT_SECRET=paste_your_client_secret_here
FRONTEND_URL=http://localhost:5173
```

### 3. Install Backend Dependencies

```bash
# From project root
pip install -r requirements.txt
```

This will install:
- `authlib>=1.3.0` - OAuth library
- `httpx>=0.26.0` - HTTP client

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Start Backend Server

```bash
# From project root
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 6. Start Frontend Server

```bash
# In a new terminal, from frontend directory
npm run dev
```

You should see:
```
VITE ready in X ms
Local: http://localhost:5173/
```

## Testing the OAuth Flow

### Test 1: Sign Up with Google

1. Open browser to `http://localhost:5173`
2. Click "Get Started" or "Sign Up"
3. Click the "Google" button (not GitHub)
4. You should be redirected to Google's login page
5. Log in with your Google account
6. Authorize the application
7. You should be redirected back to COSMIC dashboard
8. Check that your name appears in the sidebar

**Expected Result**: New user created, logged in, redirected to dashboard

### Test 2: Login with Google (Existing User)

1. Logout from COSMIC
2. Go to login page
3. Click the "Google" button
4. Should auto-login if still logged into Google
5. Redirected to dashboard

**Expected Result**: Existing user logged in, no duplicate account created

### Test 3: Email Already Exists

1. Register a user with email/password (e.g., `test@gmail.com`)
2. Logout
3. Try to login with Google using same email (`test@gmail.com`)
4. Should successfully log in

**Expected Result**: Links to existing account, marks email as verified

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: Google OAuth redirect URI doesn't match

**Solution**:
```
1. Go to Google Cloud Console > Credentials
2. Edit your OAuth 2.0 Client ID
3. Add EXACT redirect URI: http://localhost:8000/auth/google/callback
4. No trailing slash!
5. Save changes
```

### Error: "invalid_client"

**Problem**: Client ID or Secret is wrong

**Solution**:
```
1. Check .env file for typos
2. No spaces or quotes around values
3. Copy-paste credentials again from Google Console
4. Restart backend server
```

### Error: "Access blocked"

**Problem**: OAuth consent screen not configured

**Solution**:
```
1. Go to Google Cloud Console > OAuth consent screen
2. Configure consent screen (can use "Testing" mode)
3. Add your email as test user
4. Enable Google+ API
```

### Backend doesn't start

**Problem**: Missing dependencies

**Solution**:
```bash
pip install authlib httpx
# or
pip install -r requirements.txt
```

### Frontend shows "OAuth failed"

**Check**:
1. Backend is running on port 8000
2. Browser console for errors (F12)
3. Backend terminal for error logs
4. Google Cloud Console > Credentials is configured correctly

### Successful OAuth but not logged in

**Check**:
1. Browser console for errors
2. Check if token is in URL: `/oauth-callback?token=xxx`
3. Check `/auth/me` endpoint works with token
4. Clear localStorage and try again

## Verify Implementation

### Check Backend

```bash
# Test OAuth endpoints exist
curl http://localhost:8000/auth/google/login
# Should redirect to Google

curl http://localhost:8000/docs
# Should show FastAPI docs with OAuth endpoints
```

### Check Frontend

1. Open Developer Tools (F12)
2. Go to Network tab
3. Click Google button
4. Should see requests to:
   - `/auth/google/login`
   - Google OAuth URLs
   - `/oauth-callback`
   - `/auth/me`

### Check Database

```bash
# If using SQLite
sqlite3 cosmic_data_fusion.db "SELECT email, full_name, is_verified FROM users;"
```

Should show your Google user with `is_verified=1`

## Success Indicators

✅ Google button appears and is clickable
✅ Redirects to Google login page
✅ After authorization, redirects back to app
✅ User is logged in (name in sidebar)
✅ Can access dashboard and other protected pages
✅ User saved in database
✅ Email marked as verified
✅ Can logout and login again

## What's Next?

After confirming OAuth works:

1. **Production Setup**: Update redirect URIs for production domain
2. **Add More Providers**: GitHub, Microsoft, etc.
3. **Account Linking**: Allow users to link multiple auth methods
4. **Profile Pictures**: Fetch and display Google profile pictures
5. **Enhanced Security**: Add 2FA, session management

## Need Help?

1. Check `documentation/GOOGLE_OAUTH_SETUP.md` for detailed setup
2. Check `documentation/OAUTH_IMPLEMENTATION.md` for technical details
3. Review backend logs in terminal
4. Check browser console for frontend errors
5. Verify Google Cloud Console configuration

## Quick Reference

| Component | URL |
|-----------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| OAuth Login | http://localhost:8000/auth/google/login |
| OAuth Callback | http://localhost:8000/auth/google/callback |
| Google Console | https://console.cloud.google.com/ |

## Common Commands

```bash
# Start backend
uvicorn app.main:app --reload

# Start frontend
cd frontend && npm run dev

# Check dependencies
pip list | grep -E "authlib|httpx"

# View logs
# Check terminal running uvicorn

# Clear cache
# Browser: Ctrl+Shift+Delete
# localStorage: F12 > Application > Local Storage > Clear
```
