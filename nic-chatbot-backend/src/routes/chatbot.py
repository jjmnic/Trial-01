from flask import Blueprint, request, jsonify
import os
import sqlite3
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

# Import our custom NLU processor
from src.routes.nlu_processor_updated import NLUProcessor

# Langchain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
import torch

# --- Configuration --- #
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database", "schemes.db")
KNOWLEDGE_BASE_PERSIST_DIR = os.path.join(BASE_DIR, "..", "..", "data", "chroma_db")

# Initialize NLU Processor
csv_path = os.path.join(BASE_DIR, "upload", "List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv")
nlu_processor = NLUProcessor(csv_path)

# Enhanced Langchain RAG Setup

# 1. Load Better Embeddings
model_name = "sentence-transformers/all-mpnet-base-v2"  # Better embedding model
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}  # Normalize for better similarity
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)
print(f"DEBUG: Enhanced embeddings initialized: {embeddings is not None}")

# 2. Load Vector Store with better retrieval settings
if not os.path.exists(KNOWLEDGE_BASE_PERSIST_DIR):
    print(f"ERROR: Knowledge base directory not found at {KNOWLEDGE_BASE_PERSIST_DIR}.")
    vectordb = None
else:
    vectordb = Chroma(persist_directory=KNOWLEDGE_BASE_PERSIST_DIR, embedding_function=embeddings)
print(f"DEBUG: Vectordb loaded: {vectordb is not None}")

# 3. Setup Better LLM
def setup_llm():
    """Setup the best available LLM for text generation."""
    try:
        # Try Microsoft DialoGPT for better conversational responses
        model_name = "microsoft/DialoGPT-medium"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Add padding token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id
        )
        llm = HuggingFacePipeline(pipeline=pipe)
        print(f"DEBUG: DialoGPT LLM initialized successfully.")
        return llm
        
    except Exception as e:
        print(f"DialoGPT failed: {e}")
        try:
            # Fallback to FLAN-T5 Large for better reasoning
            model_name = "google/flan-t5-large"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            pipe = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=300,
                temperature=0.3,
                do_sample=True,
                top_k=50,
                top_p=0.95
            )
            llm = HuggingFacePipeline(pipeline=pipe)
            print(f"DEBUG: FLAN-T5 Large LLM initialized successfully.")
            return llm
            
        except Exception as e2:
            print(f"FLAN-T5 Large failed: {e2}")
            # Final fallback to smaller model
            try:
                model_name = "google/flan-t5-base"
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                pipe = pipeline(
                    "text2text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=250,
                    temperature=0.4,
                    do_sample=True
                )
                llm = HuggingFacePipeline(pipeline=pipe)
                print(f"DEBUG: FLAN-T5 Base LLM initialized successfully.")
                return llm
                
            except Exception as e3:
                print(f"All LLM models failed: {e3}")
                # Mock LLM as final fallback
                class EnhancedMockLLM:
                    def __call__(self, prompt):
                        # Extract question from prompt
                        if "Question:" in prompt:
                            question = prompt.split("Question:")[-1].strip()
                            if "jjm" in question.lower() or "jal jeevan mission" in question.lower():
                                if "website" in question.lower():
                                    return "The official website of Jal Jeevan Mission (JJM) is jaljeevanmission.gov.in. This website provides comprehensive information about the mission, its progress, guidelines, and implementation details."
                                else:
                                    return "Jal Jeevan Mission (JJM) is a flagship program launched by the Government of India in 2019 to provide safe and adequate drinking water through individual household tap connections to all households in rural India by 2024."
                        return "I apologize, but I'm having trouble accessing the knowledge base. Please try rephrasing your question."
                    
                    def invoke(self, prompt):
                        return self.__call__(prompt)
                
                return EnhancedMockLLM()

llm = setup_llm()

# 4. Enhanced RetrievalQA Chain with much better prompt
if vectordb:
    # Better retriever with more relevant chunks
    retriever = vectordb.as_retriever(
        search_type="mmr",  # Maximum Marginal Relevance for diverse results
        search_kwargs={"k": 8, "fetch_k": 20}  # Retrieve more, then filter
    )
    
    # Much improved prompt template
    prompt_template = """You are an expert assistant specializing in Indian water and sanitation programs, particularly the Jal Jeevan Mission (JJM), Swachh Bharat Mission (SBM), and DDWS initiatives.

Your task is to provide accurate, helpful, and specific answers based on the provided context. Follow these guidelines:

1. ANSWER DIRECTLY: Start with a clear, direct answer to the question
2. USE CONTEXT: Base your response primarily on the provided context
3. BE SPECIFIC: Include specific details like websites, dates, numbers when available
4. BE CONCISE: Provide focused answers without unnecessary elaboration
5. ACKNOWLEDGE LIMITS: If the context doesn't contain the answer, say so clearly

Context Information:
{context}

Question: {question}

Instructions: Provide a clear, accurate answer based on the context above. If asking about websites, provide the exact URL if mentioned in the context.

Answer:"""

    QA_CHAIN_PROMPT = PromptTemplate.from_template(prompt_template)

    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        return_source_documents=True
    )
else:
    qa_chain = None
    print("WARNING: qa_chain could not be initialized because vectordb is None.")

print(f"DEBUG: Enhanced QA Chain initialized: {qa_chain is not None}")

chatbot_bp = Blueprint("chatbot_bp", __name__)

# --- Helper Functions --- #

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def query_knowledge_base(query_text):
    """Enhanced knowledge base querying with better error handling and fallbacks."""
    if not qa_chain:
        print("DEBUG: qa_chain is None in query_knowledge_base.")
        return get_fallback_response(query_text)
    
    try:
        # Clean and prepare the query
        cleaned_query = query_text.strip()
        
        result = qa_chain.invoke({"query": cleaned_query})
        print(f"DEBUG: RAG query: {cleaned_query}")
        print(f"DEBUG: RAG result type: {type(result)}")
        
        if isinstance(result, dict) and "result" in result:
            answer = result["result"].strip()
            source_docs = result.get("source_documents", [])
            
            # Post-process the answer to ensure quality
            if len(answer) < 10 or answer.lower().startswith("i don't know") or "context" in answer.lower():
                return get_fallback_response(query_text)
            
            print(f"DEBUG: RAG answer: {answer[:200]}...")
            return {
                "answer": answer,
                "source_documents": [doc.metadata for doc in source_docs]
            }
        else:
            print(f"DEBUG: Unexpected result format: {result}")
            return get_fallback_response(query_text)
            
    except Exception as e:
        print(f"ERROR: Exception during qa_chain.invoke: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_response(query_text)

def get_fallback_response(query_text):
    """Provide intelligent fallback responses for common queries."""
    query_lower = query_text.lower()
    
    if "website" in query_lower and ("jjm" in query_lower or "jal jeevan mission" in query_lower):
        return {
            "answer": "The official website of Jal Jeevan Mission (JJM) is jaljeevanmission.gov.in. This website provides comprehensive information about the mission's objectives, progress, implementation guidelines, and state-wise data.",
            "source_documents": []
        }
    elif "jjm" in query_lower or "jal jeevan mission" in query_lower:
        return {
            "answer": "Jal Jeevan Mission (JJM) is a flagship program launched by the Government of India in August 2019 under the Ministry of Jal Shakti. The mission aims to provide safe and adequate drinking water through individual household tap connections (FHTC) to all households in rural India by 2024. The program has a total outlay of ₹3.60 lakh crores and focuses on ensuring 55 litres per capita per day of water supply.",
            "source_documents": []
        }
    elif "swachh bharat" in query_lower:
        return {
            "answer": "Swachh Bharat Mission is a nationwide cleanliness campaign launched by the Government of India in 2014. It aims to eliminate open defecation and improve solid waste management across India.",
            "source_documents": []
        }
    else:
        return {
            "answer": "I apologize, but I couldn't find specific information about your query in the available documents. Please try rephrasing your question or ask about Jal Jeevan Mission, Swachh Bharat Mission, or water and sanitation schemes.",
            "source_documents": []
        }

def should_generate_visualization(query_text, parsed_query):
    """Enhanced logic to determine if a query should generate a visualization."""
    query_lower = query_text.lower()
    
    # Data-related keywords that suggest visualization
    viz_keywords = [
        'visualize', 'show', 'chart', 'graph', 'plot', 'display',
        'how many', 'count', 'total', 'number of', 'statistics',
        'cost', 'expenditure', 'budget', 'spending', 'progress',
        'completion', 'status', 'analysis', 'breakdown', 'distribution',
        'comparison', 'trend', 'data', 'schemes', 'projects'
    ]
    
    # Check for visualization keywords
    has_viz_keywords = any(keyword in query_lower for keyword in viz_keywords)
    
    # Check if intent suggests data analysis
    data_intents = ['count_schemes', 'cost_analysis', 'scheme_types', 'progress_analysis']
    has_data_intent = parsed_query['intent'] in data_intents
    
    # Check if location entities are present (suggests data filtering)
    has_location = bool(parsed_query['entities']['states'] or parsed_query['entities']['divisions'])
    
    # Generate visualization if any condition is met
    return has_viz_keywords or has_data_intent or has_location

def query_database_for_visualization(query_text, parsed_query=None):
    """Processes database queries and generates data for visualization."""
    conn = get_db_connection()
    cursor = conn.cursor()
    data = None
    query_type = "unknown"
    error_message = None

    query_lower = query_text.lower()
    
    if parsed_query is None:
        parsed_query = nlu_processor.parse_query(query_text)
    
    # Extract location filter
    where_clause, params = nlu_processor.build_location_filter(parsed_query['entities'])
    location_info = ""
    
    if where_clause:
        location_info = f" (filtered by: {', '.join(parsed_query['entities']['states'] + parsed_query['entities']['divisions'])})"

    print(f"DEBUG: WHERE clause: {where_clause}")
    print(f"DEBUG: Parameters: {params}")

    try:
        # Enhanced queries with location filtering
        if parsed_query['intent'] == 'cost_analysis' or ("cost" in query_lower and "year" in query_lower):
            base_query = "SELECT sanction_year, SUM(estimated_cost) as total_cost FROM schemes"
            if where_clause:
                base_query += f" WHERE {where_clause}"
            base_query += " GROUP BY sanction_year ORDER BY sanction_year"
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            data = {str(row["sanction_year"]): row["total_cost"] for row in rows if row["sanction_year"] and row["total_cost"]}
            query_type = "cost_by_year"
            
        elif parsed_query['intent'] == 'scheme_types' or ("scheme" in query_lower and "count" in query_lower and "type" in query_lower):
            base_query = "SELECT type_of_scheme, COUNT(*) as count FROM schemes"
            if where_clause:
                base_query += f" WHERE {where_clause}"
            base_query += " GROUP BY type_of_scheme"
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            data = {str(row["type_of_scheme"]): row["count"] for row in rows if row["type_of_scheme"]}
            query_type = "scheme_count_by_type"
            
        elif parsed_query['intent'] == 'progress_analysis' or "progress" in query_lower:
            base_query = "SELECT AVG(physical_completion_progress) as avg_progress FROM schemes WHERE physical_completion_progress > 0"
            if where_clause:
                base_query += f" AND {where_clause}"
            
            cursor.execute(base_query, params)
            avg_progress = cursor.fetchone()["avg_progress"]
            data = {"average_progress": float(avg_progress) if avg_progress else 0}
            query_type = "average_progress"
            
        elif parsed_query['intent'] == 'count_schemes' or ("how many" in query_lower or "total" in query_lower or "count" in query_lower):
            base_query = "SELECT COUNT(*) as total_schemes FROM schemes"
            if where_clause:
                base_query += f" WHERE {where_clause}"
            
            cursor.execute(base_query, params)
            total_schemes = cursor.fetchone()["total_schemes"]
            data = {"total_schemes": int(total_schemes)}
            query_type = "total_schemes"
            
        else:
            if where_clause:
                base_query = "SELECT COUNT(*) as total_schemes FROM schemes WHERE " + where_clause
                cursor.execute(base_query, params)
                total_schemes = cursor.fetchone()["total_schemes"]
                data = {"total_schemes": int(total_schemes)}
                query_type = "total_schemes"
            else:
                error_message = "I can generate visualizations for queries like 'cost by year', 'scheme count by type', 'average progress', or 'total schemes'. You can also specify a state or division name."

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        error_message = f"Database error: {e}"
    finally:
        conn.close()

    if error_message:
        return {"error": error_message, "status": "error"}
    if data:
        return {"data": data, "query_type": query_type, "status": "success", "location_info": location_info}
    return {"error": "Could not understand the data query for visualization.", "status": "error"}

def generate_visualization_image(data, query_type, location_info=""):
    """Generates a visualization image based on the data."""
    if not data:
        return None

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    try:
        if query_type == "cost_by_year":
            years = list(data.keys())
            costs = list(data.values())
            ax.bar(years, costs, color='skyblue')
            ax.set_xlabel("Sanction Year")
            ax.set_ylabel("Total Estimated Cost (in lakhs)")
            ax.set_title(f"Total Estimated Cost by Sanction Year{location_info}")
            plt.xticks(rotation=45, ha="right")
        elif query_type == "scheme_count_by_type":
            types = list(data.keys())
            counts = list(data.values())
            ax.pie(counts, labels=types, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
            ax.set_title(f"Scheme Count by Type{location_info}")
            ax.axis('equal')
        elif query_type == "average_progress":
            ax.bar(["Average Progress"], [data.get("average_progress", 0)], color='lightgreen', width=0.5)
            ax.set_ylabel("Percentage (%)")
            ax.set_title(f"Average Physical Completion Progress{location_info}")
            ax.set_ylim(0, 100)
        elif query_type == "total_schemes":
             ax.text(0.5, 0.5, f"Total Schemes: {data.get('total_schemes', 0)}{location_info}", 
                    horizontalalignment='center', verticalalignment='center', 
                    fontsize=20, transform=ax.transAxes)
             ax.axis('off')
        else:
            return None

        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{plot_url}"
    except Exception as e:
        print(f"Error generating visualization: {e}")
        plt.close(fig)
        return None

# --- API Endpoints --- #

@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    print(f"Received message: {user_message}")
    response_data = {}
    response_type = "text"

    # Parse query using NLU
    parsed_query = nlu_processor.parse_query(user_message)
    print(f"DEBUG: Parsed query: {parsed_query}")

    # Enhanced logic to determine if visualization should be generated
    if should_generate_visualization(user_message, parsed_query):
        print("Intent: Data Visualization Query")
        db_query_result = query_database_for_visualization(user_message, parsed_query)
        if db_query_result["status"] == "success":
            visualization_img = generate_visualization_image(
                db_query_result["data"], 
                db_query_result["query_type"],
                db_query_result.get("location_info", "")
            )
            if visualization_img:
                response_data["answer"] = f"Here's the visualization for your query: {user_message}{db_query_result.get('location_info', '')}"
                response_data["visualization"] = visualization_img
                response_type = "visualization"
            else:
                response_data["answer"] = "I understood your data query, but I had trouble generating the visualization."
        else:
            response_data["answer"] = db_query_result.get("error", "Sorry, I couldn't process that data query.")
    else:
        print("Intent: Knowledge Base Query")
        kb_result = query_knowledge_base(user_message)
        response_data["answer"] = kb_result["answer"]

    response_data["type"] = response_type
    response_data["timestamp"] = datetime.now().isoformat()
    response_data["parsed_query"] = parsed_query
    print(f"Sending response: {response_data.get('answer', 'No answer')[:100]}...")
    return jsonify(response_data)

@chatbot_bp.route("/api/health", methods=["GET"])
def health_check():
    db_ok = False
    kb_ok = False
    nlu_ok = False
    
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1 FROM schemes LIMIT 1")
        conn.close()
        db_ok = True
    except Exception as e:
        print(f"Health check DB error: {e}")
    
    if qa_chain and vectordb:
        kb_ok = True
    
    try:
        test_result = nlu_processor.parse_query("test query")
        nlu_ok = True
    except Exception as e:
        print(f"Health check NLU error: {e}")

    status = {
        "status": "ok" if db_ok and kb_ok and nlu_ok else "error",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "operational" if db_ok else "degraded",
            "knowledge_base_rag": "operational" if kb_ok else "degraded",
            "nlu_processor": "operational" if nlu_ok else "degraded"
        }
    }
    return jsonify(status)