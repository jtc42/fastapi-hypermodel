import uvicorn

if __name__ == "__main__":
    uvicorn.run("examples.hal.app:app", host="127.0.0.1", port=8000, reload=True)
