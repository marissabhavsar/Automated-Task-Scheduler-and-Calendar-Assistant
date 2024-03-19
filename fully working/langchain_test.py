from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class LLM:
    def __init__(self, name, llm):
        self.name = name
        self.llm = llm 

def get_user_choice():
    print("Please input your choice of LLM")
    choice = input()

    while not choice.isdigit():
        print("Please enter a number")
        choice = input()

    if choice == 0:
        return LLM("ChatGPT", ChatOpenAI(openai_api_key="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"))

    else:
        return LLM("ChatGPT", ChatOpenAI(openai_api_key="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"))
    
def get_user_query():
    print("What change would you like to make to your calendar")
    return input()

