# Getting Started - Labor Market RAG System

## 🎉 What You've Received

A complete, production-ready **Hybrid RAG System for Labor Market Intelligence** with:

✅ Semantic search using ChromaDB and sentence transformers  
✅ Computational analytics with Pandas aggregations  
✅ Intelligent query routing (semantic/computational/hybrid)  
✅ K-Means clustering to reduce hallucinations  
✅ Cross-industry similarity analysis  
✅ Two-mode UI (Admin + Client)  
✅ Docker containerization  
✅ Render deployment ready  
✅ Complete documentation  

## 📦 Package Contents

```
labor-rag/
├── app/                     # Application code
│   ├── main.py             # Entry point
│   ├── ui/                 # User interfaces
│   ├── ingestion/          # Data loading
│   ├── analytics/          # Clustering & analysis
│   ├── rag/                # Vector store & retrieval
│   ├── llm/                # OpenAI integration
│   └── utils/              # Utilities
├── data/
│   ├── data.csv            # Your ONET dataset
│   └── q.txt               # Sample questions
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
├── README.md              # Comprehensive guide
├── DEPLOYMENT.md          # Deployment instructions
├── PROJECT_SUMMARY.md     # Technical overview
├── start.sh               # Quick start (Unix)
├── start.bat              # Quick start (Windows)
├── .env.example           # Environment template
├── .gitignore             # Git exclusions
└── .dockerignore          # Docker exclusions
```

## 🚀 Quick Start (3 Steps)

### Option 1: Local Development (Recommended for First Try)

**Step 1: Install Dependencies**

```bash
# Unix/Mac
./start.sh

# Windows
start.bat

# Or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Step 2: Configure API Key**

Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-your-key-here"
```

**Step 3: Run Application**

```bash
streamlit run app/main.py
```

Then:
1. Open http://localhost:8501
2. Go to Admin panel
3. Upload `data/data.csv`
4. Click "Start Ingestion Pipeline"
5. Switch to Client view and start querying!

### Option 2: Docker (Clean Environment)

```bash
# Build
docker build -t labor-rag .

# Run
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  -v $(pwd)/data:/data \
  labor-rag

# Access
open http://localhost:8501
```

### Option 3: Render (Production Deployment)

1. Push code to GitHub
2. Create Render Web Service
3. Connect repository
4. Add environment variable: `OPENAI_API_KEY`
5. Deploy automatically
6. Access your deployed URL

See `DEPLOYMENT.md` for detailed instructions.

## 📖 Key Documentation

### For Users
- **README.md**: Complete usage guide, features, troubleshooting
- **Quick queries**: See Client interface "Sample Queries" section

### For Developers
- **PROJECT_SUMMARY.md**: Architecture, design decisions, technical details
- **Code comments**: Detailed inline documentation in all modules

### For DevOps
- **DEPLOYMENT.md**: Production deployment, monitoring, maintenance
- **Dockerfile**: Container configuration
- **.env.example**: Environment variables reference

## 🎯 Test the System

### Try These Sample Queries

1. **Digital Document Creation** (from q.txt):
   ```
   What jobs require creating digital documents as part of their work?
   ```

2. **Employment Analysis**:
   ```
   What's the total employment of workers that create digital documents?
   ```

3. **Industry Analysis**:
   ```
   What industries are rich in digital document users?
   ```

4. **CSV Export**:
   ```
   Give me a CSV of total employment by industry for digital document creators
   ```

5. **AI Agent Impact** (from q.txt):
   ```
   What jobs could benefit from a customer service AI agent?
   What's the dollar savings this solution could achieve?
   ```

## 🔍 Understanding the System

### Admin Panel (System Management)
- Upload and process ONET CSV files
- Monitor system status (memory, documents, health)
- View processing logs
- Check system information

### Client Interface (Analyst Queries)
- Ask natural language questions
- View structured answers with data citations
- Download results as CSV
- See quick insights and statistics

### How It Works
1. **Query Classification**: Determines if semantic, computational, or hybrid
2. **Hybrid Retrieval**: Searches vectors AND computes statistics
3. **LLM Synthesis**: Generates human-readable answers
4. **CSV Export**: Creates downloadable data (when requested)

## 🛠️ Customization

### Adjust Retrieval
```python
# In app/utils/config.py
DEFAULT_TOP_K = 10          # Documents to retrieve
SIMILARITY_THRESHOLD = 0.3   # Minimum similarity score
```

### Modify Clustering
```python
# In app/utils/config.py
N_CLUSTERS_TASKS = 15        # Task clusters
N_CLUSTERS_ROLES = 10        # Role clusters
N_CLUSTERS_OCCUPATIONS = 20  # Occupation clusters
```

### Change LLM Model
```python
# In app/utils/config.py
LLM_MODEL = "gpt-4o-mini"    # Or "gpt-4o" for better quality
```

### Add New Query Types
1. Edit `app/rag/hybrid_router.py` - Add query patterns
2. Edit `app/llm/prompt_templates.py` - Add specialized prompts
3. Edit `app/rag/retriever.py` - Add retrieval logic

## 🐛 Troubleshooting

### "OpenAI API key not configured"
→ Set `OPENAI_API_KEY` in environment or `.streamlit/secrets.toml`

### "Vector Store not initialized"
→ Go to Admin panel and upload data

### "High memory usage"
→ Reduce batch sizes in `app/utils/config.py`

### "Slow queries"
→ Reduce `DEFAULT_TOP_K` or check system resources

### More help
→ See `README.md` troubleshooting section  
→ Check Admin panel logs  
→ Enable debug mode in Client interface

## 📊 System Requirements

### Minimum
- Python 3.10+
- 4GB RAM
- 2GB disk space
- OpenAI API key

### Recommended
- 8GB RAM
- 5GB disk space
- SSD for faster indexing

## 💡 Pro Tips

1. **Start Small**: Test with a subset of data first (~1000 rows)
2. **Monitor Costs**: Check OpenAI usage dashboard regularly
3. **Use Persistence**: Enable ChromaDB persistence to avoid re-indexing
4. **Cache Queries**: Store common query results for faster responses
5. **Optimize K**: Use k=5 for fast queries, k=20 for comprehensive
6. **Review Logs**: Check Admin panel logs for optimization opportunities

## 🎓 Learn More

### Understanding RAG
- Semantic search: Vector similarity using embeddings
- Computational: Direct calculations on structured data
- Hybrid: Combines both for comprehensive answers

### Understanding Clustering
- Groups similar items (tasks, roles, occupations)
- Reduces hallucinations through structure
- Enables cross-sector insights

### Understanding the Pipeline
1. Upload CSV → Validate schema
2. Preprocess → Normalize text, split multi-values
3. Cluster → Group similar items
4. Index → Create vector embeddings
5. Query → Retrieve + Synthesize

## 🚀 Next Steps

1. **Deploy Locally**: Run `./start.sh` or `start.bat`
2. **Upload Data**: Use Admin panel to ingest your CSV
3. **Test Queries**: Try sample questions from q.txt
4. **Explore Features**: Check quick insights, debug mode
5. **Deploy to Production**: Follow DEPLOYMENT.md for Render
6. **Customize**: Adjust parameters for your use case

## 📞 Need Help?

1. Check **README.md** for detailed documentation
2. Review **PROJECT_SUMMARY.md** for architecture
3. See **DEPLOYMENT.md** for production setup
4. Check Admin panel logs for errors
5. Enable debug mode in Client view

## 🎉 You're Ready!

This is a complete, production-ready system. All components are:
- ✅ Fully implemented
- ✅ Tested and working
- ✅ Well-documented
- ✅ Ready to deploy

**Start with**: `./start.sh` or `start.bat`  
**First task**: Upload data in Admin panel  
**Then**: Ask questions in Client interface

Enjoy your Labor Market RAG System! 🚀
