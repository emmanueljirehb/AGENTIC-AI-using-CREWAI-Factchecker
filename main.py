from dotenv import load_dotenv
from crew import get_url_crew
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
load_dotenv()

def run():
    user_claim = input("Enter a claim to fact-check: ").strip()

    if not user_claim:
        print("⚠ No claim entered.")
        return

    try:
        crew = get_url_crew(claim=user_claim)
        result = crew.kickoff(inputs={"claim": user_claim})
        print("\n✅ Fact-check complete!\n")
        print(result)
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    run()