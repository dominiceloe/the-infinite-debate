# AWS S3 Backup Setup - Management Console Guide

**Project:** Philosophical Debates Platform
**Purpose:** Configure AWS S3 for automated PostgreSQL backups using AWS Console
**Estimated Time:** 20-30 minutes

---

## Prerequisites

- [ ] Active AWS account
- [ ] Signed in to AWS Management Console (https://console.aws.amazon.com/)
- [ ] Basic familiarity with AWS console navigation

---

## Part 1: Create S3 Bucket

### Step 1: Navigate to S3

1. Sign in to **AWS Management Console**: https://console.aws.amazon.com/
2. In the search bar at the top, type **S3**
3. Click on **S3** (Scalable Storage in the Cloud)

### Step 2: Create Bucket

1. Click the **Create bucket** button (orange button, top right)

2. **Bucket Configuration:**

   **General Configuration:**
   - **Bucket name:** `philosophical-debates-backups`
   - **AWS Region:** `US East (N. Virginia) us-east-1`

   ⚠️ **Important:** Bucket names must be globally unique. If this name is taken, try:
   - `philosophical-debates-backups-[your-initials]`
   - `phil-debates-backups-[random-number]`

### Step 3: Configure Bucket Settings

**Object Ownership:**
- Leave as **ACLs disabled (recommended)**

**Block Public Access settings:**
- ✅ **Check** "Block all public access"
- Keep all 4 sub-checkboxes checked
- Click **Acknowledge** warning

**Bucket Versioning:**
- Select **Enable**
- (This protects against accidental deletion)

**Tags (Optional):**
- Skip or add:
  - Key: `Project`, Value: `PhilosophicalDebates`
  - Key: `Purpose`, Value: `DatabaseBackups`

**Default encryption:**
- Encryption type: **Server-side encryption with Amazon S3 managed keys (SSE-S3)**
- Bucket Key: **Enable**

**Advanced settings:**
- Leave all defaults

### Step 4: Create Bucket

1. Scroll to bottom
2. Click **Create bucket** (orange button)
3. You should see: "Successfully created bucket 'philosophical-debates-backups'"

---

## Part 2: Create IAM Policy

### Step 5: Navigate to IAM

1. In the top search bar, type **IAM**
2. Click on **IAM** (Identity and Access Management)

### Step 6: Create Policy

1. In left sidebar, click **Policies**
2. Click **Create policy** button (blue button, top right)

### Step 7: Configure Policy - Visual Editor

**Option A: Use Visual Editor**

1. Click on the **Visual** tab (should be selected by default)

2. **Service:**
   - Click **Choose a service**
   - Search for **S3**
   - Click **S3**

3. **Actions:**
   - Under **Access level**, expand each section and check:
     - **List:**
       - ✅ `ListBucket`
       - ✅ `GetBucketLocation`
     - **Read:**
       - ✅ `GetObject`
     - **Write:**
       - ✅ `PutObject`
       - ✅ `DeleteObject`

4. **Resources:**
   - Click **Add ARN** next to "bucket"
     - Bucket name: `philosophical-debates-backups`
     - Click **Add ARNs**

   - Click **Add ARN** next to "object"
     - Bucket name: `philosophical-debates-backups`
     - Object name: Check **Any** (or type `*`)
     - Click **Add ARNs**

5. Click **Next** (bottom right)

**Option B: Use JSON Editor (Faster)**

1. Click on the **JSON** tab
2. Replace everything with this JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BackupToS3",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::philosophical-debates-backups/*",
        "arn:aws:s3:::philosophical-debates-backups"
      ]
    }
  ]
}
```

⚠️ **If you used a different bucket name**, replace `philosophical-debates-backups` in both places!

3. Click **Next** (bottom right)

### Step 8: Review and Create Policy

1. **Policy details:**
   - **Policy name:** `PhilosophicalDebatesBackupPolicy`
   - **Description (optional):** `Allows backup and restore operations for philosophical debates database`

2. **Tags (optional):** Skip

3. Click **Create policy** (orange button, bottom right)

4. You should see: "PhilosophicalDebatesBackupPolicy has been created"

---

## Part 3: Create IAM User

### Step 9: Navigate to Users

1. In left sidebar, click **Users**
2. Click **Create user** button (orange button, top right)

### Step 10: User Details

1. **User name:** `philosophical-debates-backup`
2. **Provide user access to AWS Management Console:** ❌ **UNCHECK THIS**
   - We only need programmatic access (API keys), not console login
3. Click **Next** (bottom right)

### Step 11: Set Permissions

1. **Permissions options:** Select **Attach policies directly**

2. In the search box, type: `PhilosophicalDebatesBackupPolicy`

3. ✅ **Check the box** next to `PhilosophicalDebatesBackupPolicy`

4. Click **Next** (bottom right)

### Step 12: Review and Create User

1. Review the details:
   - User name: `philosophical-debates-backup`
   - Permissions: `PhilosophicalDebatesBackupPolicy`

2. Click **Create user** (orange button, bottom right)

3. You should see: "User philosophical-debates-backup created successfully"

4. Click **View user** or navigate to Users list

---

## Part 4: Create Access Keys

### Step 13: Generate Access Keys

1. In the **Users** list, click on **philosophical-debates-backup**

2. Click on the **Security credentials** tab

3. Scroll down to **Access keys** section

4. Click **Create access key** button

### Step 14: Access Key Best Practices

1. **Use case:** Select **Command Line Interface (CLI)**

2. ✅ Check the box: "I understand the above recommendation and want to proceed..."

3. Click **Next** (bottom right)

### Step 15: Set Description Tag (Optional)

1. **Description tag (optional):** `Database backup scripts`

2. Click **Create access key** (orange button, bottom right)

### Step 16: SAVE YOUR CREDENTIALS

**⚠️ CRITICAL: YOU WILL ONLY SEE THIS ONCE!**

You'll see a screen with:
- **Access key:** `AKIA...` (starts with AKIA)
- **Secret access key:** `wJalrXUtnFEMI...` (long random string)

**IMMEDIATELY DO ONE OF THESE:**

**Option 1: Download CSV**
1. Click **Download .csv file** button
2. Save to a secure location (NOT in your project folder!)

**Option 2: Copy and Paste**
1. Copy the **Access key** → paste somewhere secure (TextEdit, Notes, password manager)
2. Click **Show** next to Secret access key
3. Copy the **Secret access key** → paste somewhere secure

**Option 3: Keep Browser Tab Open**
- Keep this tab open until you've added to `.env` file (next section)

3. Click **Done** when finished

---

## Part 5: Configure Your Project

### Step 17: Update .env File

1. Open Terminal

2. Navigate to backend directory:
```bash
cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend
```

3. Create or edit `.env` file:
```bash
# If .env doesn't exist, copy from example
cp .env.example .env

# Open in your editor
nano .env
# or: code .env (VS Code)
# or: open -e .env (TextEdit)
```

4. **Add these lines** (or update if they exist):
```bash
# AWS S3 Backup Configuration
S3_BACKUP_BUCKET=philosophical-debates-backups
AWS_ACCESS_KEY_ID=AKIA...              # Paste your Access key from Step 16
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI... # Paste your Secret access key from Step 16
AWS_DEFAULT_REGION=us-east-1
```

⚠️ **Replace the placeholder values** with YOUR actual keys from Step 16!

⚠️ **If you used a different bucket name**, update `S3_BACKUP_BUCKET` value!

5. **Save the file** (Ctrl+O, Enter, Ctrl+X in nano)

### Step 18: Verify .env Security

```bash
# Check .env is in .gitignore (should show ".env")
grep "\.env" .gitignore

# If not found, add it:
echo ".env" >> .gitignore
```

**⚠️ NEVER commit .env to git!** It contains secret credentials.

---

## Part 6: Install AWS CLI (Required for Scripts)

Even though you used the console for setup, the backup scripts need AWS CLI to upload files.

### Step 19: Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Verify:**
```bash
aws --version
# Should show: aws-cli/2.x.x
```

**Note:** You don't need to run `aws configure` because the scripts use environment variables from `.env`.

---

## Part 7: Test Your Setup

### Step 20: Test Manual Backup

1. **Ensure Docker is running:**
```bash
docker compose ps
# Should show 'db' container as 'Up'
```

2. **Run first backup:**
```bash
cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend
make backup-s3
```

**Expected Output:**
```
=======================================
PostgreSQL Backup to AWS S3
=======================================
Database: debates
Backup type: daily
S3 bucket: s3://philosophical-debates-backups
S3 path: daily/2025-10-25
---------------------------------------
[1/4] Creating database dump...
✓ Database dump created (2.4M)
[2/4] Compressing backup...
✓ Compressed to 735K
[3/4] Uploading to S3...
✓ Uploaded to s3://philosophical-debates-backups/daily/2025-10-25/debates_daily_20251025_103000.sql.gz
[4/4] Verifying upload integrity...
✓ Upload verified (735K)
=======================================
✓ Backup completed successfully!
=======================================
```

### Step 21: Verify in AWS Console

1. Go back to **AWS S3 Console**: https://s3.console.aws.amazon.com/s3/buckets

2. Click on your bucket: **philosophical-debates-backups**

3. You should see a folder structure:
   ```
   daily/
     └── 2025-10-25/
           └── debates_daily_20251025_103000.sql.gz
   ```

4. Click through to the `.sql.gz` file

5. Verify:
   - **Encryption:** Amazon S3 managed keys (SSE-S3)
   - **Storage class:** Standard
   - **Size:** Should match terminal output (~735 KB)

### Step 22: Test Backup Integrity

```bash
make test-backup
```

**Expected Output:**
```
=======================================
Automated Backup Integrity Test
=======================================
Finding latest backup...
Latest backup: daily/2025-10-25/debates_daily_20251025_103000.sql.gz
Downloading...
Decompressing...
Creating test database...
Restoring to test database...
Verifying data...
✓ Backup integrity verified
  Personas found: 196
=======================================
✓ Backup test passed!
=======================================
```

---

## Part 8: Setup Automated Backups

### Step 23: Configure Cron Jobs

1. **Edit crontab:**
```bash
crontab -e
```

2. **Add these lines** (press `i` to insert if using vim):
```cron
# Daily PostgreSQL backup to S3 at 3 AM
0 3 * * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/backup-to-s3.sh >> logs/backup.log 2>&1

# Monthly backup on 1st of month at 4 AM
0 4 1 * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/backup-to-s3.sh --monthly >> logs/backup.log 2>&1

# Test backup integrity on 15th of month at 5 AM
0 5 15 * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/test-backup-restore.sh >> logs/backup-test.log 2>&1
```

3. **Save and exit:**
   - vim: Press `Esc`, type `:wq`, press `Enter`
   - nano: Press `Ctrl+O`, `Enter`, `Ctrl+X`

4. **Verify crontab:**
```bash
crontab -l
# Should show your 3 cron jobs
```

### Step 24: Monitor First Automated Backup

**Tomorrow after 3 AM, check:**

```bash
# View backup log
cat /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/logs/backup.log

# Or watch in real-time (Ctrl+C to exit)
tail -f /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/logs/backup.log
```

**Verify in S3 Console:**
1. Go to S3 Console
2. Click your bucket
3. Navigate to `daily/[tomorrow's date]/`
4. Should see new backup file

---

## ✅ Final Checklist

- [ ] S3 bucket created: `philosophical-debates-backups`
- [ ] Bucket versioning enabled
- [ ] Bucket encryption enabled (SSE-S3)
- [ ] Public access blocked
- [ ] IAM policy created: `PhilosophicalDebatesBackupPolicy`
- [ ] IAM user created: `philosophical-debates-backup`
- [ ] Policy attached to user
- [ ] Access keys created and saved securely
- [ ] `.env` file configured with AWS credentials
- [ ] `.env` added to `.gitignore`
- [ ] AWS CLI installed
- [ ] Manual backup test successful: `make backup-s3`
- [ ] Backup visible in S3 Console
- [ ] Integrity test passed: `make test-backup`
- [ ] Cron jobs configured
- [ ] First automated backup scheduled (tomorrow 3 AM)

---

## 🔧 Troubleshooting

### ❌ Problem: "Access Denied" during backup

**Check 1: Verify .env file**
```bash
cat backend/.env | grep AWS
# Should show your AWS credentials
```

**Check 2: Verify IAM policy in Console**
1. Go to IAM → Users → philosophical-debates-backup
2. Click **Permissions** tab
3. Should show `PhilosophicalDebatesBackupPolicy` attached

**Check 3: Verify bucket name matches**
```bash
cat backend/.env | grep S3_BACKUP_BUCKET
# Should exactly match your bucket name in AWS
```

### ❌ Problem: "Database dump failed"

**Solution:**
```bash
# Check Docker is running
docker compose ps

# Should show db container as Up
# If not, start it:
docker compose up -d
```

### ❌ Problem: Can't see bucket in S3 Console

**Check region:**
1. In S3 Console, top-right corner should show **N. Virginia (us-east-1)**
2. If different, click region dropdown and select **US East (N. Virginia)**

### ❌ Problem: Cron job not running

**macOS-specific:**
```bash
# Give Terminal full disk access
# System Preferences → Security & Privacy → Privacy → Full Disk Access
# Add Terminal.app or your terminal emulator
```

**Test cron is working:**
```bash
# Add test cron job
crontab -e

# Add this line (runs every minute):
* * * * * echo "Test $(date)" >> /tmp/cron-test.log

# Save and wait 1 minute
# Then check:
cat /tmp/cron-test.log

# If working, remove test cron job
crontab -e
# Delete the test line
```

---

## 📊 What You've Accomplished

✅ **Production-grade backup system** with:
- Daily backups at 3 AM (30-day retention)
- Monthly backups on 1st (kept indefinitely)
- AES-256 encryption
- Version protection
- 99.999999999% durability (11 nines)

## 💰 Expected Monthly Costs

- **Storage:** ~$0.75/month (30 daily + monthly backups)
- **Requests:** ~$0.01/month
- **Total:** **~$1-3/month**

**Monitor costs in AWS:**
1. AWS Console → Billing Dashboard
2. Or: https://console.aws.amazon.com/billing/

---

## 🔐 Security Best Practices

✅ **You've implemented:**
- Dedicated IAM user (not root account)
- Minimal permissions (least privilege)
- Encrypted storage (AES-256)
- No public access
- Credentials not in git

🔒 **Additional recommendations:**
- Store credentials in password manager (1Password, LastPass, etc.)
- Rotate access keys every 90 days
- Enable MFA on AWS root account
- Regularly review IAM policies

---

## 📖 Next Steps

1. **Wait for first automated backup** (tomorrow at 3 AM)
2. **Verify it worked:** Check `logs/backup.log` and S3 Console
3. **Set calendar reminder:** Check backups weekly
4. **Document recovery procedure:** Test restore process quarterly

---

## 📚 Additional Resources

- **Full Implementation Details:** See `S3_AUTO_BACKUP_PLAN.md`
- **AWS S3 Console:** https://s3.console.aws.amazon.com/
- **AWS IAM Console:** https://console.aws.amazon.com/iam/
- **AWS Billing:** https://console.aws.amazon.com/billing/

---

**Setup Complete!** 🎉

Your database is now protected with automated, encrypted, enterprise-grade backups. You can sleep soundly knowing your data is safe!

**Quick Reference Commands:**
```bash
make backup-s3        # Manual backup
make restore-s3       # Restore from backup
make test-backup      # Test backup integrity
cat logs/backup.log   # View backup logs
```

---

**Document Created:** 2025-10-25
**Last Updated:** 2025-10-25
