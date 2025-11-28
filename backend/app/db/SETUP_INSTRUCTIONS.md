# Database Setup Instructions

## Problem
You're getting this error:
```
Could not find the 'password_hash' column of 'users' in the schema cache
```

This is because your Supabase database doesn't have the correct schema for custom JWT authentication.

## Solution

### Option 1: Run Custom Auth Schema (Recommended)

1. **Go to Supabase Dashboard**
   - Open your project: https://supabase.com/dashboard
   - Navigate to: SQL Editor (left sidebar)

2. **Run the Custom Auth Schema**
   - Open: `backend/app/db/custom_auth_schema.sql`
   - Copy all the SQL code
   - Paste into Supabase SQL Editor
   - Click "Run" button

3. **What This Does:**
   - Creates a standalone `users` table with `password_hash` column
   - Removes dependency on Supabase Auth SDK
   - Sets up proper indexes and triggers
   - Disables Row-Level Security (since we're using custom JWT)

### Option 2: Add Column to Existing Table

If you want to keep existing user data:

```sql
-- Add password_hash column to existing users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Make it required (after adding, before creating new users)
-- ALTER TABLE public.users
-- ALTER COLUMN password_hash SET NOT NULL;

-- Disable RLS for custom auth
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;
```

## After Running Schema

1. **Test Signup**
   - Go to: https://ai-trading-ml.vercel.app/signup
   - Create a new account
   - Should work without errors

2. **Verify in Supabase**
   - Go to: Table Editor → users
   - You should see:
     - `id` (UUID)
     - `email`
     - `password_hash` (hashed password)
     - `full_name`
     - Other columns...

## Troubleshooting

### Still getting column errors?
- Clear Supabase cache: Wait 1-2 minutes after running schema
- Check table exists: `SELECT * FROM public.users LIMIT 1;`
- Verify column: `SELECT column_name FROM information_schema.columns WHERE table_name = 'users';`

### RLS Blocking Access?
- Make sure you disabled RLS: `ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;`
- Or use service role key (already configured in backend)

## Security Note

Row-Level Security (RLS) is disabled because:
- Using custom JWT authentication (not Supabase Auth)
- Backend uses service role key (bypasses RLS anyway)
- Access control handled by JWT tokens in backend

If you want RLS later, you can enable it with custom policies based on JWT claims.
