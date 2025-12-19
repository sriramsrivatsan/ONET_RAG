# Project Structure - Labor RAG System

This document provides a detailed explanation of the project architecture, file organization, and component relationships.

## Directory Tree

```
labor-rag/
│
├── .streamlit/
│   ├── config.toml              # Streamlit app configuration
│   └── secrets.toml.example     # Template for API keys
│
├── app/
│   ├── main.py                  # Application entry point
│   │
│   ├── ui/                      # User Interface Components
│   │   ├── __init__.py
│   │   ├── admin.py             # Admin panel for data management
│   │   └── client.py            # Analyst query interface
│   │
│   ├── ingestion/               # Data Ingestion Pipeline
│   │   ├── __init__.py
│   │   ├── csv_loader.py        # CSV loading and inspection
│   │   ├── preprocessing.py     # Text normalization & cleaning
│   │   └── validation.py        # Data quality validation
│   │
│   ├── analytics/               # Computational Intelligence Layer
│   │   ├── __init__.py
│   │   ├── aggregations.py      # Pre-computed analytics
│   │   ├── clustering.py        # K-Means clustering engine
│   │   └── similarity.py        # Cross-industry similarity
│   │
│   ├── rag/                     # Retrieval-Augmented Generation
│   │   ├── __init__.py
│   │   ├── vector_store.py      # ChromaDB wrapper
│   │   ├── retriever.py         # Hybrid retrieval logic
│   │   └── hybrid_router.py     # Query intent classification
│   │
│   ├── llm/                     # LLM Integration
│   │   ├── __init__.py
│   │   ├── prompt_templates.py  # Prompt engineering templates
│   │   └── response_builder.py  # OpenAI response generation
│   │
│   └── utils/                   # Shared Utilities
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── logging.py           # Structured logging
│       └── helpers.py           # Helper functions
│
├── data/                        # Data Directory
│   ├── data.csv                 # Sample ONET dataset
│   ├── q.txt                    # Sample evaluation questions
│   └── chroma_db/               # ChromaDB persistence (created at runtime)
│
├── .dockerignore                # Docker ignore rules
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── DEPLOYMENT.md                # Deployment guide
├── Dockerfile                   # Docker container definition
├── README.md                    # Main documentation
├── requirements.txt             # Python dependencies
├── start.sh                     # Quick start script
└── validate.py                  # System validation script
```

## Component Architecture

### 1. Entry Point (`app/main.py`)

**Purpose**: Application initialization and routing

**Responsibilities**:
- Configure Streamlit page settings
- Initialize session state
- Manage navigation between views
- Display sidebar with system status

**Key Functions**:
- `initialize_session_state()`: Setup application state
- `show_sidebar()`: Display navigation and system info
- `main()`: Application entry point

### 2. User Interface Layer (`app/ui/`)

#### Admin Panel (`admin.py`)

**Purpose**: System administration and data management

**Components**:
- System Status Dashboard
  - Memory usage
  - Vector DB status
  - Dataset information
  - Last ingestion time

- Data Ingestion Interface
  - CSV file upload
  - Validation options
  - Processing controls (clustering, indexing)

- Vector Database Management
  - Collection statistics
  - Reset functionality

- System Logs
  - Filterable log viewer
  - Log export functionality

#### Client View (`client.py`)

**Purpose**: Analyst query interface

**Components**:
- Natural Language Query Interface
  - Text input with sample questions
  - Query settings (k_results, debug options)
  - Real-time analysis

- Quick Insights Dashboard
  - Key metrics (industries, occupations, employment, wages)
  - Top industries visualization

- Advanced Analytics
  - Employment analysis charts
  - Cluster explorer
  - Similarity analysis

### 3. Ingestion Pipeline (`app/ingestion/`)

#### CSV Loader (`csv_loader.py`)

**Purpose**: Load and inspect CSV files

**Key Features**:
- Dynamic schema detection
- Missing value analysis
- Data type identification
- Cardinality analysis
- Text field detection

**Main Class**: `CSVLoader`
- `load()`: Load CSV from file
- `_inspect_dataset()`: Analyze dataset structure
- `get_metadata()`: Retrieve inspection results

#### Preprocessing (`preprocessing.py`)

**Purpose**: Text normalization and field handling

**Key Features**:
- Text cleaning and lowercasing
- Tokenization (NLTK-based with fallback)
- Stopword removal (preserving domain terms)
- Multi-value field splitting
- Deduplication

**Main Classes**:
- `TextPreprocessor`: Text normalization utilities
- `DataNormalizer`: Dataset-level preprocessing

**Processing Steps**:
1. Handle missing values
2. Normalize text fields
3. Split multi-value fields
4. Normalize numeric fields
5. Create combined text for embeddings

#### Validation (`validation.py`)

**Purpose**: Data quality assurance

**Key Features**:
- Required column validation
- Data quality metrics
- Duplicate detection
- Missing value analysis

**Main Class**: `DataValidator`
- `validate()`: Run all validation checks
- `get_validation_summary()`: Human-readable report

### 4. Analytics Layer (`app/analytics/`)

#### Aggregation Engine (`aggregations.py`)

**Purpose**: Pre-compute analytical results

**Aggregations**:
- Occupation counts by industry
- Task frequency analysis
- Role distributions
- Activity distributions
- Employment statistics (total, by industry)
- Wage statistics (mean, median, by industry)
- Time analysis (hours per task/week)
- Industry and occupation statistics

**Main Class**: `AggregationEngine`
- `compute_all()`: Calculate all aggregations
- `query_aggregation()`: Retrieve specific aggregation

#### Clustering Engine (`clustering.py`)

**Purpose**: Group similar items to reduce hallucinations

**Clustering Strategy**:
- **Algorithm**: K-Means (or MiniBatchKMeans for large data)
- **Vectorization**: TF-IDF
- **Dimensionality Reduction**: Optional PCA
- **Separate Clustering**: Tasks, Functions, Occupations

**Process**:
1. Extract text (tasks/activities/occupations)
2. Sample if dataset too large (>100k rows)
3. TF-IDF vectorization
4. Apply PCA if needed
5. K-Means clustering
6. Generate human-readable labels
7. Assign cluster IDs to data

**Main Class**: `ClusteringEngine`
- `cluster_all()`: Apply clustering to all fields
- `_generate_cluster_labels()`: Create descriptive labels

#### Similarity Analyzer (`similarity.py`)

**Purpose**: Cross-industry similarity analysis

**Analysis Types**:
- Task similarity across industries (TF-IDF + cosine similarity)
- Common task identification
- Occupation overlap detection
- Transferable skills analysis

**Main Class**: `SimilarityAnalyzer`
- `analyze_cross_industry_tasks()`: Compute similarity matrix
- `find_common_tasks()`: Identify shared tasks
- `analyze_occupation_overlap()`: Find common occupations

### 5. RAG Layer (`app/rag/`)

#### Vector Store (`vector_store.py`)

**Purpose**: ChromaDB wrapper for semantic search

**Key Features**:
- Persistent or in-memory mode
- Batch document addition
- Metadata filtering
- Similarity search
- Collection management

**Main Class**: `VectorStore`
- `create_collection()`: Initialize collection
- `add_documents()`: Index documents with metadata
- `search()`: Semantic search with filters
- `get_stats()`: Collection statistics

#### Retriever (`retriever.py`)

**Purpose**: Hybrid retrieval combining semantic and computational

**Retrieval Modes**:
- **Semantic**: Vector similarity search
- **Computational**: Pre-computed aggregations
- **Hybrid**: Combined retrieval with ranking

**Computational Query Types**:
- `occupation_count`: Occupation counts by industry
- `industry_employment`: Employment statistics
- `task_frequency`: Task frequency analysis
- `wage_stats`: Wage statistics
- `top_occupations`: Top occupations by employment
- `cluster_info`: Cluster information

**Main Class**: `HybridRetriever`
- `retrieve_semantic()`: Vector search
- `retrieve_computational()`: Analytical queries
- `retrieve_hybrid()`: Combined retrieval

#### Hybrid Router (`hybrid_router.py`)

**Purpose**: Query intent classification and routing

**Intent Classification**:
- **Computational**: Counts, totals, rankings, statistics
- **Semantic**: Explanations, similarities, descriptions
- **Hybrid**: Both computational and semantic

**Pattern Recognition**:
- Regex-based intent matching
- Parameter extraction (industry, limits)
- Filter identification
- Context analysis

**Special Handlers**:
- Digital document queries
- Agentic solution queries

**Main Class**: `HybridRouter`
- `classify_intent()`: Determine query type
- `extract_computational_params()`: Extract parameters
- `route_query()`: Full routing pipeline
- `get_query_context()`: Extract contextual information

### 6. LLM Layer (`app/llm/`)

#### Prompt Templates (`prompt_templates.py`)

**Purpose**: Structured prompts for LLM

**Templates**:
- `SYSTEM_PROMPT`: Base system instructions
- `HYBRID_QUERY_PROMPT`: For hybrid queries
- `SEMANTIC_QUERY_PROMPT`: For semantic queries
- `COMPUTATIONAL_QUERY_PROMPT`: For analytical queries
- `DIGITAL_DOCUMENT_QUERY_PROMPT`: For document creation queries
- `AGENTIC_SOLUTION_QUERY_PROMPT`: For AI agent queries
- `GROUNDING_INSTRUCTION`: Critical grounding rules

**Key Principles**:
- Stay grounded in data
- Explicit citations
- Clear separation of inferred knowledge
- Conservative external knowledge use

#### Response Builder (`response_builder.py`)

**Purpose**: Generate LLM-based responses

**Key Features**:
- OpenAI API integration
- Context-aware prompt selection
- Response formatting
- CSV generation
- Summary generation

**Main Class**: `ResponseBuilder`
- `build_response()`: Generate response based on intent
- `_call_llm()`: OpenAI API wrapper
- `format_as_csv()`: Export data as CSV

### 7. Utilities (`app/utils/`)

#### Configuration (`config.py`)

**Purpose**: Centralized configuration management

**Configuration Categories**:
- API settings (OpenAI keys, models)
- Vector DB settings (ChromaDB paths, collection names)
- Clustering parameters
- Processing limits
- Query defaults
- UI settings

#### Logging (`logging.py`)

**Purpose**: Structured logging system

**Features**:
- Console and buffered output
- Memory-based log buffer
- UI integration
- Log filtering and export

**Components**:
- `BufferedHandler`: Custom log handler
- `setup_logger()`: Logger initialization
- `get_logs()`: Retrieve logs
- `export_logs()`: Save logs to file

#### Helpers (`helpers.py`)

**Purpose**: Shared utility functions

**Utilities**:
- Memory management
- DataFrame hashing
- Safe division
- List batching
- Text cleaning
- Numeric extraction
- Number formatting
- Time/cost savings calculations

## Data Flow

### Ingestion Flow
```
CSV Upload → Validation → Normalization → Aggregation → Clustering → Indexing
```

### Query Flow
```
User Query → Intent Classification → Hybrid Retrieval → LLM Response → Display
```

### Detailed Query Processing
```
1. User enters query
2. HybridRouter classifies intent (semantic/computational/hybrid)
3. HybridRouter extracts parameters and context
4. HybridRetriever executes appropriate retrieval:
   - Semantic: VectorStore.search()
   - Computational: AggregationEngine queries
   - Hybrid: Both
5. ResponseBuilder generates response using OpenAI
6. Response displayed to user with optional:
   - Retrieved documents
   - Debug information
   - CSV export
```

## Session State Management

Streamlit session state stores:
- `current_view`: Active view (admin/client)
- `vector_store`: ChromaDB instance
- `processed_df`: Normalized DataFrame
- `aggregations`: Pre-computed analytics
- `cluster_metadata`: Cluster information
- `similarity_results`: Similarity analysis
- `last_ingestion_time`: Ingestion timestamp
- `current_query`: Active query
- `hybrid_router`: Router instance
- `response_builder`: LLM builder instance

## Extension Points

### Adding New Query Types

1. **Add pattern to HybridRouter**
```python
# hybrid_router.py
NEW_PATTERN = r'\byour_pattern\b'
COMPUTATIONAL_PATTERNS.append(NEW_PATTERN)
```

2. **Add computational query handler**
```python
# retriever.py
def _get_your_analysis(self, params):
    # Implementation
    return results
```

3. **Add prompt template**
```python
# prompt_templates.py
YOUR_QUERY_PROMPT = """..."""
```

### Adding New Aggregations

1. **Add aggregation method**
```python
# aggregations.py
def _your_aggregation(self, df):
    # Implementation
    return results
```

2. **Add to compute_all()**
```python
self.aggregations['your_analysis'] = self._your_aggregation(df)
```

### Customizing Clustering

Adjust parameters in `config.py`:
```python
N_TASK_CLUSTERS = 20  # Increase cluster count
USE_PCA = False       # Disable PCA
```

## Best Practices

### Code Organization
- Keep components focused and single-purpose
- Use type hints for clarity
- Document complex logic
- Handle errors gracefully

### Performance
- Use caching for expensive operations
- Batch process when possible
- Monitor memory usage
- Use sampling for large datasets

### Data Grounding
- Always cite sources
- Label external knowledge explicitly
- Stay conservative with inferences
- Validate against dataset

### Testing
- Run `validate.py` after changes
- Test with sample questions from `q.txt`
- Monitor logs for errors
- Check memory usage

---

**For Questions**: Refer to README.md and DEPLOYMENT.md

**Last Updated**: December 2024
