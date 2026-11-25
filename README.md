# Run locally
1) Install Python 3.11 or above.
2) Open PowerShell in the project folder.
3) Create a virtual environment : py -m venv .venv
4) Install dependencies: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
5) Copy .env.example to .env and set GEMINI_API_KEY.
6) X-Analysis-Key generate command : .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
7) Start the server : .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 4000
8) Test the API in Postman : here i mention curl 
```
postman request POST 'http://localhost:4000/link-analysis' \
  --header 'X-Analysis-Key: {{Analysis-Key}}' \
  --header 'Content-Type: application/json' \
  --body '{
    "url":"https://example.com"
}'
``` 
