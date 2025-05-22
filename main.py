# Standard library imports
import asyncio
import websockets
from datetime import datetime
# Local imports
from pronto import *
from mainbot import MainBot
from accesstoken import getAccesstoken

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Info Location:
API_BASE_URL = "https://stanfordohs.pronto.io/"
accesstoken = getAccesstoken()
USER_ID = "5301889"
INT_USER_ID = 5301889
MAIN_BUBBLE_ID = "3832006"
ORG_ID = 2245

async def keep_alive(websocket, interval=30):
    """Sends a ping event periodically to keep the connection alive."""
    try:
        while True:
            ping_message = json.dumps({"event": "pusher:ping", "data": {}})
            await websocket.send(ping_message)
            await asyncio.sleep(interval)
    except websockets.exceptions.ConnectionClosedOK:
        # Connection closed normally
        logger.info("WebSocket connection closed cleanly")
    except websockets.exceptions.ConnectionClosedError as e:
        # Unexpected disconnection
        logger.error(f"WebSocket connection closed unexpectedly: {e}")

    except Exception as e:
        # Catch-all for other issues
        logger.error(f"Error in keep-alive: {e}")


class BanBot:
    """Main bot class for managing polls, games and commands."""

    def __init__(self):
        self.access_token = getAccesstoken()
        self.pending_banishes = {}
        self.pending_unbanishes = {}
        self.warning_count = []
        self.settings = [1, 1, 1, 1, 1]
        self.banished = []
        self.is_bot_owner = False
        self.bubble_owners = []
        self.main_bot = MainBot(MAIN_BUBBLE_ID)
        self.process_messages = True
        self.last_activity_time = datetime.min
        self.stored_messages = []
        self.events = []
        self.beta_testers = [6056537, 5301921, 5301889]
        # Rules lists
        self.adminrules = []
        self.rules = []

        if MAIN_BUBBLE_ID == "3832006":
            self.adminrules.append(
                "https://docs.google.com/document/d/1pYLhxWIXCVS49JT3aBVMjMlXQmPQbxkgjQjEXj87dSA/edit?tab=t.0")
            self.rules.append(
                "https://docs.google.com/document/d/17PhM0JfKHGlqzJ0OBohS4GQEAuc-ea0accY-lGU6zzs/edit?usp=sharing")

    async def connect_and_listen(self, bubble_id, bubble_sid):
        """Connect to the websocket and listen for messages."""
        uri = "wss://ws-mt1.pusher.com/app/f44139496d9b75f37d27?protocol=7&client=js&version=8.3.0&flash=false"
        try:
            async with websockets.connect(uri) as websocket:
                response = await websocket.recv()
                logger.info(f"Received: {response}")

                # Start keep-alive in the background

                asyncio.create_task(keep_alive(websocket))
                data = json.loads(response)
                if "data" in data:
                    inner_data = json.loads(data["data"])
                    socket_id = inner_data.get("socket_id", None)

                    data = {
                        "event": "pusher:subscribe",
                        "data": {
                            "channel": f"private-bubble.{bubble_id}.{bubble_sid}",
                            "auth": self.main_bot.client.chat_auth(bubble_id, bubble_sid, socket_id)
                        }
                    }
                    await websocket.send(json.dumps(data))
                    user_sub = {
                        "event": "pusher:subscribe",
                        "data": {
                            "channel": f"private-user.{INT_USER_ID}",
                            "auth": self.main_bot.client.user_auth(socket_id)
                        }
                    }
                    logger.info("Subscribing to USER channel.")
                    await websocket.send(json.dumps(user_sub))
                    if socket_id:
                        logger.info(f"Socket ID: {socket_id}")
                    else:
                        logger.warning("Socket ID not found in response")

                # Listen for incoming messages
                async for message in websocket:
                    if message == "ping":
                        await websocket.send("pong")
                    else:
                        try:
                            msg_data = json.loads(message)
                            event_name = msg_data.get("event", "")
                            if event_name == "pusher:ping":
                                await websocket.send(json.dumps({"event": "pusher:pong", "data": {}}))
                            if event_name == "App\\Events\\BubbleChanged":
                                logger.info("BubbleChanged event – resubscribing.")
                                raw_data = msg_data.get("data")
                                # parse only if it's a string
                                if isinstance(raw_data, str):
                                    try:
                                        change_data = json.loads(raw_data)
                                    except json.JSONDecodeError:
                                        logger.error("Invalid JSON in BubbleChanged data")
                                        continue
                                else:
                                    change_data = raw_data

                                bubble_obj = change_data.get("bubble", {})
                                bubble_id_from = bubble_obj.get("id")
                                if not bubble_id_from:
                                    logger.warning("No bubble.id in event data")
                                    continue
                                if bubble_id == bubble_id_from:
                                    # unsubscribe
                                    unsub = {
                                        "event": "pusher:unsubscribe",
                                        "data": {"channel": f"private-bubble.{bubble_id}.{bubble_sid}"}
                                    }
                                    await websocket.send(json.dumps(unsub))

                                    bubble_info = get_bubble_info(self.access_token, int(MAIN_BUBBLE_ID))
                                    bubble_sid = bubble_info["bubble"]["channelcode"]
                                    # subscribe again
                                    authstr = self.main_bot.client.chat_auth(bubble_id, bubble_sid, socket_id)
                                    sub = {
                                        "event": "pusher:subscribe",
                                        "data": {
                                            "channel": f"private-bubble.{bubble_id}.{bubble_sid}",
                                            "auth": authstr
                                        }
                                    }

                                    await websocket.send(json.dumps(sub))
                                    logger.info(f"Re-subscribed to bubble {bubble_id}")
                            elif event_name == "App\\Events\\MessageAdded":
                                msg_content = json.loads(msg_data.get("data", "{}"))
                                msg = msg_content.get("message", {})

                                await self.main_bot.process_message(
                                    msg.get("message", ""),
                                    msg.get("user", {}).get("firstname", "Unknown"),
                                    msg.get("user", {}).get("lastname", "User"),
                                    datetime.strptime(msg.get("created_at", ""), "%Y-%m-%d %H:%M:%S"),
                                    msg.get("messagemedia", []),
                                    msg.get("user", {}).get("id", "User"),
                                    msg.get("id", "")
                                )
                            if event_name == "App\\Events\\MarkUpdated":
                                msg_content = json.loads(msg_data.get("data", "{}"))
                                asyncio.create_task(self.main_bot.check_for_banned(
                                    msg_content.get("user_id", {})
                                ))
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            if e == "Failed to authenticate chat: 403 Client Error: Forbidden for url: https://stanfordohs.pronto.io/api/v1/pusher.auth":
                                int("a")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            # Allow the main loop to handle reconnection

async def main_loop():
    # Delete Invites
    invitedata = await getInvites(accesstoken, int(MAIN_BUBBLE_ID))
    for invite in invitedata['data']:
        await deleteInvite(accesstoken, invite['code'])

    # Get the PORT from environment variables or default to 8080

    # Create and initialize the bot
    bot = BanBot()
    # Get bubble info and owners
    bubble_info = get_bubble_info(bot.access_token, int(MAIN_BUBBLE_ID))

    bot.bubble_owners = [row["user_id"] for row in bubble_info["bubble"]["memberships"] if row["role"] == "owner"]

    if USER_ID in bot.bubble_owners:
        bot.is_bot_owner = True

    bubble_sid = bubble_info["bubble"]["channelcode"]
    logger.info(f"Connecting to bubble with SID: {bubble_sid}")

    tries = 0
    # Run the WebSocket logic with automatic reconnection
    while True:
        if tries < 3:
            try:
                await bot.connect_and_listen(int(MAIN_BUBBLE_ID), bubble_sid)
            except Exception as e:
                logger.error(f"Connection error: {e}")
                tries += 1
                # Wait before reconnecting
                await asyncio.sleep(5)
        else:
            break


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("BanBot stopped by user.")

# The above code was originally written by Taylan Derstadt
