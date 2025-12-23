import os
import requests
import argparse
from pathlib import Path

def bulk_ingest(folder_path: str, company_id: str, api_url: str):
    """
    Scans a folder and uploads all compatible files to the HAR-228 RAG.
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Error: Folder {folder_path} not found.")
        return

    files_found = []
    extensions = ['.txt', '.pdf', '.xlsx', '.csv', '.png', '.jpg', '.jpeg']
    
    for ext in extensions:
        files_found.extend(folder.glob(f"*{ext}"))
    
    if not files_found:
        print(f"No compatible files found in {folder_path} (Supported: {extensions})")
        return

    print(f"🚀 Starting bulk ingestion for company: {company_id}")
    print(f"📂 Folder: {folder_path}")
    print(f"📄 Files found: {len(files_found)}\n")

    url = f"{api_url}/ingest/file"
    
    success_count = 0
    fail_count = 0

    for file_path in files_found:
        print(f"📤 Uploading: {file_path.name}...", end=" ", flush=True)
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f)}
                data = {"company_id": company_id}
                response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                print("✅ Success")
                success_count += 1
            else:
                print(f"❌ Failed ({response.status_code}): {response.text}")
                fail_count += 1
        except Exception as e:
            print(f"💥 Error: {str(e)}")
            fail_count += 1

    print("\n--- Ingestion Finished ---")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print("--------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Ingest documents to HAR-228 RAG")
    parser.add_argument("--folder", required=True, help="Path to the folder containing documents")
    parser.add_argument("--company", required=True, help="Company ID for the knowledge base")
    parser.add_argument("--api", default="http://localhost:8000", help="API Base URL (default: http://localhost:8000)")
    
    args = parser.parse_args()
    bulk_ingest(args.folder, args.company, args.api)
