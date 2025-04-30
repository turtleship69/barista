from .__init__ import app
import uvicorn

if __name__ == "__main__":
    #run the app with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=64390)