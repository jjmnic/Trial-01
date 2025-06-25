#!/usr/bin/env python3
"""
Test script for NLU functionality and improved chatbot capabilities.
"""

import sys
import os
sys.path.append('/home/ubuntu')

from nlu_processor_updated import NLUProcessor
import sqlite3

def test_nlu_entity_extraction():
    """Test entity extraction functionality."""
    print("=== Testing NLU Entity Extraction ===")
    
    # Initialize NLU processor with CSV data
    csv_path = "/home/ubuntu/upload/List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv"
    nlu = NLUProcessor(csv_path)
    
    test_queries = [
        "How many schemes are there in Madhya Pradesh?",
        "Show me cost by year for Bhopal division",
        "What is the progress in Andhra Pradesh?",
        "Count schemes in Gwalior",
        "Total schemes in Haryana state",
        "Show scheme types for Balaghat",
        "Cost analysis for Madhya Pradesh",
        "How many schemes without location?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        parsed = nlu.parse_query(query)
        print(f"  Intent: {parsed['intent']}")
        print(f"  States: {parsed['entities']['states']}")
        print(f"  Divisions: {parsed['entities']['divisions']}")
        print(f"  Generic locations: {parsed['entities']['locations']}")
        
        where_clause, params = nlu.build_location_filter(parsed['entities'])
        if where_clause:
            print(f"  SQL WHERE: {where_clause}")
            print(f"  Parameters: {params}")
        else:
            print("  No location filter")

def test_database_queries():
    """Test database queries with location filtering."""
    print("\n=== Testing Database Queries ===")
    
    # Create a mock database for testing
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create test table
    cursor.execute('''
        CREATE TABLE schemes (
            state_name TEXT,
            division_name TEXT,
            estimated_cost REAL,
            sanction_year TEXT,
            type_of_scheme TEXT,
            physical_completion_progress REAL
        )
    ''')
    
    # Insert test data
    test_data = [
        ('Madhya Pradesh', 'Bhopal', 100.0, '2020-2021', 'PWS', 80.0),
        ('Madhya Pradesh', 'Gwalior', 150.0, '2021-2022', 'PWS', 90.0),
        ('Andhra Pradesh', 'Guntur', 200.0, '2020-2021', 'Retrofit', 75.0),
        ('Haryana', 'Ambala', 120.0, '2022-2023', 'PWS', 85.0),
        ('Madhya Pradesh', 'Bhopal', 80.0, '2022-2023', 'Retrofit', 95.0)
    ]
    
    cursor.executemany('''
        INSERT INTO schemes VALUES (?, ?, ?, ?, ?, ?)
    ''', test_data)
    
    conn.commit()
    
    # Test queries
    test_cases = [
        {
            'description': 'Total schemes in Madhya Pradesh',
            'where_clause': 'LOWER(state_name) = ?',
            'params': ['madhya pradesh'],
            'query': 'SELECT COUNT(*) as total_schemes FROM schemes WHERE {}'
        },
        {
            'description': 'Cost by year for Bhopal',
            'where_clause': 'LOWER(division_name) = ?',
            'params': ['bhopal'],
            'query': 'SELECT sanction_year, SUM(estimated_cost) as total_cost FROM schemes WHERE {} GROUP BY sanction_year'
        },
        {
            'description': 'Average progress in Andhra Pradesh',
            'where_clause': 'LOWER(state_name) = ?',
            'params': ['andhra pradesh'],
            'query': 'SELECT AVG(physical_completion_progress) as avg_progress FROM schemes WHERE {} AND physical_completion_progress > 0'
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['description']}")
        query = test_case['query'].format(test_case['where_clause'])
        print(f"SQL: {query}")
        print(f"Params: {test_case['params']}")
        
        try:
            cursor.execute(query, test_case['params'])
            results = cursor.fetchall()
            print(f"Results: {results}")
        except Exception as e:
            print(f"Error: {e}")
    
    conn.close()

def test_intent_classification():
    """Test intent classification."""
    print("\n=== Testing Intent Classification ===")
    
    csv_path = "/home/ubuntu/upload/List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv"
    nlu = NLUProcessor(csv_path)
    
    test_queries = [
        ("How many schemes are there?", "count_schemes"),
        ("Show cost by year", "cost_analysis"),
        ("What are the scheme types?", "scheme_types"),
        ("Show me the progress", "progress_analysis"),
        ("Visualize the data", "visualization"),
        ("Tell me about water schemes", "general_query")
    ]
    for query, expected_intent in test_queries:
        parsed_query = nlu.parse_query(query)
        actual_intent = parsed_query["intent"]
        status = "✓" if actual_intent == expected_intent else "✗"
        print(f"{status} \'{query}\' -> {actual_intent} (expected: {expected_intent})")
def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Testing Edge Cases ===")
    
    csv_path = "/home/ubuntu/upload/List_of_Schemes_Format_PM_10_B_2025_04_23_09_52.csv"
    nlu = NLUProcessor(csv_path)
    
    edge_cases = [
        "",  # Empty query
        "   ",  # Whitespace only
        "xyz unknown location",  # Unknown location
        "MADHYA PRADESH",  # Uppercase
        "madhya pradesh",  # Lowercase
        "MP",  # Abbreviation
        "What is SBM?",
        "Tell me about JJM",
        "Show me schemes in Bhopal and Gwalior",  # Multiple locations
    ]
    
    for query in edge_cases:
        print(f"\nEdge case: '{query}'")
        try:
            parsed = nlu.parse_query(query)
            where_clause, params = nlu.build_location_filter(parsed['entities'])
            print(f"  Parsed successfully: {parsed['intent']}")
            print(f"  Location filter: {where_clause}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    print("Starting NLU and Chatbot Tests...")
    
    test_nlu_entity_extraction()
    test_database_queries()
    test_intent_classification()
    test_edge_cases()
    
    print("\n=== Test Summary ===")
    print("All tests completed. Check output above for any issues.")

