import json
import os
import sys

try:
    import requests
except ImportError:
    print("requests module is required. Please install it.")
    sys.exit(1)

def main():
    os.makedirs("outputs", exist_ok=True)
    urls = [
        "https://www.python.org",
        "https://github.com",
        "https://groq.com"
    ]
    
    results = []
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            # Find title tag simply without full HTML parser to keep it simple
            if "<title>" in response.text:
                title = response.text.split("<title>")[1].split("</title>")[0]
            else:
                title = "No title found"
                
            results.append({
                "url": url,
                "title": title.strip()
            })
        except requests.RequestException as e:
            results.append({
                "url": url,
                "title": f"ERROR: {str(e)}"
            })
            
    output_data = {
        "task": "fetch web titles",
        "status": "success",
        "results": results
    }
    
    with open("outputs/results.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print("Web titles fetched and saved to outputs/results.json.")

if __name__ == "__main__":
    main()
