# Game Server
-----
How to talk to the game server
(probably want to auth this later but for now just connect to redis)
* connect to redis server for message pubsub
* should subscribe to the heartbeat channel?
* if heartbeat timestamp differs from current time by 30s, just exit

How to Join a Game
* subscribe to a list of lobbies
* select a lobby by ID
* publish a message to the following channel:
* * <lobby-id>-join
* subscribe to the following channel:
* * <lobby-id>-data
* load the string into a JSON object
* make sure that you're in there lol

How to Create a Game
* create an id <lobby-id>
* publish a message to the following channel:
* * lobby-create-request
* the above request should include a lobby ID to request
* subscribe to the following channel:
* * <lobby-id>-data
* * load any string responses into a JSON object

------
# Channels
## Lobbies
* <lobby-id>-join  : publish to this channel to join a lobby
