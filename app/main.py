from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from longchain_core.output_parsers import PydanticOutputParser


class ResearchResponse(BaseModel):
    # Define the structure of the research response
    # Add fields as necessary as output from LLM call
    # Can have nested objects too as long as it inherits from BaseModel
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]



llm = ChatOpenAI(model_name="gpt-5")
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
    SystemMessagePromptTemplate.from_template(
        "You are a research assistant that helps researchers find relevant information."
    ),
    HumanMessagePromptTemplate.from_template(
        "Provide a detailed research response on the following topic:\n{topic}\n"
        "Format the response as per the following structure:\n{format_instructions}"
    )
    ]
)


response = llm.invoke("Where are you located?")
print(response)