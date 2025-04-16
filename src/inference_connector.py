import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


def init_model(temperature=0.2, **kwargs) -> ChatOpenAI:
    is_env = load_dotenv()
    assert is_env, "Environment variable file not found, quitting"
    print("Inference connector init")
    return ChatOpenAI(
        api_key=os.environ["OPEN_API_KEY"],
        base_url=os.environ["OPEN_HOST_URL"],
        model=os.environ["OPEN_MODEL"],
        temperature=temperature,
        **kwargs
    )
