#!/usr/bin/env python3
"""
Daily Data Update Script for NIC Chatbot

This script handles daily updates to the chatbot's data sources.
It can be scheduled to run automatically to keep the data current.

IMPORTANT: This script contains mock implementations for local development.
You will need to replace the mock functions with actual API calls to NIC's in-house services.
"""

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import json
import requests
from pathlib import Path

def update_csv_data(new_csv_path, db_path):
    """
    Update the database with new CSV data
    
    Args:
        new_csv_path (str): Path to the new CSV file
        db_path (str): Path to the SQLite database file
    
    Returns:
        dict: Update results
    
    TODO: Replace this with actual API calls to NIC's database service
    """
    try:
        # Read new CSV file
        df = pd.read_csv(new_csv_path)
        print(f"Loaded {len(df)} records from new CSV")
        
        # Clean column names (same as in data_loading_script.py)
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
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current record count
        cursor.execute('SELECT COUNT(*) FROM schemes')
        old_count = cursor.fetchone()[0]
        
        # Update existing records and insert new ones
        new_records = 0
        updated_records = 0
        
        for index, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                scheme_id = row_dict.get('scheme_id', '')
                
                # Check if record exists
                cursor.execute('SELECT COUNT(*) FROM schemes WHERE scheme_id = ?', (scheme_id,))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Update existing record
                    set_clause = ', '.join([f'{col} = ?' for col in row_dict.keys() if col != 'scheme_id'])
                    values = [row_dict[col] for col in row_dict.keys() if col != 'scheme_id']
                    values.append(scheme_id)
                    
                    query = f'UPDATE schemes SET {set_clause} WHERE scheme_id = ?'
                    cursor.execute(query, values)
                    updated_records += 1
                else:
                    # Insert new record
                    columns = ', '.join(row_dict.keys())
                    placeholders = ', '.join(['?' for _ in row_dict])
                    query = f'INSERT INTO schemes ({columns}) VALUES ({placeholders})'
                    cursor.execute(query, list(row_dict.values()))
                    new_records += 1
                    
            except Exception as e:
                print(f"Warning: Skipping row {index} due to error: {str(e)}")
                continue
        
        conn.commit()
        
        # Get new record count
        cursor.execute('SELECT COUNT(*) FROM schemes')
        new_count = cursor.fetchone()[0]
        
        conn.close()
        
        results = {
            'old_count': old_count,
            'new_count': new_count,
            'new_records': new_records,
            'updated_records': updated_records,
            'processed_records': len(df),
            'update_time': datetime.now().isoformat()
        }
        
        print(f"Update Results:")
        print(f"  Records before update: {old_count}")
        print(f"  Records after update: {new_count}")
        print(f"  New records added: {new_records}")
        print(f"  Existing records updated: {updated_records}")
        
        return results
        
    except Exception as e:
        print(f"Error updating CSV data: {str(e)}")
        return {'error': str(e)}

def update_knowledge_base_from_api():
    """
    Update knowledge base from NIC's RAG API
    
    Returns:
        dict: Update results
    
    TODO: Implement actual API call to NIC's RAG service to refresh knowledge base
    """
    try:
        # This is a mock implementation
        # In production, you would call NIC's RAG API to refresh the knowledge base
        
        print("Checking for knowledge base updates...")
        
        # Mock API call
        # response = requests.get('https://your-nic-rag-api.gov.in/api/v1/knowledge-base/status')
        # if response.status_code == 200:
        #     data = response.json()
        #     if data.get('needs_update'):
        #         # Trigger knowledge base refresh
        #         refresh_response = requests.post('https://your-nic-rag-api.gov.in/api/v1/knowledge-base/refresh')
        #         return {'status': 'updated', 'timestamp': datetime.now().isoformat()}
        
        # For now, just return a mock response
        return {
            'status': 'no_update_needed',
            'last_updated': datetime.now().isoformat(),
            'message': 'Knowledge base is up to date'
        }
        
    except Exception as e:
        print(f"Error updating knowledge base: {str(e)}")
        return {'error': str(e)}

def generate_daily_report(db_path, output_path):
    """
    Generate a daily report of system status and data statistics
    
    Args:
        db_path (str): Path to the SQLite database file
        output_path (str): Path to save the report
    
    Returns:
        dict: Report data
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get basic statistics
        cursor.execute('SELECT COUNT(*) FROM schemes')
        total_schemes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT state_name) FROM schemes')
        unique_states = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM schemes WHERE work_status = "Ongoing"')
        ongoing_schemes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM schemes WHERE work_status = "Financially completed"')
        completed_schemes = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(estimated_cost) FROM schemes')
        total_estimated_cost = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(total_expenditure) FROM schemes')
        total_expenditure = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(physical_completion_progress) FROM schemes WHERE physical_completion_progress > 0')
        avg_progress = cursor.fetchone()[0] or 0
        
        # Get recent updates (schemes updated in last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%d-%m-%Y')
        cursor.execute('SELECT COUNT(*) FROM schemes WHERE updated_on >= ?', (thirty_days_ago,))
        recent_updates = cursor.fetchone()[0]
        
        conn.close()
        
        report = {
            'report_date': datetime.now().isoformat(),
            'database_statistics': {
                'total_schemes': total_schemes,
                'unique_states': unique_states,
                'ongoing_schemes': ongoing_schemes,
                'completed_schemes': completed_schemes,
                'total_estimated_cost_lakhs': round(total_estimated_cost, 2),
                'total_expenditure_lakhs': round(total_expenditure, 2),
                'average_completion_progress': round(avg_progress, 2),
                'recent_updates_30_days': recent_updates
            },
            'system_health': {
                'database_accessible': True,
                'data_freshness': 'current',
                'last_update_check': datetime.now().isoformat()
            }
        }
        
        # Save report
        with open(output_path, 'w') as file:
            json.dump(report, file, indent=2)
        
        print(f"Daily report generated: {output_path}")
        print(f"Total schemes: {total_schemes}")
        print(f"Ongoing schemes: {ongoing_schemes}")
        print(f"Average progress: {avg_progress:.2f}%")
        
        return report
        
    except Exception as e:
        print(f"Error generating daily report: {str(e)}")
        return {'error': str(e)}

def main():
    """
    Main function for daily data updates
    """
    print("=== NIC Chatbot Daily Update Script ===")
    print(f"Started at: {datetime.now()}")
    
    # Define paths
    base_dir = "/home/ubuntu"
    db_path = os.path.join(base_dir, "nic-chatbot-backend", "src", "database", "schemes.db")
    report_path = os.path.join(base_dir, "data", f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    print(f"Database Path: {db_path}")
    print(f"Report Path: {report_path}")
    
    try:
        # Step 1: Check for new CSV data
        print("\\n1. Checking for new CSV data...")
        # In production, you would check for new CSV files in a designated directory
        # or call an API to get the latest data
        print("No new CSV data found (this is normal for demo)")
        
        # Step 2: Update knowledge base
        print("\\n2. Updating knowledge base...")
        kb_result = update_knowledge_base_from_api()
        print(f"Knowledge base status: {kb_result.get('status', 'unknown')}")
        
        # Step 3: Generate daily report
        print("\\n3. Generating daily report...")
        report = generate_daily_report(db_path, report_path)
        
        if 'error' not in report:
            print("\\n=== Daily Update Completed Successfully ===")
            print(f"Report saved to: {report_path}")
            print(f"Completed at: {datetime.now()}")
            return True
        else:
            print(f"ERROR: Daily update failed: {report['error']}")
            return False
        
    except Exception as e:
        print(f"\\nERROR: Daily update failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

