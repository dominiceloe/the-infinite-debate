# AWS S3 Backup Setup - Step-by-Step Guide

**Project:** The Infinite Debate
**Purpose:** Configure AWS S3 for automated PostgreSQL backups
**Estimated Time:** 30-45 minutes

---

## Prerequisites

- [ ] Active AWS account
- [ ] Terminal access
- [ ] Project repository cloned locally

---

## Step 1: Install AWS CLI

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

**Verify Installation:**
```bash
aws --version
# Should show: aws-cli/2.x.x...
```

**Configure AWS CLI (if first time):**
```bash
aws configure
# You'll need your AWS access key ID and secret (use your main AWS account for setup)
# Default region: us-east-1
# Default output format: json
```

---

## Step 2: Create S3 Bucket

```bash
# Set variables
REGION=us-east-1
BUCKET_NAME=philosophical-debates-backups

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region $REGION
```

**Expected Output:**
```
make_bucket: philosophical-debates-backups
```

---

## Step 3: Enable Bucket Versioning

```bash
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled \
  --region $REGION
```

**What this does:** Protects against accidental deletion by keeping previous versions of files.

---

## Step 4: Enable Encryption

```bash
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }' \
  --region $REGION
```

**What this does:** Automatically encrypts all uploaded files with AES-256 encryption.

---

## Step 5: Block Public Access

```bash
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
  --region $REGION
```

**What this does:** Ensures your backup bucket is never publicly accessible.

**Verify Bucket Setup:**
```bash
aws s3 ls
# Should show your new bucket: philosophical-debates-backups
```

---

## Step 6: Create IAM Policy

**Create policy document:**
```bash
cat > backup-policy.json << 'EOF'
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
EOF
```

**Create the policy in AWS:**
```bash
aws iam create-policy \
  --policy-name PhilosophicalDebatesBackupPolicy \
  --policy-document file://backup-policy.json
```

**Expected Output:**
```json
{
    "Policy": {
        "PolicyName": "PhilosophicalDebatesBackupPolicy",
        "PolicyId": "ANPA...",
        "Arn": "arn:aws:iam::123456789012:policy/PhilosophicalDebatesBackupPolicy",
        ...
    }
}
```

**Save the ARN** - you'll need it in the next step.

---

## Step 7: Create IAM User

**Create user:**
```bash
aws iam create-user --user-name philosophical-debates-backup
```

**Expected Output:**
```json
{
    "User": {
        "UserName": "philosophical-debates-backup",
        "UserId": "AIDA...",
        "Arn": "arn:aws:iam::123456789012:user/philosophical-debates-backup",
        ...
    }
}
```

---

## Step 8: Attach Policy to User

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Attach the policy
aws iam attach-user-policy \
  --user-name philosophical-debates-backup \
  --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/PhilosophicalDebatesBackupPolicy
```

**Verify Policy Attachment:**
```bash
aws iam list-attached-user-policies --user-name philosophical-debates-backup
```

---

## Step 9: Create Access Keys

```bash
aws iam create-access-key --user-name philosophical-debates-backup
```

**Expected Output:**
```json
{
    "AccessKey": {
        "UserName": "philosophical-debates-backup",
        "AccessKeyId": "AKIA...",
        "Status": "Active",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "CreateDate": "2025-10-25T12:34:56Z"
    }
}
```

**⚠️ CRITICAL: SAVE THESE CREDENTIALS IMMEDIATELY!**

Copy and save:
- `AccessKeyId`: AKIA...
- `SecretAccessKey`: wJalr...

**You will NOT be able to see the SecretAccessKey again!**

---

## Step 10: Configure Backend .env File

**Navigate to backend directory:**
```bash
cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend
```

**Edit or create .env file:**
```bash
# If .env doesn't exist, copy from example
cp .env.example .env

# Then edit with your favorite editor
nano .env  # or vim .env or code .env
```

**Add these lines to your .env file:**
```bash
# AWS S3 Backup Configuration
S3_BACKUP_BUCKET=philosophical-debates-backups
AWS_ACCESS_KEY_ID=AKIA...  # Paste your AccessKeyId from Step 9
AWS_SECRET_ACCESS_KEY=...   # Paste your SecretAccessKey from Step 9
AWS_DEFAULT_REGION=us-east-1
```

**Save and close the file.**

**⚠️ Security Check:**
```bash
# Verify .env is in .gitignore
grep ".env" .gitignore

# Should show: .env (or *.env)
```

---

## Step 11: Test Backup System

**Ensure Docker containers are running:**
```bash
docker compose ps
# Should show 'db' container as 'Up'
```

**Run your first backup:**
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

---

## Step 12: Verify Backup in S3

```bash
aws s3 ls s3://philosophical-debates-backups/daily/ --recursive --human-readable
```

**Expected Output:**
```
2025-10-25 10:30:00  735.0 KiB daily/2025-10-25/debates_daily_20251025_103000.sql.gz
```

**Check in AWS Console (optional):**
1. Go to https://console.aws.amazon.com/s3/
2. Click on `philosophical-debates-backups`
3. Navigate to `daily/2025-10-25/`
4. You should see your backup file

---

## Step 13: Test Restore (Optional but Recommended)

```bash
make restore-s3
```

**What happens:**
1. Shows list of available backups
2. Prompts you to enter S3 key (e.g., `daily/2025-10-25/debates_daily_20251025_103000.sql.gz`)
3. Asks for confirmation (type `YES`)
4. Downloads and restores to database

**⚠️ Warning:** This will REPLACE your current database. Only test if you're okay with that, or do it on a development database.

---

## Step 14: Test Backup Integrity

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

## Step 15: Setup Automated Backups (Cron)

**Edit crontab:**
```bash
crontab -e
```

**Add these lines:**
```cron
# Daily PostgreSQL backup to S3 at 3 AM
0 3 * * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/backup-to-s3.sh >> logs/backup.log 2>&1

# Monthly backup on 1st of month at 4 AM
0 4 1 * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/backup-to-s3.sh --monthly >> logs/backup.log 2>&1

# Test backup integrity on 15th of month at 5 AM
0 5 15 * * cd /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend && ./scripts/test-backup-restore.sh >> logs/backup-test.log 2>&1
```

**Save and exit the editor** (in vim: press `Esc`, type `:wq`, press `Enter`)

**Verify crontab is set:**
```bash
crontab -l
```

**Check cron is running (macOS):**
```bash
# macOS doesn't have a traditional cron service, it uses launchd
# Your cron jobs should run automatically

# You can check if cron executed by looking at logs tomorrow
tail -f backend/logs/backup.log
```

---

## Step 16: Monitor First Automated Backup

**Tomorrow morning (after 3 AM), check if backup ran:**
```bash
# View backup logs
cat /Users/thedom/LLM_PLAYGROUND/ideas/philosophical-debates/backend/logs/backup.log

# List S3 backups to verify new backup exists
aws s3 ls s3://philosophical-debates-backups/daily/ --recursive --human-readable
```

---

## ✅ Checklist - Verify Everything Works

- [ ] AWS CLI installed and configured
- [ ] S3 bucket created: `philosophical-debates-backups`
- [ ] Bucket versioning enabled
- [ ] Bucket encryption enabled
- [ ] Public access blocked
- [ ] IAM policy created: `PhilosophicalDebatesBackupPolicy`
- [ ] IAM user created: `philosophical-debates-backup`
- [ ] Policy attached to user
- [ ] Access keys created and saved
- [ ] `.env` file configured with AWS credentials
- [ ] Manual backup test successful: `make backup-s3`
- [ ] Backup visible in S3
- [ ] Integrity test passed: `make test-backup`
- [ ] Cron jobs configured
- [ ] First automated backup successful (check next day)

---

## 🔧 Troubleshooting

### Problem: "AWS CLI not found"
**Solution:**
```bash
# macOS - reinstall
brew install awscli

# Verify
which aws
aws --version
```

### Problem: "Access Denied" when uploading
**Solution:**
```bash
# Verify credentials are set
env | grep AWS

# Test AWS connection
aws sts get-caller-identity

# Check bucket exists
aws s3 ls s3://philosophical-debates-backups
```

### Problem: "Database dump failed"
**Solution:**
```bash
# Check Docker containers
docker compose ps

# Test database connection
docker compose exec db psql -U debatesuser -d debates -c "SELECT 1;"
```

### Problem: Cron job not running
**Solution:**
```bash
# macOS - check system.log for cron entries
log show --predicate 'process == "cron"' --last 1h

# Test with a simple cron job first
# Add to crontab: * * * * * echo "Test $(date)" >> /tmp/cron-test.log
# Wait 1 minute, then: cat /tmp/cron-test.log
```

---

## 📊 What You've Accomplished

- ✅ **Daily backups** at 3 AM (kept for 30 days)
- ✅ **Monthly backups** on the 1st (kept indefinitely)
- ✅ **AES-256 encryption** on all backups
- ✅ **Versioning** protection against deletion
- ✅ **Automated testing** monthly
- ✅ **99.999999999% durability** (AWS S3)

## 💰 Expected Costs

**Monthly:** ~$1-3 for typical database size
- Storage: ~$0.75/month (30 daily + monthly backups)
- Requests: ~$0.01/month
- Data transfer: Free (uploads), ~$0.10/month (restores)

**Monitor costs:** https://console.aws.amazon.com/billing/

---

## 📚 Next Steps

1. **Wait for first automated backup** (tomorrow at 3 AM)
2. **Check logs:** `cat backend/logs/backup.log`
3. **Verify in S3:** `aws s3 ls s3://philosophical-debates-backups/daily/ --recursive`
4. **Setup monitoring** (see `S3_AUTO_BACKUP_PLAN.md` for CloudWatch setup)
5. **Document credentials location** in password manager

---

## 🔐 Security Reminders

- ✅ Never commit `.env` to git
- ✅ Store AWS credentials securely (password manager)
- ✅ Rotate access keys quarterly
- ✅ Enable MFA on AWS root account
- ✅ Review IAM policies regularly

---

## 📖 Additional Resources

- **Full Implementation Plan:** `S3_AUTO_BACKUP_PLAN.md`
- **AWS S3 Documentation:** https://docs.aws.amazon.com/s3/
- **AWS IAM Best Practices:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- **Troubleshooting Guide:** See "Troubleshooting" section in `S3_AUTO_BACKUP_PLAN.md`

---

**Setup Complete!** 🎉

Your database backups are now automated and secure. Sleep well knowing your data is protected with enterprise-grade backup infrastructure.

**Questions?** Review the full plan in `S3_AUTO_BACKUP_PLAN.md` or check AWS documentation.

---

**Document Created:** 2025-10-25
**Last Updated:** 2025-10-25
