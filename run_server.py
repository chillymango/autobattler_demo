from telnetlib import IP
from server.app import *

if __name__ == "__main__":
    print('Running server')
    uvicorn.run(app, host='0.0.0.0', port=8000)
