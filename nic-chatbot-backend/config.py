# NIC Chatbot Backend Configuration

# This file contains configuration settings for the NIC chatbot backend.
# You will need to update these settings with your actual in-house API credentials and endpoints.

## In-house API Configuration

### RAG API Configuration
# Replace these with your actual NIC RAG API details if you have a dedicated RAG API endpoint.
# Otherwise, the Langchain RAG setup in src/routes/chatbot.py handles this internally.
RAG_API_ENDPOINT = "http://10.197.112.27:10022/docs#/default/rag_inference_rag_inference_post" # Placeholder
RAG_API_KEY = "rag_inference_rag_inference_post" # Placeholder

### Database API Configuration  
# Replace these with your actual NIC Database API details if you have a dedicated Database API endpoint.
# Otherwise, the chatbot directly queries the local SQLite database.
DATABASE_API_ENDPOINT = "https://your-nic-database-api.gov.in/api/v1/query" # Placeholder
DATABASE_API_KEY = "your-database-api-key-here" # Placeholder

## Important Notes for Implementation:

1. **API Keys Security**: 
   - Never commit actual API keys to version control
   - Use environment variables in production
   - Consider using a secrets management system

2. **API Integration Steps**:
   - Get the actual API documentation from NIC
   - Update the endpoint URLs above
   - Replace the mock functions in chatbot.py with real API calls
   - Test authentication and response formats

3. **Error Handling**:
   - Implement proper error handling for API failures
   - Add retry logic for transient failures
   - Log API responses for debugging

4. **Rate Limiting**:
   - Check if the APIs have rate limits
   - Implement appropriate throttling if needed

## Visualization Settings
CHART_WIDTH = 10
CHART_HEIGHT = 6
CHART_DPI = 150
