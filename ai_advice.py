import os
from google import genai
from google.genai._interactions import APIConnectionError, APIStatusError, APITimeoutError
from google.genai.errors import ContinuationInterruptedError

def build_advice_prompt(plastic_bottles, public_transport, recycling):
    return f"""
You are helping a university student improve their environmental habits.

Their weekly habits:
- Plastic bottles used: {plastic_bottles}
- Public transport trips: {public_transport}
- Recycling occasions: {recycling}

Give two practical suggestions based on these habits.
Keep each suggestion within two sentences.
Do not assume public transport is always available.
Do not invent carbon reduction figures.

Do not assume campus facilities or local recycling services are available.
Use conditional wording when availability is unknown.
Do not guarantee cost savings or environmental outcomes.
"""

def generate_advice(prompt):
    if not os.getenv("GEMINI_API_KEY"):
        return "AI advice unavailable: API key is not configured."

    try:
        with genai.Client() as client:
            response = client.interactions.create(
                model="gemini-3.8-flash",
                input=prompt,
                timeout=15
            )

            return response.output_text or "No advice was returned."

    except ContinuationInterruptedError:
        return "AI advice unavailable: generation was interrupted. Please try again later."

    except APITimeoutError:
        return "AI advice unavailable: the request timed out. Please try again later."

    except APIConnectionError:
        return "AI advice unavailable: could not connect to the service. Please try again later."

    except APIStatusError as error:
        if error.status_code == 429:
            return "AI advice unavailable: rate or quota limit reached. Please try again later."
        return "AI advice unavailable: the API request failed. Please try again later."
