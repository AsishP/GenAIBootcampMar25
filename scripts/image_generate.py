import requests
import os
import json
from dotenv import load_dotenv
load_dotenv()

def generate_image(prompt, style):
    """
    Generate an image using the Stability AI API.
    
    Args:
        prompt (str): The text prompt for image generation.
        
    Returns:
        bytes: The generated image data.
    """
    # Set the API key and endpoint
    api_key = os.getenv("STABILITY_API_KEY")
    api_endpoint = os.getenv("STABILITY_API_ENDPOINT")
    response = requests.post(
        api_endpoint,
        headers={
            "authorization": f"Bearer {api_key}",
            "accept": "application/json"
        },
        files={"none": ''},
        data={
            "prompt": prompt,
            "output_format": "png",
            "style_preset": style if style else "photographic"
        },
    )

    if response.status_code == 200:
        print("Image generation successful!")
        json_response = json.loads(response.content.decode('utf-8'))
        return json_response['image']
    else:
        raise Exception(str(response.json()))

