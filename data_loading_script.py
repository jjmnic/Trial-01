#!/usr/bin/env python3
"""
Data Loading Script for NIC Chatbot

This script handles the initial loading and processing of data for the NIC Chatbot.
It processes a CSV file into an SQLite database and a PDF document into a RAG-ready knowledge base.

IMPORTANT: This script contains mock implementations for local development.
You will need to replace the mock functions with actual API calls to NIC's in-house services
and integrate your specific RAG API key and Database keys.
"""

import pandas as pd
import sqlite3
import os
import json
from datetime import datetime
import sys

# Langchain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def create_database_schema(db_path):
    """
    Creates the SQLite database schema if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id TEXT PRIMARY KEY,
            state_name TEXT,
            division_name TEXT,
            scheme_name TEXT,
            estimated_cost REAL,
            sanction_year INTEGER,
            slssc_meeting_date TEXT,
            work_order_date TEXT,
            physical_completion_date TEXT,
            tentative_completion_date TEXT,
            derived_estimated_cost REAL,
            total_inadmissible_cost REAL,
            derived_cost_after_inadmissible REAL,
            total_expenditure REAL,
            total_central_expenditure REAL,
            total_expenditure_after_2019 REAL,
            total_central_expenditure_after_2019 REAL,
            work_status TEXT,
            scheme_type TEXT,
            water_scheme_type TEXT,
            fhtcs_planned INTEGER,
            fhtcs_provided INTEGER,
            water_source_type TEXT,
            unverified_status TEXT,
            funding_source TEXT,
            type_of_scheme TEXT,
            in_village_infrastructure_cost REAL,
            central_share_cost REAL,
            community_contribution REAL,
            physical_completion_progress REAL,
            physical_status TEXT,
            last_fhtc_month TEXT,
            last_fhtc_year INTEGER,
            last_expenditure_month TEXT,
            last_expenditure_year INTEGER,
            updated_on TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database schema created at: {db_path}")

def load_csv_data(csv_path, db_path):
    """
    Loads data from a CSV file into the SQLite database.
    """
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records from CSV")

        # Clean column names
        column_mapping = {
            'State Name': 'state_name',
            'Division Name': 'division_name',
            'SchemeId': 'scheme_id',
            'Scheme Name': 'scheme_name',
            'Estimated cost (in lakhs) as per work order': 'estimated_cost',
            'Sanction Year': 'sanction_year',
            'SLSSC/ DWSSM meeting date (dd/mm/yyyy)': 'slssc_meeting_date',
            'Work order date (dd/mm/yyyy)': 'work_order_date',
            'Physical completion date': 'physical_completion_date',
            'Tentative completion date': 'tentative_completion_date',
            'Derived estimated cost  (in lakhs)': 'derived_estimated_cost',
            'Total_inadmissible_cost  (in lakhs)': 'total_inadmissible_cost',
            'Derived estimated cost after removing inadmisible cost loaded on JJM  (in lakhs)': 'derived_cost_after_inadmissible',
            'Total expenditure (in lakhs)': 'total_expenditure',
            'Total central expenditure (in lakhs)': 'total_central_expenditure',
            'Total expenditure (in lakhs) on or after 2019-20': 'total_expenditure_after_2019',
            'Total central expenditure (in lakhs) on or after 2019-20': 'total_central_expenditure_after_2019',
            'Work not awarded/ Ongoing/ Financially completed': 'work_status',
            'New scheme/ Retrofit/ Augmentation': 'scheme_type',
            'SVS/ MVS/ Bulk Water Schemes': 'water_scheme_type',
            'FHTCS planned': 'fhtcs_planned',
            'FHTCS provided': 'fhtcs_provided',
            'Ground/ Surface water/ Bulk Water Based/ Other': 'water_source_type',
            'Un-verified status': 'unverified_status',
            'NRDWP/ State and Others/ JJM-PWS/ JJM-Non-PWS': 'funding_source',
            'Type of scheme': 'type_of_scheme',
            'In-village infrastructure cost (in lakhs) (After financial authentication)': 'in_village_infrastructure_cost',
            'Central share cost (in lakhs) (After financial authentication)': 'central_share_cost',
            'Community contribution (in lakhs) (After financial authentication)': 'community_contribution',
            'Physical completion progress (In percentage)': 'physical_completion_progress',
            'Physically completed/ Ongoing but physically not completed/ Work order not issued': 'physical_status',
            'Last FHTC reported Month': 'last_fhtc_month',
            'Last FHTC reported Year': 'last_fhtc_year',
            'Last Expenditure reported Month': 'last_expenditure_month',
            'Last Expenditure reported Year': 'last_expenditure_year',
            'Updated On': 'updated_on'
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Handle missing values
        df = df.fillna('')

        # Convert numeric columns
        numeric_columns = [
            'estimated_cost', 'derived_estimated_cost', 'total_inadmissible_cost',
            'derived_cost_after_inadmissible', 'total_expenditure', 'total_central_expenditure',
            'total_expenditure_after_2019', 'total_central_expenditure_after_2019',
            'fhtcs_planned', 'fhtcs_provided', 'in_village_infrastructure_cost',
            'central_share_cost', 'community_contribution', 'physical_completion_progress'
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Connect to database and insert data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clear existing data
        cursor.execute('DELETE FROM schemes')

        # Insert new data (handle duplicates by ignoring them)
        for index, row in df.iterrows():
            try:
                # Convert row to dict and insert
                row_dict = row.to_dict()
                columns = ', '.join(row_dict.keys())
                placeholders = ', '.join(['?' for _ in row_dict])
                query = f'INSERT OR IGNORE INTO schemes ({columns}) VALUES ({placeholders})'
                cursor.execute(query, list(row_dict.values()))
            except Exception as e:
                print(f"Warning: Skipping row {index} due to error: {str(e)}")
                continue

        conn.commit()
        conn.close()
        print(f"Successfully loaded {len(df)} records into database")
        return True
    except Exception as e:
        print(f"Error loading CSV to database: {e}")
        print("ERROR: No records were loaded from CSV")
        return False

def process_knowledge_base(pdf_path, persist_directory):
    """
    Processes the PDF knowledge base using Langchain to create a vector store.
    """
    try:
        # Load PDF documents
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages from PDF")

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        print(f"Split into {len(texts)} text chunks")

        # Create embeddings and vector store
        # Using a local model for embeddings to avoid API keys and external calls
        # You might need to download the model if it's not cached locally
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': False}
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        # Create Chroma vector store and persist it
        # This will create a directory with the vector store data
        vectordb = Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory=persist_directory)
        vectordb.persist()
        print(f"Processed knowledge base: {len(texts)} chunks saved to {persist_directory}")
        return True
    except Exception as e:
        print(f"Error processing knowledge base: {e}")
        return False

def validate_data(db_path):
    """
    Performs basic validation on the loaded data.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM schemes')
    total_records = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT state_name) FROM schemes')
    unique_states = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT sanction_year) FROM schemes')
    unique_years = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(estimated_cost) FROM schemes')
    avg_cost = cursor.fetchone()[0]

    conn.close()

    print("Data Validation Results:")
    print(f"  Total Records: {total_records}")
    print(f"  Unique States: {unique_states}")
    print(f"  Unique Years: {unique_years}")
    print(f"  Average Cost: {avg_cost:.2f} lakhs")

    if total_records > 0 and unique_states > 0:
        print("  Validation: PASSED")
        return True
    else:
        print("  Validation: FAILED")
        return False

def main():
    """
    Main function to orchestrate data loading and processing.
    """
    print("=== NIC Chatbot Data Loading Script ===")
    print(f"Started at: {datetime.now()}")

    # Define paths
    # IMPORTANT: For Windows, use double backslashes or forward slashes for paths
    base_dir = r"C:/Users/HP/Documents/Vedant/New folder 1"
    # base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".")) # Current directory
    csv_path = os.path.join(base_dir, "upload", "List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv")
    pdf_path = os.path.join(base_dir, "upload", "KnowledgeBase-DialogFlow.pdf")
    db_dir = os.path.join(base_dir, "nic-chatbot-backend", "src", "database")
    db_path = os.path.join(db_dir, "schemes.db")
    knowledge_base_persist_dir = os.path.join(base_dir, "data", "chroma_db")

    # Create necessary directories
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(knowledge_base_persist_dir, exist_ok=True)

    print(f"CSV Path: {csv_path}")
    print(f"PDF Path: {pdf_path}")
    print(f"Database Path: {db_path}")
    print(f"Knowledge Base Persist Directory: {knowledge_base_persist_dir}")

    # Step 1: Create database schema
    print("\n1. Creating database schema...")
    create_database_schema(db_path)

    # Step 2: Load CSV data
    print("\n2. Loading CSV data...")
    csv_load_success = load_csv_data(csv_path, db_path)

    # Step 3: Process knowledge base (PDF)
    print("\n3. Processing knowledge base (PDF) with Langchain...")
    kb_process_success = process_knowledge_base(pdf_path, knowledge_base_persist_dir)

    # Step 4: Validate data loading
    print("\n4. Validating data loading...")
    data_validation_success = validate_data(db_path)

    if csv_load_success and kb_process_success and data_validation_success:
        print("\n=== Data Loading Completed Successfully ===")
        print(f"Completed at: {datetime.now()}")
        return True
    else:
        print("\n=== Data Loading FAILED ===")
        print("Please check the error messages above.")
        return False

if __name__ == "__main__":
    # Create 'upload' directory and copy files if they don't exist
    upload_dir = os.path.join(os.path.dirname(__file__), "upload")
    os.makedirs(upload_dir, exist_ok=True)

    # Check if the original files exist in the expected upload location
    # If not, this script assumes they are in the current directory for the sandbox environment
    # For local PC, ensure these files are in the 'upload' subfolder next to this script
    original_csv_path = "original_csv_path = C:/Users/HP/Documents/Vedant/New folder 1/upload/List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv"
    original_pdf_path = "C:/Users/HP/Documents/Vedant/New folder 1/upload/KnowledgeBase-DialogFlow.pdf"

    # In a local PC setup, you would place the CSV and PDF directly into the 'upload' folder
    # For the sandbox, we need to copy them from the initial upload location
    if not os.path.exists(os.path.join(upload_dir, "List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv")):
        try:
            import shutil
            shutil.copy(original_csv_path, upload_dir)
            shutil.copy(original_pdf_path, upload_dir)
            print(f"Copied {os.path.basename(original_csv_path)} and {os.path.basename(original_pdf_path)} to {upload_dir}")
        except FileNotFoundError:
            print("Original CSV/PDF not found in sandbox upload path. Please ensure they are in the 'upload' folder next to data_loading_script.py on your local PC.")
        except Exception as e:
            print(f"Error copying files: {e}")

    success = main()
    sys.exit(0 if success else 1)


