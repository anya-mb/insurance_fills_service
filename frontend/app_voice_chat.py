import json
import logging
import requests
import streamlit as st
from streamlit_chat import message
import os
import openai

from audiorecorder import audiorecorder
from dotenv import load_dotenv

from io import BytesIO
from gtts import gTTS, gTTSError
from time import gmtime, strftime


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv("frontend/.env")
ENDPOINT = os.environ["AWS_API_LINK"]

openai.api_key = os.environ["OPENAI_API_KEY"]

AUDIOS_DIR = "user_audios/"

HEADERS = {"Content-Type": "application/json"}


# Setting page title and headers
st.set_page_config(page_title="Insurance bot", page_icon="🕵️‍♀️")
st.markdown(
    "<h1 style='text-align: center;'>Fill your insurance bot</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "Welcome to the AI Insurance Assistant! "
    "I can assist you in filling out a questionnaire to apply for insurance.",
    unsafe_allow_html=True,
)

st.markdown(
    "I will guide you through the process step by step. \n",
    unsafe_allow_html=True,
)
st.markdown(
    "Please describe your situation.",
    unsafe_allow_html=True,
)

# Initialise session state variables
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "audio_filenames" not in st.session_state:
    st.session_state["audio_filenames"] = []


# reset everything
def clear_state():
    """
    Clears streamlit state
    """
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    st.session_state["session_id"] = ""
    st.session_state["conversation_id"] = begin_conversation(" ")
    st.session_state["audio_filenames"] = []


def get_user_prompt_data_json(user_reply: str) -> dict:
    """
    Converts user replay into GPT4 API format
    :param user_reply:
    :return:
    """
    data = [{"role": "user", "content": user_reply}]
    data_json = json.dumps(data)
    return data_json


def send_response(conversation_id: str, user_reply: str) -> dict:
    """
    Response looks like this:
        {
        'next_question': 'Question',
        'is_finished': bool
        }

    :param conversation_id:
    :param user_reply:
    :return:
    """
    url = f"{ENDPOINT}form/{conversation_id}"

    data_json = get_user_prompt_data_json(user_reply)

    response = requests.post(url, headers=HEADERS, data=data_json)
    logger.info("response")
    logger.info(response)
    return response.json()


def begin_conversation(user_reply: str) -> str:
    """Returns conversation_id for a new chat"""
    url = f"{ENDPOINT}form"

    data_json = get_user_prompt_data_json(user_reply)

    response = requests.post(url, headers=HEADERS, data=data_json)
    conversation_id = response.json()["conversation_id"]
    print(f"conversation_id: {conversation_id}")

    return conversation_id


def generate_response(prompt: str) -> (str, bool):
    """Generates new question given an user prompt"""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    conversation_id = st.session_state.get("conversation_id", None)
    if not conversation_id:
        conversation_id = begin_conversation(prompt)
        st.session_state["conversation_id"] = conversation_id

    raw_response = send_response(conversation_id, prompt)
    logger.info("raw_response")
    logger.info(raw_response)
    question = raw_response["next_question"]
    is_finished = raw_response["is_finished"]

    st.session_state["messages"].append({"role": "assistant", "content": question})

    return is_finished, question


def get_filled_form() -> str:
    """Retrieves the filled form crom the DynamoDB"""
    print("in get_filled_form")
    conversation_id = st.session_state.get("conversation_id", None)

    if conversation_id is None:
        raise ValueError("conversation_id is None")

    print(f"conversation_id: {conversation_id}")

    url = f"{ENDPOINT}form/{conversation_id}"

    response = requests.get(url, headers=HEADERS)
    print("response", response)
    print("response.json()", response.json())
    logger.info("filled_form_response")
    logger.info(response)
    return response.json()


def reformat_filled_form(form: str) -> str:
    form = json.loads(form)
    result = "\n".join([key + " = " + value for key, value in form.items()])
    return result


def show_audio_player(ai_content: str) -> None:
    """Shows audio player in chatbox
    if activated, it says ai_content"""
    sound_file = BytesIO()
    try:
        tts = gTTS(text=ai_content, lang="en", tld="ca")
        tts.write_to_fp(sound_file)
        st.audio(sound_file)
    except gTTSError as err:
        st.error(err)


# container for chat history
response_container = st.container()
# container for text box
container = st.container()

if "conversation_id" not in st.session_state:
    conversation_id = begin_conversation(" ")
    st.session_state["conversation_id"] = conversation_id


with container:
    with st.form(key="my_form", clear_on_submit=True):
        user_input = st.text_area("You:", key="input", height=100)
        submit_button = st.form_submit_button(label="Send")

        audio = audiorecorder("Click to record", "Recording...")

        if len(audio) > 0:
            # To play audio in frontend:
            st.audio(audio.tobytes())

            audio_filename = (
                AUDIOS_DIR
                + st.session_state["conversation_id"]
                + strftime("%Y-%m-%d_%H:%M:%S", gmtime())
                + ".mp3"
            )

            # To save audio to a file:
            wav_file = open(audio_filename, "wb")
            wav_file.write(audio.tobytes())

            audio_file = open(audio_filename, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            logger.info("transcript", transcript)

            user_input = transcript["text"]
            logger.info("user_input", user_input)

    if submit_button and user_input:
        is_finished, output = generate_response(user_input)
        st.session_state["past"].append(user_input)
        if is_finished:
            filled_form = get_filled_form()
            filled_form = reformat_filled_form(filled_form)
            LAST_MESSAGE = (
                "Thank you for your time! Your form is filled successfully!\n\n"
            )
            show_audio_player(LAST_MESSAGE)
            message_and_form = LAST_MESSAGE + filled_form
            st.session_state["generated"].append(message_and_form)

        else:
            st.session_state["generated"].append(output)
            show_audio_player(output)

if st.session_state["generated"]:
    with response_container:
        for i in range(len(st.session_state["generated"])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
            message(st.session_state["generated"][i], key=str(i))

if st.button("Submit new form"):
    clear_state()
    st.experimental_rerun()
