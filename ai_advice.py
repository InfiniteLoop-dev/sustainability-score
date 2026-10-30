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
"""