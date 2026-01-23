#!/bin/bash
echo "Testing Abuse Detection API..."
echo "=============================="

# Start API in background
echo "Starting API..."
uvicorn api.app:app --reload --port 8000 &
API_PID=$!
sleep 3  # Give API time to start

echo ""
echo "1. Testing health endpoint:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "2. Testing metrics endpoint:"
curl -s http://localhost:8000/metrics | python3 -m json.tool

echo ""
echo "3. Testing prediction endpoint:"
curl -s -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello world", "I hate you", "Good morning"]}' \
  | python3 -m json.tool

echo ""
echo "4. Testing batch endpoint with sample CSV:"
cat > test_sample.csv << 'CSVEOF'
text
"This is a test"
"Hello there"
"Bad content alert"
CSVEOF

curl -s -X POST "http://localhost:8000/batch" \
  -F "file=@test_sample.csv" \
  -o batch_output.csv

echo "Batch results saved to batch_output.csv"
cat batch_output.csv

echo ""
echo "Cleaning up..."
kill $API_PID
rm -f test_sample.csv batch_output.csv

echo "Test completed!"
