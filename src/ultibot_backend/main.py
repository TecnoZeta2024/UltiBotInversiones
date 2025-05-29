from fastapi import FastAPI

app = FastAPI(title="UltiBot Backend")

@app.get("/")
async def read_root():
    return {"message": "Welcome to UltiBot Backend"}

# Aquí se incluirán los routers de api/v1/endpoints
