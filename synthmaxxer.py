import requests
import json
import os
from datetime import datetime
import random
import time
import re
from config import ACTIVE_CONFIG, REFUSAL_PHRASES, FORCE_RETRY_PHRASES, INFERENCE_API_ENDPOINT, HEADERS, MODEL

# Get the selected configuration
config = ACTIVE_CONFIG

# Constants

# Use the selected configuration variables
DIRECTORY_NAME = config["DIRECTORY_NAME"]
ASSISTANT_START_TAG = config["ASSISTANT_START_TAG"]
ASSISTANT_END_TAG = config["ASSISTANT_END_TAG"]
USER_START_TAG = config["USER_START_TAG"]
USER_END_TAG = config["USER_END_TAG"]
USER_FIRST_MESSAGE = config["USER_FIRST_MESSAGE"]
ASSISTANT_FIRST_MESSAGE = f"{ASSISTANT_START_TAG}\n{config['ASSISTANT_FIRST_MESSAGE']}\n\n{ASSISTANT_END_TAG}\n\n{USER_START_TAG}"
SYSTEM_MESSAGE = config["SYSTEM_MESSAGE"]

# Data payload for the API request
data = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": USER_FIRST_MESSAGE
        },
        {
            "role": "assistant",
            "content": ASSISTANT_FIRST_MESSAGE
        }
    ],
    "max_tokens": 200000,
    "temperature": 1,
    "top_p": 1,
    "top_k": 0,
    "system": SYSTEM_MESSAGE,
    "stream": True  # Enable streaming
}

min_turns = 1
start_index = 2

if config["IsInstruct"]:
    min_turns = 0
    start_index = 0

# Ensure the directory exists
os.makedirs(f"Datasets/Raw/{DIRECTORY_NAME}", exist_ok=True)

# Create a session object
session = requests.Session()


def handle_response(response_text):
    messages = re.split(f"({USER_START_TAG}|{ASSISTANT_START_TAG})", USER_START_TAG + response_text)[1:]
    gpt_turns = sum(1 for i in range(0, len(messages), 2) if messages[i] == ASSISTANT_START_TAG)

    if gpt_turns > min_turns and random.random() < 0.25:  # 25% chance of stopping and saving
        print("\n--------------------")
        print("CHECKING IF CAN SAVE? YES")
        print("--------------------")
        save_response(messages, True)
        return True
    else:
        print("\n--------------------")
        print("CHECKING IF CAN SAVE? NO")
        print("--------------------")
        return False


def generate_and_save():
    try:
        refusal_pattern = re.compile("|".join(REFUSAL_PHRASES))
        force_retry = re.compile("|".join(FORCE_RETRY_PHRASES))
        # Send the request to the proxy using the session object
        with session.post(INFERENCE_API_ENDPOINT, headers=HEADERS, json=data, stream=True) as response:
            # Check if the request was successful
            response.raise_for_status()

            print("Claude is generating a response...")
            full_response = ""
            accumulated_content = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8').lstrip('data: '))
                        if chunk['type'] == 'content_block_delta':
                            content = chunk['delta']['text']
                            accumulated_content += content
                            print(content, end='', flush=True)
                            full_response += content
                            if accumulated_content.endswith(ASSISTANT_END_TAG):
                                if handle_response(full_response):
                                    break
                            if refusal_pattern.search(accumulated_content):
                                print("\nRefusal detected. Restarting...")
                                return
                            if force_retry.search(accumulated_content):
                                print("\nBanned phrase, REDO!")
                                return
                        elif chunk['type'] == 'message_stop':
                            pass  # Ignore message_stop, we're checking for CLAUDE_END_TAG instead
                    except json.JSONDecodeError:
                        pass
                    except KeyError:
                        pass

            if not full_response.endswith(ASSISTANT_END_TAG):  # If the response didn't stop and save
                save_response(full_response, False)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def save_response(messages, preprocessed):


    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"Datasets/Raw/{DIRECTORY_NAME}/{timestamp}_claude_opus_synthstruct.jsonl"

    # Split the response into user and assistant messages
    if not preprocessed:
        messages = re.split(f"({USER_START_TAG}|{ASSISTANT_START_TAG})", USER_START_TAG + messages)[1:]

    structured_messages = [
        {
            "from": "system",
            "value": SYSTEM_MESSAGE
        },
    ]

    for i in range(start_index, len(messages), 2):
        role = "human" if messages[i] == USER_START_TAG else "gpt"
        content = messages[i + 1].strip().replace(USER_END_TAG, "").replace(ASSISTANT_END_TAG, "")
        structured_messages.append({"from": role, "value": content})

    # Create the ShareGPT JSON format
    sharegpt_data = {
        "id": timestamp,
        "conversations": structured_messages
    }

    # Save the JSON data to a file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)

    print(f"\nResponse has been saved to {filename}")


if __name__ == "__main__":
    # Main loop
    while True:
        generate_and_save()

        # Random delay between ~0.1-0.5 seconds
        delay = random.uniform(0.1, 0.5)
        print(f"\nWaiting for {delay:.2f} seconds before the next generation...")
        time.sleep(delay)
