import redis


def test(msg):
    queue = redis.StrictRedis(host='localhost', port=6379, db=0)
    channel = queue.pubsub()
    queue.publish("test_message", msg)


if __name__ == "__main__":
    while True:
        m = input('Enter message: ')
        test(m)
