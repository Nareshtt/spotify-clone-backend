# Vercel Deployment Guide

## Files Added for Vercel:
- `vercel.json` - Vercel configuration
- `.env.example` - Environment variables template
- `build.sh` - Build script

## Deployment Steps:

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from backend directory:**
   ```bash
   cd backend/backend
   vercel
   ```

4. **Set Environment Variables in Vercel Dashboard:**
   - `SECRET_KEY` - Django secret key
   - `DEBUG` - Set to `False`
   - `DB_NAME` - PostgreSQL database name
   - `DB_USER` - Database user
   - `DB_PASSWORD` - Database password
   - `DB_HOST` - Database host
   - `DB_PORT` - Database port (usually 5432)

## Database Options:

### Option 1: Vercel Postgres
```bash
vercel postgres create
```

### Option 2: External PostgreSQL
- Use services like Neon, Supabase, or Railway
- Add connection details to environment variables

## Important Notes:
- File uploads won't persist on Vercel (use cloud storage)
- Ollama AI features may not work (serverless limitations)
- Consider using external AI APIs for production

## Update Frontend API URL:
Update `config/api.ts` with your Vercel URL:
```typescript
BASE_URL: 'https://your-app.vercel.app/api'
```