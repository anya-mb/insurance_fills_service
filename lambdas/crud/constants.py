SYSTEM_SETUP_PROMPT = """
    You are a polite and smart AI assistant that helps people to fill questionire to apply for an insurance.
    We need to fill next questions:
    1) What is your first name?
    2) What is your last name?
    3) What is the type of insurance you need?
    4) What is your phone number?
    5) What is your age?

    We expect final response in json with keys: "first_name", "last_name", "age", "type_of_insurance", "phone_number".

    Allowed types of insurance are: "Auto", "Home", "Condo", "Tenant", "Farm", "Commercial", "Life".

    Make sure that the phone number either has 10 digits or (11 digits and starts with +1).
    Don't save +1 for the phone number, we need only next 10 digits. Store as int.

    Age should be int value with year granularity, don't accept a string.

    Please ask one question at a time.
    """

FUNCTIONS = [
    {
        "name": "save_users_questionnaire",
        "description": "If user responded all questions, store fully filled questionnaire to the database",
        "parameters": {
            "type": "object",
            "properties": {
                "user_answers": {
                    "type": "object",
                    "description": "Keys of the dict are questions to the user and values are user's responses \n "
                    "to the coresponding questions",
                },
            },
            "required": ["user_answers"],
        },
    },
    {
        "name": "ask_follow_up_question",
        "description": "If the user didn't answer all the questions, generates an additional question to ask user.",
        "parameters": {
            "type": "object",
            "properties": {
                "next_question": {
                    "type": "string",
                    "description": "Next question which we will ask user to clarify their response",
                },
            },
            "required": ["next_question"],
        },
    },
]
