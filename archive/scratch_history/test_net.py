import urllib.request
try:
    with urllib.request.urlopen("https://export.arxiv.org/api/query?search_query=ti:slip&max_results=1", timeout=5) as res:
        print("ArXiv Status:", res.status)
except Exception as e:
    print("ArXiv Error:", e)
