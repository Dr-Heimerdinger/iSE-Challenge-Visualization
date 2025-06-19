import requests
import os

def get_api_example(api_url, payload):
    """
    Calls the model's API with the prepared payload to get an example output.
    Supports both JSON and file uploads (multipart/form-data).
    """
    print("\n--- STEP 3: Fetching an Example from the Model's API ---")
    if not payload:
        print("No payload to send.")
        return None

    files_to_send = {}
    json_payload = {}
    is_multipart = False

    # Separate file paths from other JSON data
    for key, value in payload.items():
        if isinstance(value, str) and os.path.exists(value) and os.path.isfile(value):
            files_to_send[key] = open(value, 'rb')
            is_multipart = True
        else:
            json_payload[key] = value

    try:
        if is_multipart:
            print(f"Sending POST request (multipart) to {api_url}...")
            # For multipart, send non-file data in the 'data' field
            response = requests.post(api_url, data=json_payload, files=files_to_send)
        else:
            print(f"Sending POST request (json) to {api_url}...")
            # For pure JSON, send the original payload
            response = requests.post(api_url, json=payload)

        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        api_output = response.json()
        print("Successfully fetched API example.")
        return api_output
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None
    finally:
        # Ensure all opened files are closed
        for f in files_to_send.values():
            f.close()