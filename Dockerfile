# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data during build
RUN python -c "import nltk; \
    nltk.download('punkt', quiet=True); \
    nltk.download('wordnet', quiet=True); \
    nltk.download('stopwords', quiet=True); \
    nltk.download('averaged_perceptron_tagger', quiet=True)"

# Copy application code
COPY . .

# Create data directory for ChromaDB persistence
RUN mkdir -p /data/chroma_db && chmod -R 777 /data

# Create .streamlit directory for config
RUN mkdir -p /root/.streamlit

# Create Streamlit config for Render
RUN echo "\
[server]\n\
port = 8501\n\
address = '0.0.0.0'\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
\n\
[theme]\n\
base = 'light'\n\
" > /root/.streamlit/config.toml

# Expose port (Render will override this with PORT env var)
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Run the application
# Render sets PORT env var, so we use it if available, otherwise default to 8501
CMD streamlit run app/main.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true
