import asyncio
import uvicorn
import os

if os.name == 'nt': # Solo para Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    uvicorn.run("src.ultibot_backend.main:app", host="127.0.0.1", port=8000)
