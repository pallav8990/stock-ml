## 🔧 Google OAuth 400 Error Troubleshooting Guide

### Current Configuration Status:
- ✅ React App Running: http://localhost:3000
- ✅ Client ID: 956603860614-toht3c268o5tbaibivel1kn8c3ak4v39.apps.googleusercontent.com
- ✅ OAuth Library: @react-oauth/google (Latest)

### Most Likely Cause:
The 400 error typically means your Google Cloud Console OAuth configuration is missing the correct authorized origins.

### Fix Steps:

#### 1. Google Cloud Console Setup:
1. Go to: https://console.cloud.google.com/
2. Navigate to: "APIs & Services" → "Credentials"
3. Find your OAuth 2.0 Client ID
4. Click the edit (pencil) icon

#### 2. Add These EXACT URLs:

**Authorized JavaScript origins:**
```
http://localhost:3000
```

**Authorized redirect URIs:**
```
http://localhost:3000
```

⚠️ **Important Notes:**
- Use EXACT URLs above (no trailing slashes)
- Make sure you're editing the WEB client (not Android/iOS)
- Save the configuration after adding URLs
- It may take 5-10 minutes for changes to propagate

#### 3. Common Mistakes to Avoid:
❌ `http://localhost:3000/` (trailing slash)
❌ `https://localhost:3000` (https instead of http)
❌ `http://127.0.0.1:3000` (IP instead of localhost)
❌ `http://localhost:3000/auth/callback` (specific path)

✅ `http://localhost:3000` (correct format)

#### 4. Alternative Client ID Test:
If the issue persists, you can create a NEW OAuth Client ID:
1. In Google Cloud Console → "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Choose "Web application"
4. Add name: "Stock-ML Local Dev"
5. Add the authorized origins and redirect URIs as shown above
6. Copy the new Client ID to your .env file

#### 5. Verify APIs are Enabled:
Make sure these APIs are enabled in your project:
- Google+ API (or Google Identity API)
- Google People API (optional but recommended)

### Quick Test:
After making changes:
1. Clear your browser cache/cookies for localhost:3000
2. Try the login again
3. Check browser console for any error messages

### If Still Not Working:
- Try creating a completely new Google Cloud project
- Use a different browser or incognito mode
- Check if your Google account has 2FA enabled (shouldn't matter but good to know)

---

**Need Help?**
- Open browser DevTools (F12) → Console tab
- Look for any error messages when clicking "Sign in with Google"
- Share any console errors for further debugging