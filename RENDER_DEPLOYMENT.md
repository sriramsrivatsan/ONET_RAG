# 🚀 Render Deployment Guide - Labor Market RAG

## Overview

This guide provides step-by-step instructions to deploy the Labor Market RAG system to Render.com, including the new optimized Dockerfile and render.yaml configuration.

## Prerequisites

- ✅ A Render account (free tier available)
- ✅ GitHub account
- ✅ OpenAI API key
- ✅ Your code pushed to a GitHub repository

## Deployment Methods

### Method 1: Automatic with render.yaml (Recommended)

**This is the easiest method - Render will auto-configure everything!**

#### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Labor Market RAG"
git remote add origin https://github.com/yourusername/labor-market-rag.git
git push -u origin main
```

#### Step 2: Create Render Service

1. Go to https://render.com and sign in
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will detect `render.yaml` and auto-configure:
   - ✅ Web service with Docker
   - ✅ Health checks
   - ✅ Persistent disk (10GB)
   - ✅ Starter plan settings

#### Step 3: Set Environment Variable

1. In the Render dashboard, go to your service
2. Navigate to **"Environment"** tab
3. Add your variable:
   ```
   Key: OPENAI_API_KEY
   Value: sk-your-actual-api-key-here
   ```
4. Click **"Save Changes"**

#### Step 4: Deploy

1. Render will automatically start building
2. Wait for build to complete (5-10 minutes first time)
3. Once deployed, click the URL to access your app!

### Method 2: Manual Web Service Setup

If you prefer manual configuration:

#### Step 1: Create New Web Service

1. Go to Render Dashboard
2. Click **"New +"** → **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Connect to your GitHub repo

#### Step 2: Configure Service

**Basic Settings:**
```
Name: labor-market-rag
Region: Oregon (or closest to your users)
Branch: main
```

**Build Settings:**
```
Runtime: Docker
Dockerfile Path: ./Dockerfile (should auto-detect)
Docker Context: . (root directory)
```

**Instance Settings:**
```
Instance Type: Starter ($7/month) or Free
```
*Note: Starter plan recommended for better performance*

#### Step 3: Add Environment Variables

Click **"Advanced"** and add:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `sk-your-actual-key` |
| `ENABLE_PERSISTENCE` | `true` |
| `CHROMA_PERSIST_PATH` | `/data/chroma_db` |

#### Step 4: Add Persistent Disk

1. Scroll to **"Disk"** section
2. Click **"Add Disk"**
3. Configure:
   ```
   Name: labor-rag-data
   Mount Path: /data
   Size: 10 GB
   ```

#### Step 5: Configure Health Check

1. In **"Advanced"** section
2. Set **Health Check Path**: `/_stcore/health`

#### Step 6: Deploy

1. Click **"Create Web Service"**
2. Render will build and deploy automatically
3. Monitor build logs in real-time

## Post-Deployment Steps

### 1. Access Your Application

Once deployed, you'll get a URL like:
```
https://labor-market-rag.onrender.com
```

### 2. Upload Data

1. Navigate to the **Admin** panel
2. Upload your `data.csv` file
3. Click **"Start Ingestion Pipeline"**
4. Wait for processing to complete (~2-5 minutes)

### 3. Test the System

1. Switch to **Client** view
2. Try sample queries:
   ```
   What jobs require creating digital documents?
   What's the total employment of digital document creators?
   ```

## Important Render-Specific Notes

### 1. Port Configuration

The updated Dockerfile automatically handles Render's `PORT` environment variable:
```dockerfile
CMD streamlit run app/main.py --server.port=${PORT:-8501}
```
This means it will use whatever port Render assigns.

### 2. Persistent Storage

Your vector index is saved to the persistent disk at `/data/chroma_db`:
- ✅ Survives restarts
- ✅ No need to re-index
- ✅ Faster subsequent starts

### 3. Free Tier Limitations

If using Render's free tier:
- ⚠️ Service spins down after 15 minutes of inactivity
- ⚠️ First request after spin-down takes ~30-60 seconds
- ⚠️ Limited to 750 hours/month (all free services combined)
- ✅ Upgrade to Starter plan ($7/mo) for always-on service

### 4. Automatic Deploys

Render auto-deploys when you push to your main branch:
```bash
git add .
git commit -m "Update feature"
git push origin main
# Render automatically deploys!
```

## Monitoring & Maintenance

### View Logs

1. Go to your service dashboard
2. Click **"Logs"** tab
3. View real-time application logs
4. Filter by error level

### Monitor Performance

In your service dashboard, check:
- **Metrics**: CPU, memory usage
- **Events**: Deployment history
- **Health**: Service health status

### Update Environment Variables

1. Go to **"Environment"** tab
2. Update variables
3. Click **"Save Changes"**
4. Service will automatically restart

### Manual Restart

If needed:
1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Or click **"Restart Service"** for quick restart

## Scaling & Optimization

### Upgrade Instance Type

For better performance with large datasets:

1. Go to **"Settings"** tab
2. Under **"Instance Type"**, select:
   - **Standard**: 2 GB RAM, $25/month
   - **Pro**: 4 GB RAM, $85/month

### Increase Disk Size

If you need more storage:

1. Go to **"Disks"** section
2. Click on your disk
3. Increase size (charges apply)

### Enable Auto-Scaling (Pro plans)

For high-traffic scenarios:
- Available on Pro plans and above
- Auto-scales based on CPU/memory
- Configure in service settings

## Troubleshooting

### Issue: Build Fails

**Check:**
1. Dockerfile syntax is correct
2. All files are committed to Git
3. requirements.txt is complete
4. Build logs for specific error

**Solution:**
```bash
# Test locally first
docker build -t labor-rag .
docker run -p 8501:8501 -e OPENAI_API_KEY=xxx labor-rag
```

### Issue: Service Won't Start

**Check:**
1. Environment variables are set
2. Health check path is correct: `/_stcore/health`
3. PORT is not hardcoded in Streamlit command

**Solution:**
- Review deployment logs
- Verify Dockerfile CMD uses `${PORT:-8501}`

### Issue: "Out of Memory" Error

**Solutions:**
1. Upgrade to larger instance type
2. Reduce batch sizes in `app/utils/config.py`:
   ```python
   EMBEDDING_BATCH_SIZE = 16  # Reduce from 32
   ```
3. Process smaller datasets initially

### Issue: Persistent Disk Not Working

**Check:**
1. Disk is mounted at `/data`
2. `CHROMA_PERSIST_PATH=/data/chroma_db` is set
3. Directory permissions in Dockerfile

**Solution:**
- In Dockerfile, ensure: `RUN mkdir -p /data/chroma_db && chmod -R 777 /data`

### Issue: Health Check Failing

**Check:**
1. Streamlit is actually starting
2. Health check path is `/_stcore/health` (not `/health`)
3. Port configuration is correct

**Solution:**
- Check logs for Streamlit startup errors
- Verify health check configuration in Render

## Cost Estimation

### Free Tier
- ✅ 750 hours/month shared across all services
- ✅ Perfect for testing
- ⚠️ Spins down after inactivity

### Starter Plan ($7/month)
- ✅ Always-on service
- ✅ 0.5 GB RAM
- ✅ Good for moderate use
- ⚠️ May struggle with large datasets

### Standard Plan ($25/month)
- ✅ 2 GB RAM
- ✅ Better performance
- ✅ Handles larger datasets
- ✅ Recommended for production

### Additional Costs
- **Disk Storage**: ~$0.25/GB/month
  - 10 GB disk = ~$2.50/month
- **Bandwidth**: Generally included
- **OpenAI API**: Based on usage (separate cost)

## Security Best Practices

### 1. Protect API Keys

✅ **Do:**
- Store API keys in Render environment variables
- Use Render's secret management
- Rotate keys regularly

❌ **Don't:**
- Commit API keys to Git
- Share keys in logs
- Use production keys in development

### 2. Enable HTTPS

Render automatically provides:
- ✅ Free SSL/TLS certificates
- ✅ HTTPS by default
- ✅ Automatic certificate renewal

### 3. Access Control

Consider adding authentication:
```python
# In app/main.py, add before main content
import streamlit as st

def check_password():
    """Simple password check"""
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

Then add to secrets:
```toml
app_password = "your-secure-password"
```

## Backup Strategy

### 1. Code Backup
- ✅ Already in Git/GitHub
- ✅ Automatic versioning

### 2. Data Backup

**Option 1: Manual Download**
1. Access your deployed app
2. Download processed data via UI

**Option 2: Disk Snapshots**
- Available on paid plans
- Configure in disk settings

**Option 3: Export to Cloud Storage**
Add cloud storage integration:
```python
# Example: Upload to S3 after processing
import boto3

def backup_to_s3(local_path, bucket, key):
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket, key)
```

## Advanced: Custom Domain

### 1. Add Custom Domain

1. Go to **"Settings"** → **"Custom Domain"**
2. Add your domain (e.g., `labor-rag.yourcompany.com`)
3. Configure DNS records as shown

### 2. DNS Configuration

Add CNAME record:
```
Type: CNAME
Name: labor-rag (or subdomain)
Value: labor-market-rag.onrender.com
```

### 3. SSL Certificate

- Render auto-provisions Let's Encrypt SSL
- Usually takes 5-10 minutes
- Auto-renews before expiry

## Support & Resources

### Render Documentation
- Main Docs: https://render.com/docs
- Docker Deploys: https://render.com/docs/docker
- Environment Variables: https://render.com/docs/environment-variables

### Application Support
- Check Admin panel logs in your deployed app
- Review build logs in Render dashboard
- Enable debug mode in Client view

### Community
- Render Community: https://community.render.com/
- Streamlit Forum: https://discuss.streamlit.io/

## Deployment Checklist

Before deploying to production:

- [ ] Code is in GitHub
- [ ] render.yaml is configured (or manual setup complete)
- [ ] OpenAI API key is ready
- [ ] Dockerfile is updated (new version)
- [ ] Environment variables are documented
- [ ] Disk size is adequate (10GB+ recommended)
- [ ] Health check is configured
- [ ] Test queries are prepared
- [ ] Monitoring is set up
- [ ] Backup strategy is planned
- [ ] Cost estimation is reviewed

## Success! 🎉

Your Labor Market RAG system should now be live on Render!

**Next Steps:**
1. Upload your data via Admin panel
2. Test with sample queries
3. Monitor performance and costs
4. Share the URL with your team
5. Set up regular backups

**Your deployed URL:**
```
https://your-service-name.onrender.com
```

Enjoy your production RAG system! 🚀
