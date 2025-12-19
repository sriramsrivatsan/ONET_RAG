# Deployment Guide - Labor Market RAG System

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Render Deployment](#render-deployment)
4. [Production Considerations](#production-considerations)
5. [Troubleshooting](#troubleshooting)

## Local Development

### Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Secrets

Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-openai-api-key-here"
```

Or create `.env`:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 3: Run Application

```bash
streamlit run app/main.py
```

Access at: `http://localhost:8501`

### Step 4: Upload Data

1. Go to Admin panel
2. Upload `data/data.csv`
3. Click "Start Ingestion Pipeline"
4. Wait for completion (~2-5 minutes depending on data size)

### Step 5: Query the System

1. Switch to Client view
2. Enter your questions
3. Review results and download CSVs as needed

## Docker Deployment

### Build Image

```bash
docker build -t labor-rag:latest .
```

### Run Container

```bash
docker run -d \
  --name labor-rag \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your-key-here \
  -v $(pwd)/data:/data \
  labor-rag:latest
```

### Access Application

Open: `http://localhost:8501`

### View Logs

```bash
docker logs -f labor-rag
```

### Stop Container

```bash
docker stop labor-rag
docker rm labor-rag
```

## Render Deployment

**📘 For detailed Render deployment instructions, see [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)**

The application includes:
- ✅ Optimized Dockerfile for Render
- ✅ render.yaml for automatic configuration
- ✅ Health check endpoints
- ✅ Dynamic PORT handling
- ✅ Persistent disk support

### Quick Start with Render

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Render Blueprint**
   - Go to https://render.com
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render auto-configures from render.yaml

3. **Set API Key**
   - Add `OPENAI_API_KEY` in environment variables
   - Deploy!

4. **Access Your App**
   - URL: `https://your-service.onrender.com`
   - Upload data via Admin panel
   - Start querying!

For complete instructions including troubleshooting, monitoring, and advanced features, see **RENDER_DEPLOYMENT.md**.

### Method 2: Native Deployment

1. **Create Web Service**
   - Connect repository
   - Runtime: Python 3

2. **Build Command**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Command**
   ```bash
   streamlit run app/main.py --server.port=$PORT --server.address=0.0.0.0
   ```

4. **Environment Variables**
   - `OPENAI_API_KEY`: Your API key
   - `PYTHON_VERSION`: 3.10.0

## Production Considerations

### Performance Optimization

1. **Memory Management**
   - Monitor memory usage in Admin panel
   - Adjust `EMBEDDING_BATCH_SIZE` if needed
   - Enable persistence to avoid re-indexing

2. **Scaling**
   - For >100K rows, consider:
     - Increasing instance size
     - Using sampling for clustering
     - Implementing pagination

3. **Caching**
   - Streamlit caches embeddings automatically
   - ChromaDB persists index to disk
   - Consider Redis for query caching (advanced)

### Security

1. **API Key Protection**
   - Never commit API keys to version control
   - Use environment variables or secrets management
   - Rotate keys regularly

2. **Access Control**
   - Consider adding authentication (Streamlit Cloud has built-in auth)
   - Use HTTPS in production
   - Implement rate limiting for API calls

3. **Data Privacy**
   - Be mindful of sensitive labor market data
   - Consider data encryption at rest
   - Review ChromaDB security settings

### Monitoring

1. **Application Monitoring**
   - Check Admin panel system status regularly
   - Monitor memory and disk usage
   - Review system logs for errors

2. **Performance Metrics**
   - Track query response times
   - Monitor OpenAI API usage and costs
   - Log retrieval accuracy

3. **Alerting**
   - Set up alerts for high memory usage
   - Monitor for API errors
   - Track system availability

### Cost Management

1. **OpenAI API Costs**
   - Monitor token usage in Admin panel
   - Use gpt-4o-mini for cost efficiency
   - Implement caching for common queries
   - Set usage limits in OpenAI dashboard

2. **Infrastructure Costs**
   - Start with smaller Render instances
   - Scale up based on actual usage
   - Use persistent storage wisely
   - Consider spot instances for dev/test

### Backup and Recovery

1. **Data Backup**
   ```bash
   # Backup ChromaDB
   docker cp labor-rag:/data/chroma_db ./backup/chroma_db
   
   # Backup uploaded CSVs
   docker cp labor-rag:/data/data.csv ./backup/
   ```

2. **Restore Data**
   ```bash
   # Restore ChromaDB
   docker cp ./backup/chroma_db labor-rag:/data/
   ```

3. **Disaster Recovery**
   - Keep CSV files in version control or S3
   - Document data ingestion process
   - Test recovery procedures regularly

## Troubleshooting

### Common Issues

#### 1. "OpenAI API key not configured"
**Solution:**
- Verify environment variable is set
- Check Streamlit secrets.toml
- Restart application after setting key

#### 2. "Memory Error during indexing"
**Solutions:**
- Reduce batch size in config
- Use smaller dataset for testing
- Upgrade instance RAM
- Enable swap memory

#### 3. "ChromaDB persistence error"
**Solutions:**
- Check disk space availability
- Verify write permissions on /data
- Clear old ChromaDB data
- Restart container

#### 4. "Slow query responses"
**Solutions:**
- Reduce k_results parameter
- Check system resources
- Optimize ChromaDB settings
- Consider caching layer

#### 5. "Container crashes on startup"
**Solutions:**
- Check logs: `docker logs labor-rag`
- Verify all dependencies installed
- Check port availability
- Review Docker resource limits

### Debug Mode

Enable detailed logging:
```python
# In app/utils/logging.py
logger = RAGLogger(level=logging.DEBUG)
```

### Health Checks

**Application Health:**
```bash
curl http://localhost:8501/_stcore/health
```

**Vector Store Health:**
- Check Admin panel → System Status
- Verify document count > 0
- Test a simple query

### Performance Tuning

**For Large Datasets (>50K rows):**
```python
# In app/utils/config.py
EMBEDDING_BATCH_SIZE = 16  # Reduce from 32
CLUSTERING_SAMPLE_SIZE = 5000  # Reduce from 10000
```

**For Fast Queries:**
```python
DEFAULT_TOP_K = 5  # Reduce from 10
```

### Support Resources

- **System Logs**: Admin panel → System Logs
- **Debug Info**: Client view → Enable "Show Debug Info"
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Streamlit Docs**: https://docs.streamlit.io/

## Maintenance

### Regular Tasks

**Weekly:**
- Review system logs for errors
- Check memory usage trends
- Monitor API costs

**Monthly:**
- Update dependencies: `pip install -U -r requirements.txt`
- Review and optimize slow queries
- Backup ChromaDB data

**Quarterly:**
- Security audit
- Performance benchmarking
- User feedback review

### Updating the System

1. **Update Code:**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   streamlit run app/main.py
   ```

2. **Update Docker Image:**
   ```bash
   docker build -t labor-rag:latest .
   docker stop labor-rag
   docker rm labor-rag
   docker run -d ... labor-rag:latest
   ```

3. **Update on Render:**
   - Push to GitHub
   - Render auto-deploys from main branch
   - Or manually trigger deployment

---

**Need Help?** Check the Admin panel logs or review the README.md for additional guidance.
