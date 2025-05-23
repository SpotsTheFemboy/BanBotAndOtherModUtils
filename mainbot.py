# Standard library imports
import re
import uuid
from datetime import timezone, datetime
from pronto import *
from accesstoken import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_BASE_URL = "https://stanfordohs.pronto.io/"
USER_ID = "5301889"
INT_USER_ID = 5301889
MAIN_BUBBLE_ID = "3832006"
admin_bubble_id = "4206470"
ORG_ID = 2245

def try_send_emoji(emoji, msg_id):
    responce = send_reaction(accesstoken, emoji, msg_id)
    print(responce)
    if responce['message'] == 'The given data was invalid.':
        emoji = emoji.strip("\n")
        emoji = emoji + '️'
        responce = send_reaction(accesstoken, emoji, msg_id)
        if responce['message'] == 'The given data was invalid.':
            logger.error(responce)

class ProntoClient:
    """Handles communication with the Pronto API."""

    def __init__(self, api_base_url, access_token):
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        self.stored_dms = []

    def send_message(self, message, bubble_id, media):
        """Send a message to a specific bubble."""
        if media is None:
            media = []

        unique_uuid = str(uuid.uuid4())
        message_created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "id": "Null",
            "uuid": unique_uuid,
            "bubble_id": bubble_id,
            "message": message,
            "created_at": message_created_at,
            "user_id": USER_ID,
            "attachment_file_keys": media
        }
        url = f"{self.api_base_url}api/v1/message.create"

        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {e}")
            raise BackendError(f"Failed to send message: {e}")

    def get_dm_or_create(self, user_id):
        """Get an existing DM or create a new one with the specified user."""
        matches = [row for row in self.stored_dms if row[0] == user_id]
        if not matches:
            dm_info = createDM(self.access_token, user_id, ORG_ID)
            data = [user_id, dm_info]
            self.stored_dms.append(data)
            matches = [data]
        return matches[0][1]
    def user_auth(self, socket_id: str) -> str:
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {accesstoken}",
        })
        resp = session.post(
            f"{API_BASE_URL}api/v1/pusher.auth",
            json={
                "socket_id": socket_id,
                "channel_name": f"private-user.{INT_USER_ID}"
            },
        )
        resp.raise_for_status()
        return resp.json().get("auth", "")
    def chat_auth(self, bubble_id, bubble_sid, socket_id):
        """Authenticate for chat websocket connection."""
        url = f"{self.api_base_url}api/v1/pusher.auth"
        data = {
            "socket_id": socket_id,
            "channel_name": f"private-bubble.{bubble_id}.{bubble_sid}"
        }
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            bubble_auth = response.json().get("auth")
            logger.info("Bubble Connection Established.")
            return bubble_auth
        except Exception as e:
            logger.error(f"Error authenticating chat: {e}")
            raise BackendError(f"Failed to authenticate chat: {e}")
    def org_auth(self, bubble_id, bubble_sid, socket_id):
        """Authenticate for chat websocket connection."""
        url = f"{self.api_base_url}api/v1/pusher.auth"
        data = {
            "socket_id": socket_id,
            "channel_name": "private-user.5301889"
        }
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            bubble_auth = response.json().get("auth")
            logger.info("Bubble Connection Established.")
            return bubble_auth
        except Exception as e:
            logger.error(f"Error authenticating chat: {e}")
            raise BackendError(f"Failed to authenticate chat: {e}")
    def upload_file_and_get_key(self, file_path, filename):
        """Upload a file to Pronto and get the file key."""
        url = "https://api.pronto.io/api/files"
        try:
            # Open the file and prepare headers
            with open(file_path, 'rb') as file:
                file_content = file.read()

            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "Content-Length": str(len(file_content)),
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/octet-stream"
            }

            # Send the PUT request
            response = requests.put(url, headers=headers, data=file_content)

            # Check if the request was successful
            if response.status_code == 200:
                response_data = response.json()
                file_key = response_data['data']['key']
                return file_key
            else:
                logger.error(f"Failed to upload file: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
class MainBot:
    """Main bot class"""

    def __init__(self, main_bubble):
        self.access_token = getAccesstoken()
        self.client = ProntoClient(API_BASE_URL, self.access_token)
        global MAIN_BUBBLE_ID
        MAIN_BUBBLE_ID = main_bubble
        self.inviters = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "inviters.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.inviters = json.load(f)
        except Exception as e:
            logger.error(e)

        self.chat_info = get_bubble_info(accesstoken, int(MAIN_BUBBLE_ID))
        self.bubble_owners = [row["user_id"] for row in self.chat_info["bubble"]["memberships"] if row["role"] == "owner"]
        self.bans = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, "bans.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as openfile:
                # Reading from json file
                self.bans = [int(line) for line in openfile]
        except Exception as e:
            print(e)
        self.process_messages = True

    def is_seven_digit_number(self, s):
        """Check if a string is a seven-digit number."""
        return bool(re.match(r'^\d{7}$', s))

    async def check_for_banned(self, user_id):
        tempinviters = []


        if user_id not in self.bans:
            return

        await kickUserFromBubble(accesstoken, int(MAIN_BUBBLE_ID), [user_id])
        invitedata = await getInvites(accesstoken, int(MAIN_BUBBLE_ID))

        processed_users = set()

        for invite in invitedata.get('data', []):
            await deleteInvite(accesstoken, invite['code'])

            user_id = invite['user_id']

            if user_id in processed_users:
                continue  # Already counted this user in this batch

            processed_users.add(user_id)
            if user_id not in tempinviters:
                tempinviters.append(user_id)

            # Check if user is already tracked
            for inviter in self.inviters:
                if inviter['user_id'] == user_id:
                    inviter['count'] += 1
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    file_path = os.path.join(script_dir, "inviters.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.inviters, f, indent=2)
                    if inviter['count'] >= 5:
                        self.bans.append(user_id)
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        file_path = os.path.join(script_dir, "bans.txt")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(f"{item}\n" for item in self.bans)
                        await kickUserFromBubble(accesstoken, int(MAIN_BUBBLE_ID), [user_id])
                        self.client.send_message(
                            f"<@{user_id}> has made invite links after a banned user rejoined 5 times, so they are now banned.",
                            int(admin_bubble_id),
                            None
                        )
                    break
            else:
                # Not found in inviters, add with count 1
                self.inviters.append({'user_id': user_id, 'count': 1})

                # Save inviters to inviters.txt
                script_dir = os.path.dirname(os.path.abspath(__file__))
                inviters_file_path = os.path.join(script_dir, "inviters.json")
                with open(inviters_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.inviters, f, indent=2)


    async def process_message(self, msg_text, user_firstname, user_lastname, timestamp, msg_media, user_id, msg_id):
        """Process an incoming message."""
        # Check for bot toggling command
        if msg_text.startswith("!bot"):
            command = msg_text[1:].split()
            print(command)
            if len(command) > 1 and user_id in self.bubble_owners:
                if command[1] == "on":
                    self.process_messages = True
                    logger.info(f"Bot enabled by {user_id}")
                    send_reaction(accesstoken, '💡', msg_id)
                elif command[1] == "off":
                    self.process_messages = False
                    logger.info(f"Bot disabled by {user_id}")
                    send_reaction(accesstoken, '📴', msg_id)

        if not self.process_messages:
            return

        await self.check_for_commands(msg_text, user_id, msg_id)


    async def check_for_commands(self, msg_text_tall, user_id, msg_id):
        """Check for commands in the message and handle them."""

        msg_text = msg_text_tall.lower()
        command = msg_text[1:].split()
        if user_id in self.bubble_owners:

            if msg_text.lower().startswith("!pin "):
                message = msg_text[5::]
                self.chat_info = get_bubble_info(accesstoken, int(MAIN_BUBBLE_ID))
                pinned_message = self.chat_info['bubble']['pinned_message']
                try_send_emoji("📌", msg_id)
                if pinned_message['user_id'] != INT_USER_ID:
                    pinned_message = await self.client.send_message(message, int(MAIN_BUBBLE_ID), [])
                    pinMessage(accesstoken, pinned_message['message']['id'], "2031-11-11 11:11:11")
                else:
                    editMessage(accesstoken, message, pinned_message['id'])

            if msg_text.lower().startswith("!atpin "):
                message = msg_text[7::]
                self.chat_info = get_bubble_info(accesstoken, int(MAIN_BUBBLE_ID))
                pinned_message = self.chat_info['bubble']['pinned_message']
                try_send_emoji("📌", msg_id)
                if pinned_message['user_id'] != INT_USER_ID:
                    pinned_message = await self.client.send_message(message, int(MAIN_BUBBLE_ID), [])
                    pinMessage(accesstoken, pinned_message['message']['id'], "2031-11-11 11:11:11")
                else:
                    newmessage = pinned_message['message'] + "\n" + message
                    editMessage(accesstoken, newmessage, pinned_message['id'])

            if msg_text.startswith("!ban"):
                target_match = re.search(r"<@(\d+)>", command[1])
                if target_match:
                    target_user = int(target_match.group(1))
                    if target_user not in self.bans:
                        self.bans.append(target_user)
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        file_path = os.path.join(script_dir, "bans.txt")
                        with open(file_path, 'w', encoding="utf-8") as openfile:
                            for item in self.bans:
                                openfile.write(str(item) + '\n')
                        await kickUserFromBubble(accesstoken, int(MAIN_BUBBLE_ID), [target_user])

            if msg_text.startswith("!unban"):
                target_match = re.search(r"<@(\d+)>", command[1])
                if target_match:
                    target_user = int(target_match.group(1))
                    if target_user in self.bans:
                        self.bans.remove(target_user)
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        file_path = os.path.join(script_dir, "bans.txt")
                        with open(file_path, 'w', encoding="utf-8") as openfile:
                            for item in self.bans:
                                openfile.write(str(item) + '\n')
                        await addMemberToBubble(accesstoken, int(MAIN_BUBBLE_ID), [target_user])
            if msg_text.startswith("!poll "):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, "pollinfo.json")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_poll_info = json.load(f)
                except Exception as e:
                    logger.error(e)
                    all_poll_info = []
                message = msg_text_tall[6::]
                message_to_send = f"Poll #{all_poll_info.__len__()+1}:\n" + message
                poll_message = self.client.send_message(message_to_send, int(MAIN_BUBBLE_ID), [])
                send_reaction(accesstoken, '✅️', poll_message['message']['id'])
                send_reaction(accesstoken, '❌️', poll_message['message']['id'])
                all_poll_info.append(
                    {
                        "message": message,
                        "message_id": poll_message['message']['id'],
                        "poll_id": all_poll_info.__len__()+1,
                        "poll_type": 1
                    }
                )
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, "pollinfo.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_poll_info, f, indent=4)
            if msg_text.startswith("!advpoll "):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, "pollinfo.json")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_poll_info = json.load(f)
                except Exception as e:
                    logger.error(e)
                    all_poll_info = []
                message = msg_text_tall[9::]
                message_to_send = f"Poll #{all_poll_info.__len__()+1}:\n" + message
                poll_message = self.client.send_message(message_to_send, int(MAIN_BUBBLE_ID), [])
                all_poll_info.append(
                    {
                        "message": message,
                        "message_id": poll_message['message']['id'],
                        "poll_id": all_poll_info.__len__()+1,
                        "poll_type": 2
                    }
                )
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, "pollinfo.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_poll_info, f, indent=4)

            if msg_text.startswith("!getpoll "):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, "pollinfo.json")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_poll_info = json.load(f)
                except Exception as e:
                    logger.error(e)
                    all_poll_info = []

                if command.__len__() != 2:
                    return
                try:
                    target_poll_id = int(command[1])
                except Exception as e:
                    return

                if target_poll_id > all_poll_info.__len__() or target_poll_id < 1:
                    return

                message_id_of_poll = all_poll_info[target_poll_id - 1]['message_id']
                unique_uuid = str(uuid.uuid4())
                message_created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                send_message_to_bubble(accesstoken, int(MAIN_BUBBLE_ID), message_created_at, "Check out the poll here!", INT_USER_ID, unique_uuid, message_id_of_poll)
            if msg_text.startswith("!checkpoll "):

                if command.__len__() != 2:
                    return

                try:
                    target_poll_id = int(command[1])
                except Exception as e:
                    return
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(script_dir, "pollinfo.json")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_poll_info = json.load(f)
                except Exception as e:
                    logger.error(e)
                    all_poll_info = []
                if target_poll_id > all_poll_info.__len__() or target_poll_id < 1:
                    return

                message_id_of_poll = all_poll_info[target_poll_id - 1]['message_id']
                info = get_bubble_thread(accesstoken, int(MAIN_BUBBLE_ID), message_id_of_poll)
                if info['parentmessages'].__len__() == 1:
                    poll_message = info['parentmessages'][0]
                elif info['parentmessages'].__len__() == 0:
                    if info['messages'].__len__() == 0:
                        return
                    poll_message = info['messages'][info['messages'].__len__() - 1]
                else:
                    return
                if poll_message['id'] != message_id_of_poll:
                    return
                reactions = poll_message['reactionsummary']
                if all_poll_info[target_poll_id -1]['poll_type'] == 1:
                    yescount = 0
                    nocount = 0
                    for reactionData in reactions:
                        if reactionData['emoji'] == '✅':
                            yescount = reactionData['count'] - 1
                        if reactionData['emoji'] == '❌':
                            nocount = reactionData['count'] - 1
                    if yescount > nocount:
                        win_message = "The majority voted Yes!"
                    elif nocount > yescount:
                        win_message = "The majority voted No!"
                    else:
                        win_message = "It's a tie!"
                    unique_uuid = str(uuid.uuid4())
                    message_created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    send_message_to_bubble(accesstoken, int(MAIN_BUBBLE_ID), message_created_at,
                                           f"The results for poll #{target_poll_id} are:\n✅ {yescount} people said yes!\n❌ {nocount} people said no!\n{win_message}", INT_USER_ID, unique_uuid, message_id_of_poll)
                if all_poll_info[target_poll_id - 1]['poll_type'] == 2:
                    to_send_message = f"The results for poll #{target_poll_id} are:\n"
                    most_common_responses = []
                    max_count = 0

                    for reactionData in reactions:
                        count = reactionData['count']
                        emoji = reactionData['emoji']
                        people = "person" if count == 1 else "people"
                        to_send_message += f"{count} {people} said {emoji}!\n"

                        # Track most common responses
                        if count > max_count:
                            max_count = count
                            most_common_responses = [emoji]
                        elif count == max_count:
                            most_common_responses.append(emoji)

                    if max_count > 0 and most_common_responses:
                        common_str = ', '.join(most_common_responses)
                        to_send_message += f"\nMost common response(s): {common_str} with {max_count} vote(s)."

                    unique_uuid = str(uuid.uuid4())
                    message_created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    send_message_to_bubble(
                        accesstoken,
                        int(MAIN_BUBBLE_ID),
                        message_created_at,
                        to_send_message,
                        INT_USER_ID,
                        unique_uuid,
                        message_id_of_poll
                    )