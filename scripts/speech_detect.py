import base64 
import os 
from openai import AzureOpenAI 
from mimetypes import guess_type
from dotenv import load_dotenv
import json
load_dotenv()

# Function to encode a local image into data URL 
def getbase64(audiopath):
    
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(audiopath)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(audiopath, "rb") as audio_file:
        base64_encoded_data = base64.b64encode(audio_file.read()).decode('utf-8')

    # Construct the data URL
    return base64_encoded_data
 
## get the image base64
def get_audio_filepath_base64(path, base64=False):
    encodeddata = ""
    audiopath = path.strip()

    if (not audiopath.startswith("\\")): audiopath = "\\" + audiopath.replace("/", "\\")

    # Get the parent directory of the current script
    parent_dir = os.path.dirname(__file__)

    # Combine the parent directory and relative path to get the absolute path
    audiopath = os.path.join(os.path.dirname(parent_dir) + '\\web\\static' + audiopath)

    if not os.path.exists(audiopath):
        print("The audio file does not exist. Please enter a valid path.")
        return Exception("The audio file does not exist. Please enter a valid path.")       
   
    if base64:
        # Check if http or not and return data in base64
        if not("http" in audiopath or "https" in audiopath):
            print("Encoding the audio into a data URL \n")
            audiopath = audiopath ## Provide the path with respect to Parent folder
            return getbase64(audiopath)
    else:
        return audiopath

def audiotranscription():
    # Set environment variables or edit the corresponding values here.
    deployment_name = os.getenv("WHISPER_DEPLOYMENT_NAME") 

    #Authentication
    client = AzureOpenAI(
        api_key= os.getenv("AZURE_OPENAI_API_KEY1"),  
        api_version= os.getenv("API_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT1")
    )

    audio_test_file = get_audio_filepath_base64('audio\wikipediaOcelot.wav')
    
    # Send the request to the model
    print("Calling the Azure Open AI endpoint to transcribe the audio file. Waiting for response.. \n")
    result = client.audio.transcriptions.create (
        file=open(audio_test_file, "rb"),            
        model=deployment_name
    )

    if result:
        print("Transcription result:") 
        print(result.text)
        return result.text
    else:
        print("No transcription result received.")
        return None

def audio_multiturn_conversation(messages):
    # Set environment variables or edit the corresponding values here.
    deployment_name = os.getenv("AUDIO_DEPLOYMENT_NAME") 

    querymessages = messages

    #Authentication
    client = AzureOpenAI(
        api_key= os.getenv("AZURE_OPENAI_API_KEY1"),  
        api_version= os.getenv("API_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT1")
    )
    # Read and encode audio file  
    audio_encoded_string = get_audio_filepath_base64('audio\EarningsCall.wav', base64=True)

    # Initialize messages with the first turn's user input 
    messages = [
        { 
            "role": "user", 
            "content": [ 
                { "type": "text", "text": querymessages[0] }, 
                { "type": "input_audio", 
                    "input_audio": { 
                        "data": audio_encoded_string, 
                        "format": "wav" 
                    } 
                } 
            ] 
        }] 

    # # Convert the messages to a JSON string for debugging or logging purposes
    # messages_json = json.dumps(messages, indent=4)
    # print("Messages JSON:")
    # print(messages_json)

    # Get the first turn's response
    print("Calling the Azure Open AI endpoint to transcribe the audio file. Waiting for response.. \n")
    # Send the request to the model
    completion = client.chat.completions.create( 
        model=deployment_name, 
        modalities=["text", "audio"], 
        audio={"voice": "alloy", "format": "wav"}, 
        messages=messages
    ) 

    print("Get the first turn's response:")
    print(f"Question: {querymessages[0]}")
    print(completion.choices[0].message.audio.transcript) 

    result = f"Question: {querymessages[0]} \n {completion.choices[0].message.audio.transcript} \n-------------------------------------\n"   

    querymessages = querymessages[1:]

    while len(querymessages) >= 1:

        print("Add a history message referencing the first turn's audio by ID:")
        print(completion.choices[0].message.audio.id)

        # Add a history message referencing the first turn's audio by ID 
        messages.append({ 
            "role": "assistant", 
            "audio": { "id": completion.choices[0].message.audio.id } 
        }) 

        # Add the next turn's user message 
        messages.append({ 
            "role": "user", 
            "content": querymessages[0] 
        }) 

        # Send the follow-up request with the accumulated messages
        completion = client.chat.completions.create( 
            model=deployment_name, 
            messages=messages
        ) 

        print(f"Question: {querymessages[0]}")
        print(completion.choices[0].message.audio.transcript)
        result = result + f"Question: {querymessages[0]} \n {completion.choices[0].audio.transcript} \n-------------------------------------\n"

        # Remove the processed messages to avoid infinite loop
        querymessages = querymessages[1:]   

    return result

   