import json

def find_sessions_recursively(data):
    """
    Recursively search for objects that look like sessions (have a 'messages' key).
    """
    sessions = []
    if isinstance(data, dict):
        # If the current dictionary has a 'messages' key, it's a session.
        if 'messages' in data and isinstance(data['messages'], list):
            sessions.append(data)
        # Otherwise, recurse into its values.
        else:
            for key, value in data.items():
                sessions.extend(find_sessions_recursively(value))
    elif isinstance(data, list):
        # If it's a list, recurse into its items.
        for item in data:
            sessions.extend(find_sessions_recursively(item))
    return sessions

try:
    with open('layers/data/L2.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find all session-like objects in the loaded data
    all_sessions = find_sessions_recursively(data)
    print(f"Found {len(all_sessions)} potential session objects.")

    chat_data = []
    for session in all_sessions:
        chat_data.append({
            'session_id': session.get('session_id', 'N/A'),
            'messages': session['messages']
        })

    # Write the extracted chat data to a new JSON file
    with open('layers/data/L2-chat.json', 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully extracted chat data. Found and wrote {len(chat_data)} sessions to layers/data/L2-chat.json")
    if not chat_data:
        print("Warning: No sessions with a 'messages' key were found in the file.")

except FileNotFoundError:
    print("Error: layers/data/L2.json not found.")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON from L2.json: {e}. The file might be malformed.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
