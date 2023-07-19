import os

import streamlit as st
import string
import sys
import random
from dotenv import load_dotenv
import requests
import json

load_dotenv()

AWS_API_LINK = os.environ["AWS_API_LINK"]


def process_customer_input(user_input: str) -> dict:
    is_finished = random.random() <= 0.3
    # forms_link = AWS_API_LINK + 'form/{conversation_id}'
    # response = requests.get(forms_link, params={"conversation_id": 'vfdpvlsdlb'})

    # Define the URL
    url = AWS_API_LINK

    # Define the headers
    headers = {"Content-Type": "application/json"}

    # Define the data
    data = [
        {
            "role": "user",
            "content": "Hi, I am Bob Smith. I am looking for a car insurance. Do you offer it?",
        }
    ]

    # Convert the data to JSON format
    data_json = json.dumps(data)

    # Send the POST request
    response = requests.post(url, headers=headers, data=data_json)

    # Print the response
    print(response.text)

    if is_finished:
        return {
            "is_finished": True,
            "response": response,
        }  #  "Form is filled and saved, thanks"}
    else:
        return {"is_finished": False, "response": response}  #  user_input[::-1]}


def start_claim() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def clear_state():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state["HISTORY"] = []
    st.session_state["IS_FORM_FILLED"] = False


if st.button("Start New Claim"):
    clear_state()
    st.session_state["CLAIM_ID"] = start_claim()
    claim_id = None

claim_id = st.session_state.get("CLAIM_ID")
if not claim_id:
    sys.exit(0)

st.write(f"Current Claim ID: {claim_id}")

# Chat interface
history = st.session_state.get("HISTORY")
is_form_filled = st.session_state["IS_FORM_FILLED"]

if not is_form_filled:
    user_input = st.text_input("You: ", "", key="user_input")


if not is_form_filled and user_input:
    history.append(f"You: {user_input}")

    bot_response = process_customer_input(user_input)
    # body = bot_response__dict__
    history.append(f"Bot: {bot_response}")
    # history.append(f'Bot body: {body}')# bot_response["response"]
    st.session_state["IS_FORM_FILLED"] = bot_response["is_finished"]


for chat in history:
    st.text(chat)