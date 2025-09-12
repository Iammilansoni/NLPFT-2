import requests
import json

def test_convert():
    url = "http://localhost:8000/api/v1/convert/"
    
    data = {
        "text": "Login with username admin and password secret123, go to www.google.com"
    }
    
    try:
        print("Testing:", data["text"])
        response = requests.post(url, 
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(data))
        
        print("Status:", response.status_code)
        if response.status_code == 200:
            result = response.json()
            functions = result.get('functions', [])
            print(f"Found {len(functions)} functions:")
            for func in functions:
                print(f"- {func['function']}: {func['args']} (confidence: {func['confidence']:.2f})")
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print("Exception:", str(e))

if __name__ == "__main__":
    test_convert()