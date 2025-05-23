#Author: Paul Estrada
#Email: paul257@ohs.stanford.edu
#URL: https://github.com/Society451/Better-Pronto

import requests, logging
import pycurl
import json
from io import BytesIO
from dataclasses import dataclass, asdict


API_BASE_URL = "https://stanfordohs.pronto.io/"
class BackendError(Exception):
    pass
# Dataclass for device information
@dataclass
class DeviceInfo:
    browsername: str
    browserversion: str
    osname: str
    type: str
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#AUTHENTICATION FUNCTIONS
# Function to verify user email
def requestVerificationEmail(email):
    url = "https://accounts.pronto.io/api/v1/user.verify"
    payload = json.dumps({"email": email})
    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, ["Content-Type: application/json"])
        curl.setopt(pycurl.POSTFIELDS, payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        raise BackendError(f"An error occurred: {err}")

# Function to log in using email and verification code
def verification_code_to_login_token(email, verification_code):
    url = "https://accounts.pronto.io/api/v3/user.login"
    device_info = DeviceInfo(
        browsername="Firefox",
        browserversion="130.0.0",
        osname="Windows",
        type="WEB"
    )
    request_payload = {
        "email": email,
        "code": verification_code,
        "device": asdict(device_info)
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=request_payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise BackendError(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred: {req_err}")
        raise BackendError(f"Request exception occurred: {req_err}")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

def get_bubble_thread(access_token, bubbleID, threadID):
    url = f"{API_BASE_URL}api/v1/bubble.history"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {"bubble_id": bubbleID}
    if threadID is not None:
        request_payload["thread_id"] = threadID
    payload_json = json.dumps(request_payload)
    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")
#BUBBLE FUNCTIONS
# Function to get all user's bubbles
def getUsersBubbles(access_token):
    url = f"{API_BASE_URL}api/v3/bubble.list"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"  # Ensure 'Bearer' is included
    ]

    buffer = BytesIO()
    curl = pycurl.Curl()
    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to get last 50 messages in a bubble, given bubble ID
# and an optional argument of latest message ID, which will return a list of 50 messages sent before that message
def get_bubble_messages(access_token, bubbleID, latestMessageID=None):
    url = f"{API_BASE_URL}api/v1/bubble.history"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {"bubble_id": bubbleID}
    if latestMessageID is not None:
        request_payload["latest"] = latestMessageID
    payload_json = json.dumps(request_payload)

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

def send_reaction(access_token, reaction, message_id):
    url = f"{API_BASE_URL}api/clients/messages/{message_id}/reactions"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]
    request_payload = json.dumps({"emoji": reaction})

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")
#Function to get information about a bubble



def get_bubble_info(access_token, bubbleID):
    url = f"{API_BASE_URL}api/v2/bubble.info"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({"bubble_id": bubbleID})

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

#Function to mark a bubble as read
def markBubble(access_token, bubbleID, message_id=None):
    url = f"{API_BASE_URL}api/v1/bubble.mark"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {"bubble_id": bubbleID}
    if message_id is not None:
        request_payload["message_id"] = message_id
    payload_json = json.dumps(request_payload)

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")



def membershipUpdate(access_token, bubbleID, marked_unread=False):
    url = f"{API_BASE_URL}api/v1/membership.update"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "bubble_id": bubbleID,
        "marked_unread": marked_unread
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")
#Function to create DM
def createDM(access_token, user_id, orgID):
    url = f"{API_BASE_URL}api/v1/dm.create"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "organization_id": orgID,
        "user_id": user_id
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

#Function to create a bubble/group
def createBubble(access_token, orgID, title, category_id=None):
    url = f"{API_BASE_URL}api/v1/bubble.create"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {
        "organization_id": orgID,
        "title": title
    }
    if category_id is not None:
        request_payload["category_id"] = category_id
    payload_json = json.dumps(request_payload)

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")


#Function to add a member to a bubble
#people is a list of user IDs, in the form of [5302519, 5302367]


async def addMemberToBubble(access_token, bubbleID, people):
    url = f"{API_BASE_URL}api/clients/chats/{bubbleID}/memberships/batch"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({"user_ids": people})

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

#Function to kick user from a bubble
#users is a list of user IDs, in the form of [5302519]
async def kickUserFromBubble(access_token, bubbleID, users):
    url = f"{API_BASE_URL}api/v1/bubble.kick"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "bubble_id": bubbleID,
        "users": users
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")


#Function to update a bubble
#title is the new title of the bubble, in the form of a string
#category_id is the new category ID of the bubble, in the form of an integer such as 173528
#changetitle = allow "owner" or "member" to change the title of the bubble
#addmember = allow "owner" or "member" to add a member to the bubble
#leavegroup = allow "owner" or "member" to leave the bubble
#create_message = allow "owner" or "member" to create a message in the bubble
#assign_task = allow "owner" or "member" to assign a task in the bubble
#pin_message = allow "owner" or "member" to pin a message in the bubble or "null"
#changecategory = allow "owner" or "member" to change the category of the bubble
#removemember = allow "owner" or "member" to remove a member from the bubble
#create_videosession = allow "owner" or "member" to create a video session in the bubble
#videosessionrecordcloud = allow "owner" or "member" to record a video session in the cloud
#create_announcement = allow "owner" or "member" to create an announcement in the bubble

def updateBubble(access_token, bubbleID, title=None, category_id=None, changetitle=None, addmember=None,
                 leavegroup=None, create_message=None, assign_task=None, pin_message=None, changecategory=None,
                 removemember=None, create_videosession=None, videosessionrecordcloud=None, create_announcement=None):
    url = f"{API_BASE_URL}api/v1/bubble.update"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {"bubble_id": bubbleID}

    # Add optional parameters to the payload
    for key, value in {
        "title": title, "category_id": category_id, "changetitle": changetitle, "addmember": addmember,
        "leavegroup": leavegroup, "create_message": create_message, "assign_task": assign_task,
        "pin_message": pin_message, "changecategory": changecategory, "removemember": removemember,
        "create_videosession": create_videosession, "videosessionrecordcloud": videosessionrecordcloud,
        "create_announcement": create_announcement
    }.items():
        if value is not None:
            request_payload[key] = value

    payload_json = json.dumps(request_payload)

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

#Function to pin message to bubble
#Example {bubble_id: 3955365, pinned_message_id: 96930584, pinned_message_expires_at: "2025-01-18 23:12:18"}
# or send pinned_messageid: "null" to unpin the message
def pinMessage(access_token, pinned_message_id, pinned_message_expires_at):
    url = f"{API_BASE_URL}api/v1/bubble.update"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "pinned_message_id": pinned_message_id,
        "pinned_message_expires_at": pinned_message_expires_at
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")


def getUsers(access_token, cursor):
    url = f"{API_BASE_URL}api/clients/users/search?page[size]=100&filter[relation]=all"
    if cursor is not None:
        url += f"&cursor={cursor}"

    headers = [
        "Accept: application/json",
        "Authorization: Bearer " + access_token
    ]

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")


def getAllUsers(access_token):
    cursor = None
    users = []

    while True:
        data = getUsers(access_token, cursor)
        users.extend(data.get('data', []))
        cursor = data.get('cursors', {}).get('next')
        if cursor is None:
            break

    return users

async def getInvites(access_token, bubbleID):
    url = f"{API_BASE_URL}api/clients/groups/{bubbleID}/invites"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")
async def deleteInvite(access_token, code):
    url = f"{API_BASE_URL}api/clients/invites/{code}"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data) if response_data else {"status": "Success"}

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")
#Function to create invite link
#access is the access level of the invite, expiration is the expiration date of the invite
#access example: access: "internal"
#^this allows for only users with the link and who are a part of the org to join
#expiration example: expires: "2024-12-09T16:08:34.332Z"

def createInvite(bubbleID, access, expires, access_token):
    url = f"{API_BASE_URL}api/clients/groups/{bubbleID}/invites"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "access": access,
        "expires": expires
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")



#MESSAGE FUNCTIONS
# Function to send a message to a bubble
def send_message_to_bubble(access_token, bubbleID, created_at, message, userID, uuid, parentmessage_id=None):
    url = f"{API_BASE_URL}api/v1/message.create"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {
        "bubble_id": bubbleID,
        "created_at": created_at,
        "id": "Null",
        "message": message,
        "messagemedia": [],
        "user_id": userID,
        "uuid": uuid
    }

    if parentmessage_id is not None:
        request_payload["parentmessage_id"] = parentmessage_id

    payload_json = json.dumps(request_payload)
    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to add a reaction to a message [DEPRECATED?]
def addReaction(access_token, messageID, reactiontype_id):
    url = f"{API_BASE_URL}api/v1/message.addreaction"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "message_id": messageID,
        "reactiontype_id": reactiontype_id
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to remove a reaction from a message
def removeReaction(access_token, messageID, reactiontype_id):
    url = f"{API_BASE_URL}api/v1/message.removereaction"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "message_id": messageID,
        "reactiontype_id": reactiontype_id
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to edit a message
def editMessage(access_token, newMessage, messageID):
    url = f"{API_BASE_URL}api/v1/message.edit"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "message": newMessage,
        "message_id": messageID
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to delete a message
def deleteMessage(access_token, messageID):
    url = f"{API_BASE_URL}api/v1/message.delete"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "message_id": messageID
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data) if response_data else {"status": "Success"}

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")


#USER INFO FUNCTIONS
# Function to get user information
def userInfo(access_token, user_id):
    url = f"{API_BASE_URL}api/v1/user.info"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({"id": user_id})

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to get a user's mutual groups
def mutualGroups(access_token, user_id):
    url = f"{API_BASE_URL}api/v1/user.mutualgroups"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({"id": user_id})

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

# Function to set online/offline status
def setStatus(access_token, userID, isonline, lastpresencetime):
    url = f"{API_BASE_URL}api/clients/users/presence"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = json.dumps({
        "data": [
            {
                "user_id": userID,
                "isonline": isonline,
                "lastpresencetime": lastpresencetime
            }
        ]
    })

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, request_payload)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

#OTHER Functions
# Search for message function
#EXAMPLE: {search_type: "files", size: 25, from: 0, orderby: "newest", query: "hello there", user_ids: [5302419]}

def searchMessage(access_token, query, bubbleIDs=None, user_ids=None, start_date=None, end_date=None, fromnum=0, orderby=None, size=10):
    url = f"{API_BASE_URL}api/v1/message.search"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {
        "search_type": "messages",
        "size": size,
        "from": fromnum,
        "query": query
    }

    # Include optional parameters in the request payload
    for key, value in {
        "bubble_ids": bubbleIDs, "orderby": orderby, "user_ids": user_ids,
        "start_date": start_date, "end_date": end_date
    }.items():
        if value is not None:
            request_payload[key] = value

    payload_json = json.dumps(request_payload)
    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")

#{"orderby":["firstname","lastname"],"includeself":true,"bubble_id":"3640189","page":1}
def bubbleMembershipSearch(access_token, bubble_id, orderby=["firstname", "lastname"], includeself=True, page=None):
    url = f"{API_BASE_URL}/api/v1/bubble.membershipsearch"
    headers = [
        "Content-Type: application/json",
        f"Authorization: Bearer {access_token}"
    ]

    request_payload = {
        "orderby": orderby,
        "includeself": includeself,
        "bubble_id": bubble_id
    }
    if page is not None:
        request_payload["page"] = page

    payload_json = json.dumps(request_payload)
    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPHEADER, headers)
        curl.setopt(pycurl.POSTFIELDS, payload_json)
        curl.setopt(pycurl.WRITEDATA, buffer)

        curl.perform()
        curl.close()

        response_data = buffer.getvalue().decode("utf-8")
        return json.loads(response_data)

    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        raise BackendError("Failed to parse JSON response")
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise BackendError(f"An unexpected error occurred: {err}")