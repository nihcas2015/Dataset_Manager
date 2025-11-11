import os
import json
import requests
import ollama
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict, Optional
import time
import re
import webbrowser
import csv

class DatasetFinder:
    def __init__(self, model='llama3.2'):
        self.model = model
        self.datasets_folder = 'datasets'
        self.results_folder = 'results'
        self.create_folders()
        
        # Activity log
        self.activity_log = []
        self.found_datasets = []
        
        # Predefined data repositories
        self.repositories = {
            'kaggle': {
                'name': 'Kaggle',
                'search_url': 'https://www.kaggle.com/search?q=',
                'api_info': 'CSV datasets available',
                'open_browser': True
            },
            'data_gov': {
                'name': 'Data.gov',
                'search_url': 'https://catalog.data.gov/dataset?q=',
                'api_info': 'Multiple CSV datasets',
                'open_browser': True
            },
            'uci_ml': {
                'name': 'UCI ML Repository',
                'search_url': 'https://archive.ics.uci.edu/datasets?search=',
                'api_info': 'ML-ready datasets',
                'open_browser': True
            },
            'world_bank': {
                'name': 'World Bank Data',
                'search_url': 'https://data.worldbank.org/indicator?q=',
                'api_info': 'CSV downloads available',
                'open_browser': True
            },
            'github': {
                'name': 'GitHub',
                'search_url': 'https://github.com/search?q=dataset+csv+',
                'api_info': 'Raw CSV files',
                'open_browser': True
            },
            'awesome_data': {
                'name': 'Awesome Public Datasets',
                'search_url': 'https://github.com/awesomedata/awesome-public-datasets/search?q=',
                'api_info': 'Curated datasets',
                'open_browser': True
            }
        }
        
    def create_folders(self):
        """Create necessary folders"""
        os.makedirs(self.datasets_folder, exist_ok=True)
        os.makedirs(self.results_folder, exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Replace emojis with ASCII equivalents for Windows console compatibility
        message = message.replace('\U0001F916', '[AI]')  # robot emoji
        message = message.replace('\U0001F310', '[WEB]')  # globe emoji
        message = message.replace('\U0001F4CA', '[DATA]')  # bar chart emoji
        message = message.replace('\u2705', '[OK]')  # check mark emoji
        message = message.replace('\u274C', '[X]')  # cross mark emoji
        message = message.replace('\u26A0\uFE0F', '[!]')  # warning sign emoji
        message = message.replace('\U0001F50D', '[SEARCH]')  # magnifying glass emoji
        
        activity = {
            'time': timestamp,
            'level': level,
            'message': message
        }   
        self.activity_log.append(activity)
        
        # Color coding for terminal
        colors = {
            'INFO': '\033[94m',      # Blue
            'SUCCESS': '\033[92m',   # Green
            'WARNING': '\033[93m',   # Yellow
            'ERROR': '\033[91m',     # Red
            'STATUS': '\033[95m',    # Magenta
        }
        reset = '\033[0m'
        color = colors.get(level, '')
        
        try:
            print(f"{color}[{timestamp}] [{level}] {message}{reset}")
        except UnicodeEncodeError:
            # Fallback without color if encoding fails
            print(f"[{timestamp}] [{level}] {message}")
    
    def open_search_page(self, url: str, repo_name: str):
        """Open repository search page in browser"""
        try:
            self.log(f" Opening {repo_name} in browser...", "STATUS")
            webbrowser.open(url)
            time.sleep(2)  # Give time for browser to open
        except Exception as e:
            self.log(f"Could not open browser: {str(e)}", "WARNING")
        
    def query_llm(self, prompt: str, system_context: str = None) -> str:
        """Query the LLM"""
        try:
            messages = []
            if system_context:
                messages.append({'role': 'system', 'content': system_context})
            messages.append({'role': 'user', 'content': prompt})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            self.log(f"LLM query failed: {str(e)}", "ERROR")
            return ""
    
    def generate_ml_focused_queries(self, user_query: str) -> List[str]:
        """Generate ML-focused search queries"""
        self.log(" Generating ML-focused search queries...", "STATUS")
        
        prompt = f"""Given the query: "{user_query}"

Generate 3-5 search queries specifically for finding ML-suitable CSV datasets.
Focus on: tabular data, numerical features, classification/regression tasks.

Return ONLY a JSON array: ["query1", "query2", "query3"]"""
        
        response = self.query_llm(prompt)
        
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group())
                self.log(f" Generated {len(queries)} search queries", "SUCCESS")
                for i, q in enumerate(queries, 1):
                    self.log(f"  Query {i}: {q}", "INFO")
                return queries
        except:
            pass
        
        fallback = [user_query + " csv dataset", user_query + " machine learning data"]
        self.log(f"Using fallback queries: {fallback}", "WARNING")
        return fallback
    
    def is_csv_url(self, url: str) -> bool:
        """Check if URL points to a CSV file"""
        url_lower = url.lower()
        return (url_lower.endswith('.csv') or 
                url_lower.endswith('.csv.gz') or
                '/csv/' in url_lower or
                'format=csv' in url_lower or
                'csv' in url_lower)
    
    def analyze_ml_suitability(self, dataset_info: Dict) -> Dict:
        """Use LLM to analyze if dataset is ML-suitable"""
        prompt = f"""Analyze this dataset for ML suitability:

Title: {dataset_info.get('title', 'N/A')}
Description: {dataset_info.get('description', 'N/A')}
URL: {dataset_info.get('url', 'N/A')}

Evaluate:
1. Is it CSV format? (check URL and description)
2. Suitable for ML? (tabular, numerical, labeled data)
3. Dataset size (prefer 100+ rows, 3+ features)
4. Has clear target variable or use case?

Return JSON:
{{
    "is_csv": true/false,
    "ml_suitable": true/false,
    "ml_score": 0-10,
    "estimated_rows": "<estimate or unknown>",
    "estimated_features": "<estimate or unknown>",
    "ml_task": "<classification/regression/clustering/unknown>",
    "reasoning": "<brief explanation>"
}}"""
        
        response = self.query_llm(prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
        except:
            pass
        
        # Fallback analysis
        return {
            "is_csv": self.is_csv_url(dataset_info.get('url', '')),
            "ml_suitable": True,
            "ml_score": 5,
            "estimated_rows": "unknown",
            "estimated_features": "unknown",
            "ml_task": "unknown",
            "reasoning": "Basic URL analysis"
        }
    
    def extract_csv_datasets(self, content: str, query: str) -> List[Dict]:
        """Extract CSV dataset URLs from content"""
        prompt = f"""Find CSV datasets in these search results for: "{query}"

Content (excerpt):
{content[:4000]}

Extract ONLY CSV datasets suitable for machine learning.
Look for: .csv files, CSV download links, tabular data mentions.

Return JSON array:
[
    {{
        "url": "<direct_csv_url>",
        "title": "<dataset_name>",
        "description": "<what it contains>",
        "format": "csv"
    }}
]

Return empty array [] if none found."""
        
        response = self.query_llm(prompt)
        
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                datasets = json.loads(json_match.group())
                # Filter only CSV
                csv_datasets = [ds for ds in datasets if 
                               self.is_csv_url(ds.get('url', '')) or 
                               ds.get('format', '').lower() == 'csv']
                return csv_datasets
        except Exception as e:
            self.log(f"Failed to parse datasets: {str(e)}", "ERROR")
        
        return []
    
    def search_repository(self, repo_key: str, query: str) -> List[Dict]:
        """Search repository for CSV datasets"""
        repo = self.repositories[repo_key]
        
        # Build search URL
        search_query = query + " csv"
        search_url = repo['search_url'] + quote(search_query)
        
        self.log(f"\n{'='*70}", "INFO")
        self.log(f"Searching: {repo['name']}", "STATUS")
        self.log(f"Query: {search_query}", "INFO")
        self.log(f"URL: {search_url}", "INFO")
        self.log(f"{'='*70}", "INFO")
        
        # Open in browser
        if repo.get('open_browser', True):
            self.open_search_page(search_url, repo['name'])
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            self.log(f"Fetching search results from {repo['name']}...", "INFO")
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                self.log(f"Successfully accessed {repo['name']}", "SUCCESS")
                
                # Extract datasets using LLM
                self.log(f" Analyzing page content with LLM...", "INFO")
                datasets = self.extract_csv_datasets(response.text, query)
                
                if datasets:
                    self.log(f" Found {len(datasets)} CSV datasets from {repo['name']}", "SUCCESS")
                    for i, ds in enumerate(datasets[:3], 1):
                        self.log(f"   {i}. {ds.get('title', 'Unknown')}", "INFO")
                else:
                    self.log(f" No CSV datasets found in {repo['name']}", "WARNING")
                
                return datasets
            else:
                self.log(f" Failed to access {repo['name']}: Status {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f" Error searching {repo['name']}: {str(e)}", "ERROR")
        
        return []
    
    def validate_csv_content(self, filepath: str) -> Dict:
        """Validate downloaded CSV for ML suitability"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            if len(rows) < 2:
                return {"valid": False, "reason": "Too few rows"}
            
            headers = rows[0]
            num_features = len(headers)
            num_rows = len(rows) - 1
            
            # Check for numerical data
            numerical_cols = 0
            for col_idx in range(min(num_features, len(rows[1]))):
                try:
                    float(rows[1][col_idx])
                    numerical_cols += 1
                except:
                    pass
            
            is_valid = num_rows >= 10 and num_features >= 2
            
            return {
                "valid": is_valid,
                "rows": num_rows,
                "features": num_features,
                "numerical_features": numerical_cols,
                "headers": headers[:5]  # First 5 headers
            }
        except Exception as e:
            return {"valid": False, "reason": str(e)}
    
    def download_csv_dataset(self, url: str, filename: str) -> Optional[Dict]:
        """Download and validate CSV dataset"""
        try:
            self.log(f" Downloading: {url}", "INFO")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                filepath = os.path.join(self.datasets_folder, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Validate CSV
                validation = self.validate_csv_content(filepath)
                
                if validation.get('valid'):
                    file_size = os.path.getsize(filepath)
                    self.log(f" Downloaded valid CSV: {filename}", "SUCCESS")
                    self.log(f"   Size: {file_size} bytes", "INFO")
                    self.log(f"   Rows: {validation.get('rows')}, Features: {validation.get('features')}", "INFO")
                    return {
                        'filepath': filepath,
                        'validation': validation
                    }
                else:
                    os.remove(filepath)
                    self.log(f" Invalid CSV removed: {validation.get('reason')}", "WARNING")
            else:
                self.log(f" Download failed: Status {response.status_code}", "WARNING")
        except Exception as e:
            self.log(f" Download error: {str(e)}", "ERROR")
        
        return None
    
    def save_dataset_list(self, datasets: List[Dict], query: str):
        """Save comprehensive dataset list"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = os.path.join(self.results_folder, f"ml_datasets_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump({
                'query': query,
                'timestamp': timestamp,
                'total_found': len(datasets),
                'datasets': datasets
            }, f, indent=2)
        
        self.log(f"Saved dataset list: {json_file}", "SUCCESS")
        
        # Save as CSV
        csv_file = os.path.join(self.results_folder, f"ml_datasets_{timestamp}.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'URL', 'ML Score', 'ML Task', 'Est. Rows', 'Est. Features', 'Downloaded', 'Local Path', 'Description'])
            
            for ds in datasets:
                writer.writerow([
                    ds.get('title', 'N/A'),
                    ds.get('url', 'N/A'),
                    ds.get('ml_analysis', {}).get('ml_score', 'N/A'),
                    ds.get('ml_analysis', {}).get('ml_task', 'N/A'),
                    ds.get('ml_analysis', {}).get('estimated_rows', 'N/A'),
                    ds.get('ml_analysis', {}).get('estimated_features', 'N/A'),
                    'Yes' if ds.get('downloaded') else 'No',
                    ds.get('local_path', 'N/A'),
                    ds.get('description', 'N/A')[:100]
                ])
        
        self.log(f"Saved CSV list: {csv_file}", "SUCCESS")
        return json_file, csv_file
    
    def find_datasets(self, user_query: str):
        """Main function to find ML-suitable CSV datasets"""
        self.log("\n" + " " + "="*66, "STATUS")
        self.log("   STARTING ML DATASET SEARCH", "STATUS")
        self.log("   Browser windows will open for each search", "STATUS")
        self.log("="*70 + "\n", "STATUS")
        
        # Generate queries
        search_queries = self.generate_ml_focused_queries(user_query)
        
        self.log("\n Beginning repository searches...", "STATUS")
        self.log("   (Browser tabs will open - you can review the actual search pages)\n", "INFO")
        
        input("Press ENTER to start searching repositories...")
        
        all_datasets = []
        
        # Search repositories
        for repo_key in self.repositories:
            for query in search_queries[:2]:  # Top 2 queries per repo
                datasets = self.search_repository(repo_key, query)
                all_datasets.extend(datasets)
                
                # Pause between searches
                if datasets or True:  # Always pause
                    self.log(f"[PAUSE] Pausing 3 seconds before next search...\n", "INFO")
                    time.sleep(3)
        
        # Remove duplicates
        unique_datasets = []
        seen_urls = set()
        for ds in all_datasets:
            url = ds.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_datasets.append(ds)
        
        self.log(f"\n Found {len(unique_datasets)} unique CSV datasets across all repositories", "SUCCESS")
        
        if not unique_datasets:
            self.log(" No CSV datasets found. Try different search terms.", "ERROR")
            return
        
        # Analyze ML suitability
        self.log("\n Analyzing ML suitability of datasets...", "STATUS")
        ml_suitable_datasets = []
        
        for i, ds in enumerate(unique_datasets, 1):
            self.log(f"   Analyzing dataset {i}/{len(unique_datasets)}...", "INFO")
            analysis = self.analyze_ml_suitability(ds)
            ds['ml_analysis'] = analysis
            
            if analysis.get('ml_suitable') and analysis.get('ml_score', 0) >= 5:
                ml_suitable_datasets.append(ds)
                self.log(f"    ML Score: {analysis.get('ml_score')}/10 - {ds.get('title', 'Unknown')}", "SUCCESS")
        
        # Sort by ML score
        ml_suitable_datasets.sort(key=lambda x: x.get('ml_analysis', {}).get('ml_score', 0), reverse=True)
        
        self.log(f"\n Found {len(ml_suitable_datasets)} ML-suitable datasets", "SUCCESS")
        self.found_datasets = ml_suitable_datasets
        
        # Save list
        json_file, csv_file = self.save_dataset_list(ml_suitable_datasets, user_query)
        
        # Attempt downloads
        self.log("\n  Attempting to download top datasets...", "STATUS")
        download_count = 0
        
        for i, dataset in enumerate(ml_suitable_datasets[:5]):
            url = dataset.get('url', '')
            if not url:
                continue
            
            self.log(f"\n Dataset {i+1}/5:", "INFO")
            self.log(f"   Title: {dataset.get('title', 'Unknown')}", "INFO")
            self.log(f"   ML Score: {dataset.get('ml_analysis', {}).get('ml_score')}/10", "INFO")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ml_dataset_{timestamp}_{i+1}.csv"
            
            result = self.download_csv_dataset(url, filename)
            if result:
                download_count += 1
                dataset['downloaded'] = True
                dataset['local_path'] = result['filepath']
                dataset['validation'] = result['validation']
        
        # Final summary
        self.log("\n" + "="*70, "SUCCESS")
        self.log(" SEARCH COMPLETE!", "SUCCESS")
        self.log("="*70, "SUCCESS")
        self.log(f" Total datasets found: {len(ml_suitable_datasets)}", "SUCCESS")
        self.log(f" Successfully downloaded: {download_count}", "SUCCESS")
        self.log(f" Results saved to: {csv_file}", "SUCCESS")
        if download_count > 0:
            self.log(f" CSV files saved in: {self.datasets_folder}/", "SUCCESS")
        self.log("="*70 + "\n", "SUCCESS")


def main():
    """Main entry point"""
    # Set UTF-8 encoding for console output
    import sys
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    try:
        print("\n" + "="*70)
        print("  [AI] ML DATASET FINDER - CSV Only")
        print("  [WEB] Browser Integration - See What's Being Searched")
        print("="*70 + "\n")
        
        user_query = input("Enter your ML dataset search query: ").strip()
        
        if not user_query:
            print("Error: Query cannot be empty")
            return
        
        print("\n[!] IMPORTANT: Browser tabs will open for each repository search.")
        print("    You'll be able to see exactly what the agent is searching.\n")
        
        finder = DatasetFinder(model='llama3.2')
        
        try:
            finder.find_datasets(user_query)
        except KeyboardInterrupt:
            print("\n\n[!] Search interrupted by user")
        except Exception as e:
            print(f"\n[X] Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
    except UnicodeEncodeError:
        # Fallback for encoding errors
        print("\n" + "="*70)
        print("  ML DATASET FINDER - CSV Only")
        print("  Browser Integration - See What's Being Searched")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()