from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationEntityMemory

class LLM:
    def __init__(self, name, llm, memory, calendar):
        self.name = name
        self.llm = llm 
        self.memory = memory
        self.calendar = calendar

def get_user_choice(calendar):
    print("Please input your choice of LLM")
    choice = input()

    while not choice.isdigit():
        print("Please enter a number")
        choice = input()
    
    llm = ChatOpenAI(openai_api_key="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")
    return LLM("ChatGPT", llm, ConversationBufferMemory(), calendar)
    
def get_user_query():
    print("What change would you like to make to your calendar")
    return input()

