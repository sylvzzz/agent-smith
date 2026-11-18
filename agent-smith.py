from src.agent import agent
from openai import BadRequestError

if __name__ == "__main__":
    try:
        history = []

        print("agent-smith: How can i help you today?")

        while True:
            prompt = input("\nYou: ")
            history = agent(prompt, history)

    except KeyboardInterrupt as error:
        print(f"\nThank you for using agent-smith!")
    except Exception as error:
        print(f"Something went wrong ... {error}")