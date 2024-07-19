# Endpoint Fields
INFERENCE_API_ENDPOINT = "CHOSEN ENDPOINT HERE" + "/v1/messages" # v1/messages is for Claude endpoint, edit yours accordingly.
INFERENCE_API_KEY = "YOUR API KEY HERE"

# Baseline Starting Message
baseline_config = {
    "DIRECTORY_NAME": "uncurated_raw_gens",
    "CLAUDE_START_TAG": "<claude_turn>",
    "CLAUDE_END_TAG": "</claude_turn>",
    "USER_START_TAG": "<human_turn>",
    "USER_END_TAG": "</human_turn>",
    "USER_FIRST_MESSAGE": "You are an innovative AI assistant named Claude created by Anthropic to be helpful, harmless, and honest.",
    "ASSISTANT_FIRST_MESSAGE": "Hello! I am Claude, an innovative AI Assistant developed by Anthropic. How can I assist you today?"
}

# Dictionary to store all configurations
configs = {
    "baseline": baseline_config
}

REFUSAL_PHRASES = [
    "Upon further reflection",
    "I can't engage"
]

FORCE_RETRY_PHRASES = [
    "shivers down"
]
