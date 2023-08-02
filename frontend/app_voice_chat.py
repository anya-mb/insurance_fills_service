import logging
import streamlit as st
from streamlit_chat import message
import openai
from audiorecorder import audiorecorder
from time import gmtime, strftime

from utils import (
    show_audio_player,
    begin_conversation,
    generate_response,
    get_filled_form,
    reformat_filled_form,
    clear_state,
    LAST_MESSAGE,
    set_titles_and_headers,
)


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


AUDIOS_DIR = "user_audios/"


# Setting page title and headers
set_titles_and_headers()


# Initialise session state variables
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "audio_filenames" not in st.session_state:
    st.session_state["audio_filenames"] = []


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

            # transcribe
            audio_file = open(audio_filename, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            logger.info("transcript", transcript)

            user_input = transcript["text"]
            logger.info("user_input", user_input)

    if submit_button and user_input:
        is_finished, output = generate_response(
            user_input, st.session_state["conversation_id"]
        )
        st.session_state["past"].append(user_input)
        if is_finished:
            filled_form = get_filled_form(st.session_state["conversation_id"])
            filled_form = reformat_filled_form(filled_form)

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
