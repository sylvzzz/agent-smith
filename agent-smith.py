from src.agent import agent
from openai import BadRequestError

if __name__ == "__main__":
    try:
        history = []

        print("agent-smith: How can i help you today?")

        while True:
            prompt = input("\nYou: ")
            history = agent(prompt, history)

    except KeyboardInterrupt:
        print("\nThank you for using agent-smith!")