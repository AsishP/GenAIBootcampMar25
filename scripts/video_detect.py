import json
import logging
import time
from collections.abc import Callable
from openai import AzureOpenAI
from pathlib import Path
from typing import Any, cast
from dataclasses import dataclass
import requests
import os
from mimetypes import guess_type
import base64
from dotenv import load_dotenv
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
def get_filepath_base64(path, base64=False):
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

def video_transcript(returnmarkdown=False):
    settings = Settings(
        endpoint=os.getenv("ANALYSER_ENDPOINT"),
        api_version=os.getenv("ANALYSER_API_VERSION"),
        # Either subscription_key or aad_token must be provided. Subscription Key is more prioritized.
        subscription_key=os.getenv("AZURE_OPENAI_API_KEY1"),
        aad_token="",
        analyzer_id=os.getenv("ANALYSER_ID"),
        file_location="video\FlightSimulator.mp4",
    )
    
    client = AzureContentUnderstandingClient(
        settings.endpoint,
        settings.api_version,
        subscription_key=settings.subscription_key
    )

    response = client.begin_analyze(settings.analyzer_id, settings.file_location)

    result = client.poll_result(
        response,
        timeout_seconds=60 * 60,
        polling_interval_seconds=1,
    )

    print("Video JSON result:\n")
    print(json.dumps(result, indent=4))

    # Parse the result JSON object
    contents = result.get("result", {}).get("contents", [])
    markdown_output = "# Video Analysis Results\n\n"

    # Append each content with timestamp and fields
    for content in contents:
        startTimeMs = content.get("startTimeMs", "N/A")
        endTimeMs = content.get("endTimeMs", "N/A")
        timestamp = f"{startTimeMs} - {endTimeMs}" if startTimeMs != "N/A" and endTimeMs != "N/A" else "N/A"
        fields = content.get("fields", {})
        fields_json = json.dumps(fields, indent=4)

        markdown_output += f"## Timestamp: {timestamp}\n\n"
        markdown_output += f"### Fields:\n\n```json\n{fields_json}\n```\n\n"
        markdown_output += "---\n\n"

    # If returnmarkdown is True, return the markdown output
    if returnmarkdown:
        return markdown_output
    else:
        return result

def analyse_video(message):
    result = video_transcript()
    # print("Creating the Azure Open AI Client. \n")
    ## Create the Azure Open AI client
    client = AzureOpenAI(
        api_key= os.getenv("AZURE_OPENAI_API_KEY1"),  
        api_version= os.getenv("API_VERSION"),
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT1")
    )

    deployment_name = os.getenv("DEPLOYMENT_NAME") 

    sysmsg = """
    You're a chat assisatnat for a Video Analysis.
    Your job is to analyze the video results based on the JSON provided to analyze the below scenarios and answer questions based on that
    1. The transcript of the video
    2. The contents array has markdown with transcript, description, start and end time
    3. The contents array has fields for each segment of the video
    4. The fields has following metadata attibutes
        a. Description - A concise summary of the video's content, highlighting key themes, subjects, and visuals. 
        b. Background - Details about the physical location shown in the video, such as city, region, landmark, and whether it is an indoor or outdoor setting.
        c. ShotType - Camera shot type
        d. VideoCategories - List of relevant categories
        e. Usecases - Capture the various cases of implementation listed in the Video
        f. Brands - List all Brands and Companies mentioned
        g. Sentiment - List the overall sentiment in the video from the Speakers tone
        h. Highlights - Capture all the main highlights of the video and the content mentioned
        i. VideoTransitions - List all the timestamps in seconds where transitions has happened in the video
        j. Locations - List all the landscape information shown in the video
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
                "text": message,  # Pass the prompt
            },
            {
            "type": "text",
            "text": json.dumps(result, indent=4),  # Pass the result JSON
            }
        ],
        } 
    ],
    max_tokens=4000 
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


@dataclass(frozen=True, kw_only=True)
class Settings:
    endpoint: str
    api_version: str
    subscription_key: str | None = None
    aad_token: str | None = None
    analyzer_id: str
    file_location: str

    def __post_init__(self):
        key_not_provided = (
            not self.subscription_key
            or self.subscription_key == "AZURE_CONTENT_UNDERSTANDING_SUBSCRIPTION_KEY"
        )
        token_not_provided = (
            not self.aad_token
            or self.aad_token == "AZURE_CONTENT_UNDERSTANDING_AAD_TOKEN"
        )
        if key_not_provided and token_not_provided:
            raise ValueError(
                "Either 'subscription_key' or 'aad_token' must be provided"
            )

    @property
    def token_provider(self) -> Callable[[], str] | None:
        aad_token = self.aad_token
        if aad_token is None:
            return None

        return lambda: aad_token


class AzureContentUnderstandingClient:
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        subscription_key: str | None = None,
        token_provider: Callable[[], str] | None = None,
        x_ms_useragent: str = "cu-sample-code",
    ) -> None:
        if not subscription_key and token_provider is None:
            raise ValueError(
                "Either subscription key or token provider must be provided"
            )
        if not api_version:
            raise ValueError("API version must be provided")
        if not endpoint:
            raise ValueError("Endpoint must be provided")

        self._endpoint: str = endpoint.rstrip("/")
        self._api_version: str = api_version
        self._logger: logging.Logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        self._headers: dict[str, str] = self._get_headers(
            subscription_key, token_provider and token_provider(), x_ms_useragent
        )

    def begin_analyze(self, analyzer_id: str, file_location: str):
        """
        Begins the analysis of a file or URL using the specified analyzer.

        Args:
            analyzer_id (str): The ID of the analyzer to use.
            file_location (str): The path to the file or the URL to analyze.

        Returns:
            Response: The response from the analysis request.

        Raises:
            ValueError: If the file location is not a valid path or URL.
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        file_path = get_filepath_base64(file_location)
        if Path(file_path).exists():
            with open(file_path, "rb") as file:
                data = file.read()
            headers = {"Content-Type": "application/octet-stream"}
        elif "https://" in file_location or "http://" in file_location:
            data = {"url": file_location}
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError("File location must be a valid path or URL.")

        headers.update(self._headers)
        if isinstance(data, dict):
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                json=data,
            )
        else:
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                data=data,
            )

        response.raise_for_status()
        self._logger.info(
            f"Analyzing file {file_location} with analyzer: {analyzer_id}"
        )
        return response

    def poll_result(
        self,
        response: requests.Response,
        timeout_seconds: int = 120,
        polling_interval_seconds: int = 2,
    ) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """
        Polls the result of an asynchronous operation until it completes or times out.

        Args:
            response (Response): The initial response object containing the operation location.
            timeout_seconds (int, optional): The maximum number of seconds to wait for the operation to complete. Defaults to 120.
            polling_interval_seconds (int, optional): The number of seconds to wait between polling attempts. Defaults to 2.

        Raises:
            ValueError: If the operation location is not found in the response headers.
            TimeoutError: If the operation does not complete within the specified timeout.
            RuntimeError: If the operation fails.

        Returns:
            dict: The JSON response of the completed operation if it succeeds.
        """
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers.")

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            self._logger.info(
                "Waiting for service response", extra={"elapsed": elapsed_time}
            )
            if elapsed_time > timeout_seconds:
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds:.2f} seconds."
                )

            response = requests.get(operation_location, headers=self._headers)
            response.raise_for_status()
            result = cast(dict[str, str], response.json())
            status = result.get("status", "").lower()
            if status == "succeeded":
                self._logger.info(
                    f"Request result is ready after {elapsed_time:.2f} seconds."
                )
                return response.json()  # pyright: ignore[reportAny]
            elif status == "failed":
                self._logger.error(f"Request failed. Reason: {response.json()}")
                raise RuntimeError("Request failed.")
            else:
                self._logger.info(
                    f"Request {operation_location.split('/')[-1].split('?')[0]} in progress ..."
                )
            time.sleep(polling_interval_seconds)

    def _get_analyze_url(self, endpoint: str, api_version: str, analyzer_id: str):
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={api_version}"

    def _get_headers(
        self, subscription_key: str | None, api_token: str | None, x_ms_useragent: str
    ) -> dict[str, str]:
        """Returns the headers for the HTTP requests.
        Args:
            subscription_key (str): The subscription key for the service.
            api_token (str): The API token for the service.
            enable_face_identification (bool): A flag to enable face identification.
        Returns:
            dict: A dictionary containing the headers for the HTTP requests.
        """
        headers = (
            {"Ocp-Apim-Subscription-Key": subscription_key}
            if subscription_key
            else {"Authorization": f"Bearer {api_token}"}
        )
        headers["x-ms-useragent"] = x_ms_useragent
        return headers
