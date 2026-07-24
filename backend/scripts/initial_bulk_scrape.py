import os
import sys
import time
import argparse
from datetime import datetime

# Adjust Python path to allow importing from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app import create_app
from backend.extensions import db

def main():
    parser = argparse.ArgumentParser(description="Initial bulk scrape of BCT circulars.")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Limit the number of circulars to download and ingest."
    )
    parser.add_argument(
        "--delay", 
        type=int, 
        default=2, 
        help="Delay in seconds between circular downloads (default: 2s)."
    )
    args = parser.parse_args()

    print("Initializing Flask App context...")
    app = create_app("development")
    
    with app.app_context():
        scraper = app.bct_scraper
        print("Scraping circular listings from BCT website...")
        scraped = scraper.scrape_circulars()
        
        if not scraped:
            print("ERROR: Scraper found no circulars. The page structure might have changed or site is down.")
            sys.exit(1)
            
        print(f"Total circulars found on BCT page: {len(scraped)}")
        
        print("Filtering out already ingested circulars...")
        new_circulars = scraper.get_new_circulars(scraped)
        print(f"New circulars to ingest: {len(new_circulars)}")
        
        if not new_circulars:
            print("No new circulars found. Database is up to date!")
            return
            
        # Sort circulars chronologically (oldest first) to build modification chains logically
        new_circulars.sort(key=lambda x: x.date)
        
        if args.limit is not None:
            print(f"Applying limit: Processing only the first {args.limit} new circulars.")
            new_circulars = new_circulars[:args.limit]
            
        total = len(new_circulars)
        success_count = 0
        failed_count = 0
        errors = []
        
        start_time = datetime.now()
        print(f"Starting bulk ingestion of {total} circulars at {start_time.strftime('%Y-%m-%d %H:%M:%S')}...\n")
        
        for idx, circ in enumerate(new_circulars, start=1):
            print(f"[{idx}/{total}] Processing Circular {circ.number}: '{circ.title[:80]}...'")
            print(f"  Source URL: {circ.pdf_url}")
            print(f"  Date: {circ.date.strftime('%Y-%m-%d')} | Category: {circ.category}")
            
            # Step 1: Download PDF
            pdf_path = scraper.download_pdf(circ)
            if not pdf_path:
                err_msg = f"Failed to download PDF for circular {circ.number}"
                print(f"  ❌ {err_msg}")
                errors.append(err_msg)
                failed_count += 1
                continue
                
            print(f"  Downloaded PDF to {pdf_path}")
            
            # Step 2: Ingest (runs processing, text chunking, embeddings, Neo4j construction)
            try:
                res = scraper.ingest_circular(circ, pdf_path)
                if res.get("success"):
                    print(f"  ✅ Ingested successfully. Chunks: {res.get('chunks_count')}")
                    success_count += 1
                else:
                    err_msg = f"Failed to ingest circular {circ.number}: {res.get('error') or res.get('errors')}"
                    print(f"  ❌ {err_msg}")
                    errors.append(err_msg)
                    failed_count += 1
            except Exception as e:
                err_msg = f"Unexpected error ingesting circular {circ.number}: {e}"
                print(f"  ❌ {err_msg}")
                errors.append(err_msg)
                failed_count += 1
                
            # Politeness delay
            if idx < total:
                print(f"  Waiting {args.delay} seconds before next download...")
                time.sleep(args.delay)
            print()
            
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("==================================================")
        print("BULK INGESTION SUMMARY")
        print("==================================================")
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration}")
        print(f"Processed:  {total}")
        print(f"Success:    {success_count}")
        print(f"Failed:     {failed_count}")
        
        if errors:
            print("\nErrors encountered:")
            for err in errors:
                print(f"  - {err}")
        print("==================================================")

if __name__ == "__main__":
    main()
