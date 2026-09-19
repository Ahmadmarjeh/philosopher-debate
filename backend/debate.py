import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .prompts import HOBBES_PROMPT, LOCKE_PROMPT, ROUSSEAU_PROMPT
    from .document import read_document
except ImportError:
    from prompts import HOBBES_PROMPT, LOCKE_PROMPT, ROUSSEAU_PROMPT
    from document import read_document


load_dotenv(Path(__file__).with_name(".env"))

SOURCE_PATH = Path(__file__).parent / "documents" / "State and Social Contract.docx"
SOURCE_MATERIAL = read_document(SOURCE_PATH)[:10000] if SOURCE_PATH.exists() else ""
client = None
model = None


def ask_philosopher(system_prompt, question, debate_history):
    global client, model

    if client is None:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=60.0,
                max_retries=1,
            )
            model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        else:
            client = OpenAI()
            model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    system_prompt = system_prompt + (
        "\n\nSOURCE MATERIAL (use as background evidence, not as a script):\n"
        + SOURCE_MATERIAL
        + "\n\nDEBATE REQUIREMENTS:\n"
        "- Make the social contract the central issue of this debate.\n"
        "- Explain what people give up, what they gain, and why political authority is legitimate.\n"
        "- Contrast your theory of the social contract with the other philosophers' theories.\n"
        "- Answer the user's question directly.\n"
        "- Take a clear philosophical position; do not only summarize the source.\n"
        "- If another philosopher has already spoken, challenge one specific claim they made.\n"
        "- Explain your reasoning in your own words and apply the ideas to the question.\n"
        "- Do not quote long passages or repeat the source material.\n"
        "- End with a concise statement of what you disagree with or defend."
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if debate_history:
        debate_history = debate_history[-12000:]
        messages.append({
            "role": "user",
            "content": "Here is the debate so far:\n\n" + debate_history
        })

    messages.append({
        "role": "user",
        "content": (
            "You are speaking now in the live debate. Speak in character and "
            "in the first person as the philosopher named in your role. Do not "
            "describe that philosopher from the outside. Argue with the other "
            "philosophers and answer this question:\n\n" + question
        )
    })

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_completion_tokens=700,
        reasoning_effort="low",
    )

    message = response.choices[0].message
    content = message.content
    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    content = (content or "").strip()
    if not content:
        raise RuntimeError("The AI provider returned an empty response. Please try again.")
    return content


def run_debate(question, rounds=3):

    debate_history = ""
    debate = []

    for round_number in range(rounds):

        # HOBBES
        hobbes_answer = ask_philosopher(
            HOBBES_PROMPT,
            question,
            debate_history
        )

        debate.append({
            "round": round_number + 1,
            "philosopher": "Hobbes",
            "message": hobbes_answer
        })

        debate_history += f"\n\nHOBBES:\n{hobbes_answer}"


        # LOCKE
        locke_answer = ask_philosopher(
            LOCKE_PROMPT,
            question,
            debate_history
        )

        debate.append({
            "round": round_number + 1,
            "philosopher": "Locke",
            "message": locke_answer
        })

        debate_history += f"\n\nLOCKE:\n{locke_answer}"


        # ROUSSEAU
        rousseau_answer = ask_philosopher(
            ROUSSEAU_PROMPT,
            question,
            debate_history
        )

        debate.append({
            "round": round_number + 1,
            "philosopher": "Rousseau",
            "message": rousseau_answer
        })

        debate_history += f"\n\nROUSSEAU:\n{rousseau_answer}"


    return debate