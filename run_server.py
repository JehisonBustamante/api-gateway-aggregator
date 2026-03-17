import uvicorn
from main import app

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        import traceback
        traceback.print_exc()
