# Labor Market RAG - Hybrid Retrieval-Augmented Generation System

A production-ready Hybrid RAG system for labor market intelligence, combining semantic search with computational analytics to answer complex queries about occupations, industries, tasks, and employment data.

## 🎯 Features

### Core Capabilities
- **Hybrid Retrieval**: Combines semantic search (vector similarity) with computational analytics
- **Semantic Search**: ChromaDB-powered vector search with sentence transformers
- **Computational Analytics**: Pandas-based aggregations, groupings, and statistical analysis
- **Intelligent Routing**: Automatic query classification (semantic/computational/hybrid)
- **Clustering**: K-Means clustering of tasks, roles, and occupations to reduce hallucinations
- **Cross-Industry Analysis**: Similarity detection and comparison across industries
- **Explainable Responses**: Clear attribution of data sources with separated external insights

### User Interfaces
- **Client View**: Analyst interface for natural language queries
- **Admin View**: System management, data ingestion, and monitoring

## 📁 Project Structure

```
labor-rag/
│
├── app/
│   ├── main.py                 # Streamlit application entry point
│   │
│   ├── ui/
│   │   ├── admin.py             # Admin panel UI
│   │   └── client.py            # Client query interface
│   │
│   ├── ingestion/
│   │   ├── csv_loader.py        # CSV loading and validation
│   │   └── preprocessing.py     # Data preprocessing and normalization
│   │
│   ├── analytics/
│   │   ├── aggregations.py      # Computational analytics
│   │   ├── clustering.py        # K-Means clustering
│   │   └── similarity.py        # Cross-industry similarity
│   │
│   ├── rag/
│   │   ├── vector_store.py      # ChromaDB wrapper
│   │   ├── retriever.py         # Hybrid retriever
│   │   └── hybrid_router.py     # Query intent classification
│   │
│   ├── llm/
│   │   ├── prompt_templates.py  # LLM prompts
│   │   └── response_builder.py  # OpenAI integration
│   │
│   └── utils/
│       ├── config.py            # Configuration management
│       ├── logging.py           # Logging utilities
│       └── helpers.py           # Helper functions
│
├── data/
│   └── (place your data.csv here)
│
├── Dockerfile
├── requirements.txt
├── README.md
└── .env.example
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key
- 4GB+ RAM recommended
- 2GB+ disk space for vector index

### Installation

1. **Clone or download the repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Or use Streamlit secrets:
```bash
mkdir -p ~/.streamlit
echo "OPENAI_API_KEY = 'your-key-here'" > ~/.streamlit/secrets.toml
```

4. **Run the application**
```bash
streamlit run app/main.py
```

## 🐳 Docker Deployment

### Build and Run with Docker

```bash
# Build the image
docker build -t labor-rag:latest .

# Run the container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your-key-here \
  -v $(pwd)/data:/data \
  labor-rag:latest
```

### Deploy to Render

1. **Create a new Web Service on Render**
2. **Connect your Git repository**
3. **Configure the service:**
   - Build Command: `docker build -t labor-rag .`
   - Start Command: (use Dockerfile CMD)
   - Add environment variable: `OPENAI_API_KEY`
4. **Deploy**

## 📊 Using the System

### Admin Panel (Data Ingestion)

1. Navigate to **Admin (System)** view in the sidebar
2. Upload your ONET labor market CSV file
3. Click **Start Ingestion Pipeline**
4. Wait for processing to complete (shows progress for 6 steps):
   - CSV loading
   - Validation
   - Preprocessing
   - Aggregation computation
   - Clustering
   - Vector indexing

### Client Interface (Querying)

1. Navigate to **Client (Analyst)** view
2. Enter your natural language question
3. Adjust retrieval settings if needed
4. Click **Analyze Query**
5. View results and download CSV if applicable

### Sample Queries

**Digital Document Creation:**
- "What jobs require creating digital documents?"
- "What's the total employment of workers who create digital documents?"
- "Which industries are rich in digital document users?"
- "Give me a CSV of total employment by industry for digital document creators"

**AI Agent Impact Analysis:**
- "What jobs could benefit from a customer service AI agent?"
- "How much time could an AI agent save per week?"
- "What's the dollar savings this solution could achieve?"
- "Show me the top 10 occupations that could save the most time"

**General Labor Market:**
- "Which industries have the highest employment?"
- "Compare task requirements across Healthcare and Technology"
- "What occupations require the most diverse skill sets?"

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `CHROMA_PERSIST_PATH` - Path for ChromaDB persistence (default: `/data/chroma_db`)
- `ENABLE_PERSISTENCE` - Enable persistent storage (default: `true`)
- `EMBEDDING_MODEL` - Sentence transformer model (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `LLM_MODEL` - OpenAI model (default: `gpt-4o-mini`)

### System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 2GB disk space

**Recommended:**
- 4+ CPU cores
- 8GB RAM
- 5GB disk space

## 📈 System Architecture

### Data Flow

1. **Ingestion Pipeline**
   ```
   CSV Upload → Validation → Preprocessing → Clustering → Vector Indexing
   ```

2. **Query Processing**
   ```
   User Query → Intent Classification → Hybrid Retrieval → LLM Synthesis → Response
   ```

### Hybrid Retrieval Strategy

The system intelligently combines:

- **Semantic Search**: Vector similarity for conceptual queries
- **Computational Queries**: Pandas operations for numerical/statistical queries
- **Hybrid Fusion**: Both approaches for complex queries

Query routing is automatic based on keyword analysis.

### Clustering for Hallucination Reduction

The system clusters:
- **Tasks** (15 clusters)
- **Work Activities** (10 clusters)
- **Occupations** (20 clusters)

This provides:
- Semantic grouping for better retrieval
- Cross-industry similarity detection
- Reduced hallucinations through structured categorization

## 🔍 Key Components

### Vector Store (ChromaDB)
- Persistent storage of document embeddings
- Fast semantic similarity search
- Metadata filtering capabilities

### Hybrid Router
- Classifies query intent (semantic/computational/hybrid)
- Extracts parameters (top N, aggregations, filters)
- Determines execution strategy

### Hybrid Retriever
- Orchestrates semantic and computational retrieval
- Filters and ranks results
- Prepares context for LLM

### Response Builder
- Formats retrieved context
- Generates LLM prompts
- Synthesizes final responses
- Separates external/inferred knowledge

## 🎓 Best Practices

### For Accurate Results
1. Upload complete, validated ONET data
2. Rebuild index when data changes significantly
3. Use specific questions rather than vague queries
4. Request CSV exports for numerical analysis
5. Check the debug panel for retrieval quality

### For Performance
1. Start with default k=10 for retrieval
2. Increase k for comprehensive queries
3. Monitor memory usage in Admin panel
4. Enable persistence for faster restarts

## 🐛 Troubleshooting

### "OpenAI API key not configured"
- Ensure `OPENAI_API_KEY` is set in environment or Streamlit secrets

### "Vector Store not initialized"
- Go to Admin panel and complete data ingestion

### High memory usage
- Reduce batch sizes in config
- Process smaller datasets
- Restart the application

### Slow queries
- Reduce k_results parameter
- Check system resources
- Consider upgrading hardware

## 📝 Data Format

Expected CSV columns:
- `Industry title` - Industry name
- `ONET job title` - Occupation title
- `Job description` - Job description text
- `Detailed work activities` - Semicolon-separated activities
- `Detailed job tasks` - Semicolon-separated tasks
- `Employment` - Number of employed workers
- `Hourly wage` - Average hourly wage
- `Hours per week spent on task` - Task time allocation

## 🤝 Contributing

This is a production-ready template. Customize as needed:
- Add new query types in `hybrid_router.py`
- Extend clustering in `clustering.py`
- Add visualizations in UI components
- Implement custom prompt templates

## 📄 License

This project is provided as-is for labor market analysis purposes.

## 🙏 Acknowledgments

Built with:
- Streamlit
- ChromaDB
- OpenAI GPT-4o-mini
- Sentence Transformers
- scikit-learn

---

**For questions or issues, please check the system logs in the Admin panel.**
