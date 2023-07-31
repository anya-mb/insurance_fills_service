import json
import logging
import requests
import streamlit as st
from streamlit_chat import message
import os
from dotenv import load_dotenv

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv("frontend/.env")
ENDPOINT = os.environ["AWS_API_LINK"]

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
    if "session_id" in st.session_state:
        del st.session_state["session_id"]


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
    print(f"conversation_id: {conversation_id}")

    url = f"{ENDPOINT}form/{conversation_id}"

    response = requests.get(url, headers=HEADERS)
    print("response", response)
    print("response.json()", response.json())
    logger.info("filled_form_response")
    logger.info(response)
    return response.json()


# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key="my_form", clear_on_submit=True):
        user_input = st.text_area("You:", key="input", height=100)
        submit_button = st.form_submit_button(label="Send")

    if submit_button and user_input:
        is_finished, output = generate_response(user_input)
        st.session_state["past"].append(user_input)
        if is_finished:
            filled_form = get_filled_form()
            LAST_MESSAGE = (
                "Thank you for your time! Your form is filled successfully!\n"
                + filled_form
            )
            st.session_state["generated"].append(LAST_MESSAGE)

            # st.session_state["generated"].append(filled_form)
        else:
            st.session_state["generated"].append(output)


if st.session_state["generated"]:
    with response_container:
        for i in range(len(st.session_state["generated"])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
            message(st.session_state["generated"][i], key=str(i))

if st.button("Submit new form"):
    clear_state()
    st.experimental_rerun()
