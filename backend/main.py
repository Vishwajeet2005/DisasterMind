from api.main import app

import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("api.main:app", host=host, port=8000, reload=True)
