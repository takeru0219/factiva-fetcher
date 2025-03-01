import logging

from src.api.streamer import FactivaStreamer
from src.pubsub.publisher import publish_message


def main():
    logging.basicConfig(level=logging.INFO)

    streamer = FactivaStreamer()

    # ストリーミングデータを受信し、Pub/Subに発行
    for data in streamer.stream():
        publish_message(data)
        logging.info(f"Published message: {data['id']}")


if __name__ == "__main__":
    main()
