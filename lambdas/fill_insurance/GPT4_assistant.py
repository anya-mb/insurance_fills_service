# import os
# import json
# import openai
# import requests
# from dotenv import load_dotenv
# from tenacity import retry, wait_random_exponential, stop_after_attempt
# from constants import FUNCTIONS, SYSTEM_SETUP_PROMPT
#
# GPT_MODEL = "gpt-4-0613"
#
# load_dotenv(".env")
# openai.api_key = os.environ["OPENAI_API_KEY"]
#
#
# @retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
# def chat_completion_request(messages, functions=None, model=GPT_MODEL):
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer " + openai.api_key,
#     }
#     json_data = {"model": model, "messages": messages}
#     if functions is not None:
#         json_data.update({"functions": functions})
#     try:
#         response = requests.post(
#             "https://api.openai.com/v1/chat/completions",
#             headers=headers,
#             json=json_data,
#         )
#         return response
#     except Exception as e:
#         print("Unable to generate ChatCompletion response")
#         print(f"Exception: {e}")
#         return e
#
#
# class Chat:
#     def __init__(self):
#         self.conversation_history = []
#         self._add_prompt("system", SYSTEM_SETUP_PROMPT)
#
#     def _add_prompt(self, role: str, content: str):
#         message = {"role": role, "content": content}
#         self.conversation_history.append(message)
#
#     def add_assistant_prompt(self, content: str):
#         role = "assistant"
#         self._add_prompt(role, content)
#
#     def add_user_prompt(self, content: str):
#         role = "user"
#         self._add_prompt(role, content)
#
#     def display_conversation(self):
#         for message in self.conversation_history:
#             print(
#                 f"{message['role']}: {message['content']}\n\n",
#                 message["role"],
#             )
#
#     def upload_conversation_history(self, conversation_history: list):
#         self.conversation_history = conversation_history
#
#     def generate_response_for_user(self, functions: list = FUNCTIONS) -> (bool, str):
#
#         chat_response = chat_completion_request(
#             self.conversation_history, functions=functions
#         )
#
#         if chat_response is not None:
#             response_content = chat_response.json()["choices"][0]["message"]
#
#             message = chat_response.json()["choices"][0]["message"]["content"]
#
#             #         print("message:")
#             #         print(message)
#
#             if message is not None:
#                 chat_finished = False
#                 return chat_finished, message
#
#             if "function_call" in response_content:
#                 if (
#                     response_content["function_call"]["name"]
#                     == "save_users_questionnaire"
#                 ):
#
#                     questionnaire = json.loads(
#                         response_content["function_call"]["arguments"]
#                     )
#                     #                 print("Result questionnaire:")
#                     #                 print(questionnaire)
#
#                     chat_finished = True
#                     return chat_finished, questionnaire
#
#                 elif (
#                     response_content["function_call"]["name"]
#                     == "ask_follow_up_question"
#                 ):
#                     next_question = json.loads(
#                         response_content["function_call"]["arguments"]
#                     )["next_question"]
#                     #                 print("Next question:")
#                     #                 print(next_question)
#
#                     chat_finished = False
#                     return chat_finished, next_question
#
#         else:
#             print("ChatCompletion request failed. Retrying...")
