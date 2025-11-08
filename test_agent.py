import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import create_agent

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
gemini_api_key = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini model
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0
)

# Initialize DuckDuckGo search tool
search_tool = DuckDuckGoSearchRun()

# Create research agent
agent = create_agent(
    model=model,
    tools=[search_tool],
    system_prompt="You are an expert researcher. Conduct thorough research and provide detailed, accurate answers."
)

# Run the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "What are the latest developments in AI?"}]
})

print(result["messages"][-1].content)