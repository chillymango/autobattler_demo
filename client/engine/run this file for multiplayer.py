import json
import uuid

with open('current_player.json', 'w+') as playerfile:

    playerfile.write(json.dumps(dict(name="Your Name", id =str(uuid.uuid4()))))

# python client/screens/battle_window.py
