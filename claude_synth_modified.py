import requests
import json
import os
from datetime import datetime
import random
import time
import re
from config import CONFIGS, REFUSAL_PHRASES, FORCE_RETRY_PHRASES, INFERENCE_API_ENDPOINT, INFERENCE_API_KEY
# Specify the desired configuration
selected_config = "baseline_claude"  # Change this to the desired configuration key

# Get the selected configuration
config = CONFIGS[selected_config]

# Constants

# Use the selected configuration variables
DIRECTORY_NAME = config["DIRECTORY_NAME"]
ASSISTANT_START_TAG = config["ASSISTANT_START_TAG"]
ASSISTANT_END_TAG = config["ASSISTANT_END_TAG"]
USER_START_TAG = config["USER_START_TAG"]
USER_END_TAG = config["USER_END_TAG"]
USER_FIRST_MESSAGE = config["USER_FIRST_MESSAGE"]
ASSISTANT_FIRST_MESSAGE = f"{ASSISTANT_START_TAG}\n{config['ASSISTANT_FIRST_MESSAGE']}\n\n{ASSISTANT_END_TAG}\n\n{USER_START_TAG}"

# Headers for the API request
headers = {
    "Content-Type": "application/json",
    "X-API-Key": INFERENCE_API_KEY,
    "anthropic-version": "2023-06-01"
}

# Data payload for the API request
data = {
    "model": "claude-3-opus-20240229",
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
    "max_tokens": 32876,
    "temperature": 1,
    "top_p": 1,
    "top_k": 0,
    "system": "[Begin]\n<chat_history>",
    "stream": True  # Enable streaming
}

# Ensure the uncurated_raw_gens directory exists
os.makedirs(f"Datasets/Raw/{DIRECTORY_NAME}", exist_ok=True)

# Create a session object
session = requests.Session()

def handle_response(response_text):
    if random.random() < 0.25:  # 25% chance of stopping and saving
        print("\n--------------------")
        print("CHECKING IF CAN SAVE? YES")
        print("--------------------")
        save_response(response_text)
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
        with session.post(INFERENCE_API_ENDPOINT, headers=headers, json=data, stream=True) as response:
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
                save_response(full_response)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def save_response(full_response):
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"Datasets/Raw/{DIRECTORY_NAME}/{timestamp}_claude_opus_synthstruct.txt"

    # Export the finished generation with USER_START_TAG at the start
    with open(filename, "w", encoding="utf-8") as f:
        if full_response.startswith('\n'):
            f.write(USER_START_TAG + full_response)
        else:
            f.write(USER_START_TAG + "\n" + full_response)
    print(f"\nResponse has been saved to {filename}")

# Main loop
while True:
    generate_and_save()

    # Random delay between ~0.1-0.5 seconds
    delay = random.uniform(0.1, 0.5)
    print(f"\nWaiting for {delay:.2f} seconds before the next generation...")
    time.sleep(delay)
