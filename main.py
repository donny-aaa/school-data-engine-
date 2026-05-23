import functions_framework
from flask import jsonify, make_response
import pandas as pd
import io

@functions_framework.http
def process_school_data(request):
    """
    HTTP Cloud Function to process school data uploads.
    """
    # 1. CORS CONFIGURATION (Crucial for web form submissions)
    # This handles the "preflight" request the browser sends to check permissions
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*', # Change '*' to your website URL for better security later
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Headers for the actual response
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    try:
        # 2. EXTRACT FORM VARIABLES
        # Fallback to 'unknown' if not provided
        district = request.form.get('district', 'unknown')
        dashboard = request.form.get('dashboard', 'unknown')
        academic_year = request.form.get('year', 'unknown')
        sheet_urls_raw = request.form.get('sheet_urls', '')

        print(f"Processing upload for {district} - {dashboard} ({academic_year})")

        # 3. PROCESS UPLOADED FILES (.csv, .xlsx)
        uploaded_files = request.files.getlist('files')
        file_stats = []

        for file in uploaded_files:
            if file.filename == '':
                continue
            
            try:
                # Load the file directly into a Pandas DataFrame based on its extension
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.filename.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    print(f"Skipping unsupported file type: {file.filename}")
                    continue
                
                # --- YOUR DATA LOGIC GOES HERE ---
                # Example: df = df.dropna() # Clean data
                # Example: df.to_gbq('my_dataset.my_table', project_id='my-project') # Send to BigQuery
                # ---------------------------------

                # Record some basic stats to return to the frontend
                file_stats.append({
                    "filename": file.filename,
                    "rows": len(df),
                    "columns": len(df.columns)
                })
                print(f"Successfully processed {file.filename} with {len(df)} rows.")

            except Exception as e:
                print(f"Error reading file {file.filename}: {e}")

        # 4. PROCESS GOOGLE SHEETS LINKS
        # Split the text area by newlines to get individual URLs
        sheet_urls = [url.strip() for url in sheet_urls_raw.split('\n') if url.strip()]
        
        for url in sheet_urls:
            # --- YOUR GOOGLE SHEETS LOGIC GOES HERE ---
            # To read public sheets in pandas, you usually alter the URL to export as CSV:
            # export_url = url.replace('/edit#gid=', '/export?format=csv&gid=')
            # df = pd.read_csv(export_url)
            # ------------------------------------------
            print(f"Acknowledged Sheet URL: {url}")

        # 5. SEND SUCCESS RESPONSE TO FRONTEND
        response_payload = {
            "status": "success",
            "message": "Data batch processed successfully.",
            "details": {
                "district": district,
                "dashboard_target": dashboard,
                "files_processed": len(file_stats),
                "sheets_acknowledged": len(sheet_urls)
            }
        }
        
        return (jsonify(response_payload), 200, headers)

    except Exception as e:
        print(f"Critical Error: {e}")
        # Send error response so the frontend knows something went wrong
        return (jsonify({"status": "error", "message": str(e)}), 500, headers)
