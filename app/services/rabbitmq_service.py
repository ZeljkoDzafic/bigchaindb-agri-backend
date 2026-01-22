"""RabbitMQ service for message queue management."""

import json
from typing import Any, Callable, Optional

import pika
from pika.exceptions import AMQPConnectionError

from app.config import get_settings

settings = get_settings()


class RabbitMQService:
    """Service for interacting with RabbitMQ."""

    def __init__(self):
        """Initialize RabbitMQ connection parameters."""
        self.connection_params = pika.URLParameters(settings.rabbitmq_url)
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None

    def connect(self) -> bool:
        """Establish connection to RabbitMQ.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            self._setup_exchange_and_queue()
            return True
        except AMQPConnectionError:
            return False

    def _setup_exchange_and_queue(self) -> None:
        """Set up the exchange and queue."""
        if self.channel is None:
            return

        # Declare exchange
        self.channel.exchange_declare(
            exchange=settings.rabbitmq_exchange,
            exchange_type="topic",
            durable=True,
        )

        # Declare queue
        self.channel.queue_declare(
            queue=settings.rabbitmq_queue,
            durable=True,
        )

        # Bind queue to exchange
        self.channel.queue_bind(
            queue=settings.rabbitmq_queue,
            exchange=settings.rabbitmq_exchange,
            routing_key="sensor.#",
        )

    def publish(
        self,
        message: dict[str, Any],
        routing_key: str = "sensor.data",
    ) -> bool:
        """Publish a message to the queue.

        Args:
            message: Message to publish
            routing_key: Routing key for the message

        Returns:
            True if published successfully, False otherwise
        """
        if self.channel is None:
            if not self.connect():
                return False

        try:
            self.channel.basic_publish(
                exchange=settings.rabbitmq_exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json",
                ),
            )
            return True
        except Exception:
            return False

    def consume(
        self,
        callback: Callable[[dict[str, Any]], None],
        auto_ack: bool = False,
    ) -> None:
        """Start consuming messages from the queue.

        Args:
            callback: Function to call for each message
            auto_ack: Whether to auto-acknowledge messages
        """
        if self.channel is None:
            if not self.connect():
                raise ConnectionError("Failed to connect to RabbitMQ")

        def on_message(channel, method, properties, body):
            message = json.loads(body)
            callback(message)
            if not auto_ack:
                channel.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=settings.rabbitmq_queue,
            on_message_callback=on_message,
            auto_ack=auto_ack,
        )
        self.channel.start_consuming()

    def close(self) -> None:
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
