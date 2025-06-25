# Chatbot System Architecture

This document outlines the proposed architecture for the NIC dynamic chatbot, designed to address general queries from a knowledge base and provide data visualizations from a database, adhering to the constraint of using only in-house API keys.

## High-Level Overview

The chatbot will consist of three main components:
1.  **Frontend:** A user-facing web interface for interaction.
2.  **Backend:** A server-side application handling business logic, API integrations, and data processing.
3.  **Data Storage:** Databases for the knowledge base and numerical data.

```mermaid
graph TD
    User[User] -->|Sends Query| Frontend[Frontend (React)]
    Frontend -->|API Request| Backend[Backend (Flask)]

    Backend -->|General Query| QueryRouter[Query Router/Intent Classifier]
    QueryRouter -->|Knowledge Base Query| KnowledgeBaseModule[Knowledge Base Module (RAG)]
    KnowledgeBaseModule -->|Retrieval| InHouseRAGAPI[NIC In-house RAG API]
    InHouseRAGAPI -->|Response| KnowledgeBaseModule
    KnowledgeBaseModule -->|Generated Answer| Backend

    QueryRouter -->|Database Query| DatabaseModule[Database Module]
    DatabaseModule -->|SQL Query| InHouseDatabaseAPI[NIC In-house Database API]
    InHouseDatabaseAPI -->|Data| DatabaseModule
    DatabaseModule -->|Visualization Request| VisualizationGenerator[Visualization Generator]
    VisualizationGenerator -->|Image| Backend

    Backend -->|Text/Image Response| Frontend
    Frontend -->|Displays Response| User

    subgraph Data Storage
        InHouseRAGAPI --- VectorDB[Vector Database (for Knowledge Base)]
        InHouseDatabaseAPI --- RelationalDB[Relational Database (for CSV data)]
    end

    DataLoading[Data Loading/Processing Scripts] --> VectorDB
    DataLoading --> RelationalDB
```

## Component Breakdown

### 1. Frontend (React)

*   **Purpose:** Provides the user interface for interacting with the chatbot.
*   **Key Features:**
    *   **Chat Interface:** A clean and intuitive chat window for users to type queries and view responses.
    *   **Response Display:** Renders text-based answers from the knowledge base and displays image-based visualizations for database queries.
    *   **Input Handling:** Captures user input and sends it to the backend API.
*   **Technology:** React.js (or a similar modern JavaScript framework).

### 2. Backend (Flask)

*   **Purpose:** The central hub for processing user requests, integrating with NIC's in-house APIs, and generating responses.
*   **Technology:** Flask (a lightweight Python web framework).
*   **Key Modules:**
    *   **API Endpoints:** Receives HTTP requests from the frontend and sends back responses.
    *   **Query Router/Intent Classifier:**
        *   **Functionality:** Analyzes incoming user queries to determine their intent (e.g., general knowledge question, database query for specific data, request for visualization).
        *   **Implementation (Initial):** Can start with simple keyword matching or rule-based classification. For more advanced capabilities, an in-house NLP model could be integrated here if available.
    *   **Knowledge Base Module (RAG - Retrieval Augmented Generation):**
        *   **Functionality:** Handles queries related to the `KnowledgeBase-DialogFlow.pdf`.
        *   **Integration:** Will interact with NIC's in-house RAG API. This API is assumed to handle:
            *   **Embedding:** Converting text (queries and knowledge base content) into numerical vectors.
            *   **Retrieval:** Searching a vector database (populated from the PDF) for relevant information chunks based on the query's embedding.
            *   **Generation:** Using an in-house Large Language Model (LLM) to synthesize a coherent answer from the retrieved information and the user's query.
        *   **Note for Beginner:** The complexity of RAG (embedding, vector database, LLM) is abstracted by assuming an existing in-house RAG API. If such an API is not available, this module would require significant development (e.g., using open-source embedding models like Sentence Transformers and a local vector database like FAISS or ChromaDB, and potentially a local open-source LLM if allowed for internal use).
    *   **Database Module:**
        *   **Functionality:** Processes queries requiring data from the `List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv`.
        *   **Integration:** Will interact with NIC's in-house Database API. This API is assumed to handle:
            *   **Text-to-SQL (or similar):** Translating natural language queries into database-understandable commands (e.g., SQL queries).
            *   **Data Retrieval:** Executing queries against the relational database and returning the results.
        *   **Note for Beginner:** The 


complexity of this module depends on the sophistication of the in-house Database API. If it's a simple API that returns raw data, the Flask backend will need to handle data parsing and filtering. If it's a more advanced API that can execute complex queries, the backend's role will be simpler.
    *   **Data Parsing/Processing:** Converts raw data from the database into a format suitable for visualization or direct response.
    *   **Visualization Generator:**
        *   **Functionality:** Creates visual representations (graphs) of numerical data.
        *   **Technology:** Python libraries like `Matplotlib` or `Seaborn` are excellent choices for generating static image files of graphs.
        *   **Output:** Generated images will be sent back to the frontend.
        *   **Note for Beginner:** This module will require careful mapping of user requests to specific data columns and chart types (e.g., 'show me the estimated cost by sanction year' -> bar chart of 'Estimated cost' vs 'Sanction Year').

### 3. Data Storage

*   **Purpose:** Stores the knowledge base content and the numerical scheme data.
*   **Components:**
    *   **Vector Database (for Knowledge Base):**
        *   **Content:** Embeddings of the `KnowledgeBase-DialogFlow.pdf` content.
        *   **Access:** Accessed via NIC's in-house RAG API.
        *   **Note for Beginner:** You won't directly interact with this database; the RAG API handles it.
    *   **Relational Database (for CSV data):**
        *   **Content:** Data from `List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv`.
        *   **Access:** Accessed via NIC's in-house Database API.
        *   **Note for Beginner:** You won't directly interact with this database; the Database API handles it. For local development, you might use a simple SQLite database to simulate this if the in-house API isn't immediately available.

## Data Loading and Processing

*   **Knowledge Base:**
    *   The `KnowledgeBase-DialogFlow.pdf` will need to be processed (as already done by converting to text) and then fed into the NIC in-house RAG API for embedding and indexing into their vector database. This process is typically handled by the RAG API's ingestion pipeline.
    *   **Your Role:** Ensure the PDF content is in a format acceptable by the RAG API and understand how to trigger its ingestion process.
*   **Numerical Data:**
    *   The `List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv` will need to be loaded into the relational database. This can be done via a script that uses the NIC in-house Database API to insert data.
    *   **Your Role:** Write a Python script to read the CSV and push the data to the database using the provided API. This script will also handle daily updates.

## In-house API Keys and Usage

*   **Crucial Point:** Since you have in-house API keys, you will need to get the documentation for these APIs from NIC. This documentation will specify:
    *   **API Endpoints:** The URLs to which you send requests.
    *   **Authentication:** How to use your API keys (e.g., in headers, as query parameters).
    *   **Request/Response Formats:** The expected JSON or other data structures for sending requests and receiving responses.
    *   **Rate Limits:** Any restrictions on how often you can call the APIs.
*   **Where you can get stuck:** Without this documentation, you cannot proceed with integrating the in-house APIs. This is the most critical dependency.

## Local Deployment

*   **Frontend:** The React application will be built into static files (HTML, CSS, JavaScript) and served by the Flask backend or a simple web server (e.g., Nginx, Apache) for local testing.
*   **Backend:** The Flask application will run as a Python process on your local machine.
*   **Simulating In-house APIs (if needed):** If the actual in-house APIs are not accessible during local development, you might need to create mock APIs or local data stores (e.g., SQLite for the database, a simple text file for RAG responses) to simulate their behavior. This will allow you to develop and test the frontend and backend independently.

## Next Steps

1.  **Obtain In-house API Documentation:** This is the absolute first step. Without it, further development is blocked.
2.  **Set up Local Development Environment:** Install Python, Node.js, and necessary package managers (pip, npm/yarn).
3.  **Backend Development (Flask):** Start by creating a basic Flask app and defining API endpoints.
4.  **Frontend Development (React):** Begin with the chat interface and integrate with the Flask backend.
5.  **Data Loading Scripts:** Develop scripts to load your CSV data into a local database (or simulate the in-house API interaction).
6.  **Integration and Testing:** Connect all components and thoroughly test the chatbot's functionality.

This architecture provides a clear roadmap. The success of this project heavily relies on the availability and understanding of NIC's in-house API documentation.

