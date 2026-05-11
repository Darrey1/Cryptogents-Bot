import uvicorn 
import os 


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("src:app",
                host="0.0.0.0",
                port= port,
                reload=False )
    
    
    
