import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)
p = r.pubsub()
p.subscribe('test_message')
while True:
    message = p.get_message()
    if message:
        print(message['data'])
