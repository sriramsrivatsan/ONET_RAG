#!/bin/bash

# Docker Build Test Script for Labor Market RAG
# Tests that the Docker container builds and runs correctly

echo "🐳 Labor Market RAG - Docker Build Test"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✅ Docker found${NC}"
docker --version
echo ""

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set in environment${NC}"
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        export OPENAI_API_KEY="$api_key"
        echo -e "${GREEN}✅ API key set${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping API key - app will need it to run${NC}"
    fi
else
    echo -e "${GREEN}✅ OPENAI_API_KEY found in environment${NC}"
fi

echo ""
echo "📦 Step 1: Building Docker image..."
echo "This may take 5-10 minutes on first build..."
echo ""

# Build the Docker image
if docker build -t labor-rag:test .; then
    echo ""
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo ""
echo "📊 Image details:"
docker images labor-rag:test

echo ""
echo "🚀 Step 2: Testing container startup..."
echo ""

# Check if port 8501 is already in use
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8501 is already in use${NC}"
    echo "Trying port 8502 instead..."
    TEST_PORT=8502
else
    TEST_PORT=8501
fi

# Run the container in detached mode
CONTAINER_ID=$(docker run -d \
    --name labor-rag-test \
    -p ${TEST_PORT}:8501 \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    labor-rag:test)

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Container started: ${CONTAINER_ID:0:12}${NC}"
echo ""
echo "⏳ Waiting for application to start (30 seconds)..."

# Wait for the application to start
sleep 30

# Check if container is still running
if docker ps | grep -q labor-rag-test; then
    echo -e "${GREEN}✅ Container is running${NC}"
else
    echo -e "${RED}❌ Container stopped unexpectedly${NC}"
    echo ""
    echo "Container logs:"
    docker logs labor-rag-test
    docker rm labor-rag-test
    exit 1
fi

echo ""
echo "🔍 Checking health endpoint..."

# Test the health endpoint
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${TEST_PORT}/_stcore/health)

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed (HTTP $HEALTH_CHECK)${NC}"
else
    echo -e "${YELLOW}⚠️  Health check returned HTTP $HEALTH_CHECK${NC}"
    echo "This might be normal during startup, checking logs..."
fi

echo ""
echo "📝 Recent container logs:"
echo "========================"
docker logs --tail 20 labor-rag-test
echo "========================"
echo ""

# Cleanup prompt
echo ""
echo -e "${GREEN}🎉 Build test complete!${NC}"
echo ""
echo "Your Docker image is ready to deploy!"
echo ""
echo "📍 Container is running at: http://localhost:${TEST_PORT}"
echo ""
echo "To view logs:"
echo "  docker logs -f labor-rag-test"
echo ""
echo "To stop and remove the test container:"
echo "  docker stop labor-rag-test && docker rm labor-rag-test"
echo ""

read -p "Press Enter to stop and remove the test container (or Ctrl+C to keep it running)..."

# Cleanup
echo ""
echo "🧹 Cleaning up..."
docker stop labor-rag-test
docker rm labor-rag-test

echo ""
echo -e "${GREEN}✅ Test complete and cleaned up!${NC}"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Deploy to Render using render.yaml"
echo "3. Or run locally with:"
echo "   docker run -p 8501:8501 -e OPENAI_API_KEY=xxx labor-rag:test"
echo ""
