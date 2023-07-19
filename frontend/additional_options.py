# import openai
import streamlit as st

# from audiorecorder import audiorecorder
# from dotenv import load_dotenv


def clear_state():
    for key in st.session_state.keys():
        del st.session_state[key]


CLAIMS = {
    "Bob": ["HelloHelloHello", "GoodByeGoodByeGoodBye", "HowAreYouHowAreYou"],
    "Mary": ["JUST_ONE_FILLED_FORM"],
    "ROB": [],
}

username = st.selectbox(
    "Choose your user", ("Bob", "Mary", "Rob"), on_change=clear_state
)

col1, col2 = st.columns(2)

with col1:
    if st.button("List last 5 forms"):
        for idx, form in enumerate(CLAIMS[username]):
            st.write(f"{idx}. {form[:5]}...")

# with col2:
