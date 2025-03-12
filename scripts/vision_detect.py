import json
import os
from openai import AzureOpenAI
import base64
from mimetypes import guess_type
from dotenv import load_dotenv 

load_dotenv() 

# Function to encode a local image into data URL 
def getbase64(image_path):
    
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"
 
## get the image base64
def get_image_filepath_base64(path):
    data_url = ""
    imagepath = path.strip()

    if (not imagepath.startswith("\\")): imagepath = "\\" + imagepath.replace("/", "\\")

    # Get the parent directory of the current script
    parent_dir = os.path.dirname(__file__)

    # Combine the parent directory and relative path to get the absolute path
    imagepath = os.path.join(os.path.dirname(parent_dir) + '\\web\\static' + imagepath)

    if not os.path.exists(imagepath):
        print("The image file does not exist. Please enter a valid path.")
        return Exception("The image file does not exist. Please enter a valid path.")
        
    # Check if http or not and return data in base64
    if not("http" in imagepath or "https" in imagepath):
        print("Encoding the image into a data URL \n")
        image_path = imagepath ## Provide the path with respect to Parent folder
        data_url = getbase64(image_path)
    
    return data_url

def getdefectdetails(imageUrl, refImageUrl, jsonpref):
    # print("Creating the Azure Open AI Client. \n")
    ## Create the Azure Open AI client
    client = AzureOpenAI(
        api_key= os.getenv("AZURE_OPENAI_API_KEY1"),  
        api_version= os.getenv("API_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT1")
    )

    deployment_name = os.getenv("VISION_DEPLOYMENT_NAME") 
    refImageData = get_image_filepath_base64(refImageUrl)
    inputImagedata = get_image_filepath_base64(imageUrl)

    sysmsg = """
    You're a professional defect detector.
    Your job is to compare the test image with reference image, please answer the question with "No defect detected" or "Defect detected", 
    also explain your decision as detail as possible. 
    """
    sysmsgjson = """
    You're a professional defect detector.
    Your job is to compare the test image with reference image, please answer the question with "No defect detected" or "Defect detected", 
    also explain your decision as detail as possible.
    Return the output in JSON format with type of defect, the location of the defect in X and Y coordinates and serverity of the defect. Also provide a defect confidence score from 0 to 1 based on the refernce image.
    """
    print("Calling Azure Open AI endpoint to analyse the image. Waiting for response.. \n")
    ## Call the Azure Open AI endpoint to analyse the image using the local Data Url
    response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        { "role": "system", "content": sysmsgjson if jsonpref.lower() == '1' else sysmsg},
        { "role": "user", "content": [
            {
                "type": "text",
                "text": "Here is the reference image",  # Pass the prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"{refImageData}"  # Pass the encoded reference image
                },
            },
            {
                "type": "text",
                "text": "Here is the test image",  # Pass the prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"{inputImagedata}"  # Pass the encoded test image
                }, 
            },
        ],
        } 
    ],
    max_tokens=2000 
    )

    ## Print the response from the Azure Open AI endpoint
    print("Got response from the Azure Open AI endpoint \n")
    responseval = response.choices[0].message.content

    if responseval == "":
        print("No response from the model")
        exit();

    if "json" in responseval:
        s = responseval
        # Remove '```json\n' from the start and '\n```' from the end
        s = s[7:-4]
        responseval = s
        print("Outputting the response \n")
        responsejson = json.loads(responseval)
        pretty_object = json.dumps(responsejson, indent=4)
        print("Response output: \n", pretty_object)
    else:
        print("Response: \n", responseval)
    return responseval


def getChatResult(message):
    # print("Creating the Azure Open AI Client. \n")
    ## Create the Azure Open AI client
    client = AzureOpenAI(
        api_key= os.getenv("AZURE_OPENAI_API_KEY1"),  
        api_version= os.getenv("API_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT1")
    )

    deployment_name = os.getenv("VISION_DEPLOYMENT_NAME") 

    # Create an array of base64 image data for files named food1 to food10 in the images folder
    image_base64_array = []
    for i in range(1, 11):
        image_path = f"images/food{i}.jpg"
        try:
            image_base64 = get_image_filepath_base64(image_path)
            image_base64_array.append(image_base64)
        except Exception as e:
            print(f"Error processing {image_path}: {e}")

    sysmsg = """
    You're a chat assisatnat for a Food conceirage.
    Your job is to analyze the images of food and menus provied to you to analyze the below scenarios and answer questions based on that
    1. Identify the food items in the image and provide a list of them.
    2. Recommend the best food item based on the image and provide a reason for your recommendation.
    3. Provide a list of ingredients used in the food items.
    4. Provide a list of allergens present in the food items.
    5. Provide a list of nutritional facts for the food items.
    """
    
    print("Calling Azure Open AI endpoint to analyse the image. Waiting for response.. \n")
    ## Call the Azure Open AI endpoint to analyse the image using the local Data Url
    response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        { "role": "system", "content": sysmsg},
        { "role": "user", "content": [
            {
                "type": "text",
                "text": "Here are the food images for analysis",  # Pass the prompt
            },
            *[
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"{image_base64}"  # Pass the encoded image
                    },
                } for image_base64 in image_base64_array
            ],
        ],
        } 
    ],
    max_tokens=2000 
    )

    ## Print the response from the Azure Open AI endpoint
    print("Got response from the Azure Open AI endpoint \n")
    responseval = response.choices[0].message.content

    if responseval == "":
        print("No response from the model")
        exit();

    if "json" in responseval:
        s = responseval
        # Remove '```json\n' from the start and '\n```' from the end
        s = s[7:-4]
        responseval = s
        print("Outputting the response \n")
        responsejson = json.loads(responseval)
        pretty_object = json.dumps(responsejson, indent=4)
        print("Response output: \n", pretty_object)
    else:
        print("Response: \n", responseval)
    return responseval

