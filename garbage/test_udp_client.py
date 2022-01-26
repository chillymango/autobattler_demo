import socket
import sys
import argparse

from engine.env import Environment
from engine.models.player import Player
from engine.models.state import State

host = 'localhost' 
data_payload = 65536
 
def echo_client(port): 
    """ A simple echo client """ 
    # Create a UDP socket 
    sock = socket.socket(socket.AF_INET, 
                         socket.SOCK_DGRAM) 
 
    server_address = (host, port) 
    print ("Connecting to %s port %s" % server_address) 
    message = 'This is the message.  It will be repeated.'
    env = Environment.create_webless_game(4)
    p1 = Player(name='Albert Yang')
    env.add_player(p1)
    state = env.state
    try: 
 
        # Send data 
        #message = "Test message. This will be echoed"
        message = state.json() * 100
        print(len(message))
        print ("Sending %s" % message)
        sent = sock.sendto(message, server_address) 
 
        # Receive response 
        data, server = sock.recvfrom(data_payload) 
        print ("received %s" % data) 
 
    finally: 
        print ("Closing connection to the server") 
        sock.close() 
 
if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='Socket Server Example') 
    parser.add_argument('--port', action="store", dest="port", type=int, required=True) 
    given_args = parser.parse_args()  
    port = given_args.port 
    echo_client(port)
