import json
import logging
import requests
import streamlit as st
import os
import openai
from dotenv import load_dotenv
from io import BytesIO
from gtts import gTTS, gTTSError


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


HEADERS = {"Content-Type": "application/json"}
LAST_MESSAGE = "Thank you for your time! Your form is filled successfully!\n\n"


def setup_endpoint_and_api_key() -> str:
    load_dotenv("frontend/.env")
    endpoint = os.environ["AWS_API_LINK"]

    openai.api_key = os.environ["OPENAI_API_KEY"]
    return endpoint


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
    endpoint = setup_endpoint_and_api_key()
    url = f"{endpoint}form/{conversation_id}"

    data_json = get_user_prompt_data_json(user_reply)

    response = requests.post(url, headers=HEADERS, data=data_json)
    logger.info("response")
    logger.info(response)
    return response.json()


def begin_conversation(user_reply: str) -> str:
    """Returns conversation_id for a new chat"""
    endpoint = setup_endpoint_and_api_key()
    url = f"{endpoint}form"

    data_json = get_user_prompt_data_json(user_reply)

    response = requests.post(url, headers=HEADERS, data=data_json)
    conversation_id = response.json()["conversation_id"]
    logger.info(f"conversation_id: {conversation_id}")

    return conversation_id


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


def generate_response(prompt: str, conversation_id: str) -> (str, bool):
    """Generates new question given an user prompt"""
    st.session_state["messages"].append({"role": "user", "content": prompt})

    raw_response = send_response(conversation_id, prompt)
    logger.info("raw_response")
    logger.info(raw_response)
    question = raw_response["next_question"]
    is_finished = raw_response["is_finished"]

    st.session_state["messages"].append({"role": "assistant", "content": question})

    return is_finished, question


def get_filled_form(conversation_id: str) -> str:
    """Retrieves the filled form crom the DynamoDB"""
    endpoint = setup_endpoint_and_api_key()
    url = f"{endpoint}form/{conversation_id}"

    response = requests.get(url, headers=HEADERS)
    logger.info("response.json()", response.json())
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


# Setting page title and headers
def set_titles_and_headers():
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
