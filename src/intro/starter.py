import boto3
import json
import threading
import time
import itertools
import sys
import wikipedia
from wikipedia.exceptions import DisambiguationError, PageError
import os
import warnings
from bs4 import GuessedAtParserWarning

warnings.filterwarnings("ignore", category=GuessedAtParserWarning)

# -------------------- Config --------------------
REGION = "us-west-2"
TITAN_MODEL_ID = "amazon.titan-text-express-v1"

MAX_PROMPT_CHARS = 8000
WIKI_SENTENCES = 3
STOP_SEQUENCES = ["User:"]

HISTORY_FILE = "chat_history.txt"
NAME_FILE = "user_name.txt"

# -------------------- Utils --------------------
def loading_spinner(stop_event):
    for symbol in itertools.cycle(['|', '/', '-', '\\']):
        if stop_event.is_set():
            break
        sys.stdout.write(f'\rLoading {symbol}')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 30 + '\r')

def save_history(history: str):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        f.write(history)

def load_history() -> str:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def get_user_name() -> str:
    if os.path.exists(NAME_FILE):
        with open(NAME_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        name = input("What's your name? ").strip()
        with open(NAME_FILE, 'w', encoding='utf-8') as f:
            f.write(name)
        return name

def trim_history(history: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    if len(history) <= max_chars:
        return history
    tail = history[-max_chars:]
    newline_pos = tail.find('\n')
    if newline_pos != -1:
        return tail[newline_pos + 1 :]
    return tail

def safe_wikipedia_summary(query: str, sentences: int = WIKI_SENTENCES) -> (str, str):
    try:
        search_results = wikipedia.search(query, results=5)
        if not search_results:
            return None, None
        title = search_results[0]
        try:
            page = wikipedia.page(title, auto_suggest=False)
        except DisambiguationError as e:
            candidate = e.options[0] if e.options else title
            try:
                page = wikipedia.page(candidate, auto_suggest=False)
                title = candidate
            except Exception:
                return None, None
        except PageError:
            return None, None

        raw_summary = page.summary
        sentences_list = raw_summary.split('. ')
        limited = '. '.join(sentences_list[:sentences])
        if not limited.endswith('.'):
            limited = limited.strip() + '.'
        return title, limited
    except Exception:
        return None, None

# -------------------- Main chat --------------------
def main():
    user_name = get_user_name()
    system_prompt = (
        f"You are a helpful, concise assistant chatting with {user_name}. "
        "You have the full conversation history provided above. "
        "Always refer to the conversation history for context, personal details, and past discussions. "
        "When users ask about previous conversations or personal info, use the history directly. "
        "Use provided facts only if they are relevant to factual questions; do not let them override conversation context. "
        "When given a 'FACTS' block, incorporate it only if it directly answers the query; otherwise, ignore it and use history. "
        "Do not say 'As an AI language model' or similar. Be succinct and polite."
    )

    conversation_history = load_history()
    if not conversation_history:
        conversation_history = f"System: {system_prompt}\n"
    else:
        if not conversation_history.startswith("System:"):
            conversation_history = f"System: {system_prompt}\n" + conversation_history

    print(f"✅ AI Console Chat with memory + Wikipedia started. Welcome back, {user_name}! Type '/reset' to clear memory, '/history' to show history, or 'exit' to quit.\n")

    client = boto3.client(service_name='bedrock-runtime', region_name=REGION)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            save_history(conversation_history)
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            save_history(conversation_history)
            print("👋 Goodbye!")
            break
        if user_input.lower() == "/reset":
            conversation_history = f"System: {system_prompt}\n"
            save_history(conversation_history)
            print("🔄 Memory cleared.")
            continue
        if user_input.lower() == "/history":
            print("\n--- Conversation history ---")
            print(conversation_history)
            print("--- end history ---\n")
            continue

    
        prompt_base = conversation_history + f"User: {user_input}\n"

        # --- Wikipedia first ---
        title, summary = safe_wikipedia_summary(user_input, sentences=WIKI_SENTENCES)
        if title and summary:
            facts_block = f"FACTS (optional, from Wikipedia article '{title}'): {summary}\n"
            full_prompt = prompt_base + facts_block + "AI:"
        else:
            full_prompt = prompt_base + "AI:"

        full_prompt = trim_history(full_prompt, MAX_PROMPT_CHARS)

        titan_config = json.dumps({
            "inputText": full_prompt,
            "textGenerationConfig": {
                "maxTokenCount": 1024,
                "stopSequences": STOP_SEQUENCES,
                "temperature": 0.1,
                "topP": 1
            }
        })


        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(target=loading_spinner, args=(stop_spinner,))
        spinner_thread.start()

        try:
            response = client.invoke_model(
                body=titan_config,
                modelId=TITAN_MODEL_ID,
                accept="application/json",
                contentType="application/json"
            )
        except Exception as e:
            stop_spinner.set()
            spinner_thread.join()
            print(f"\n❌ Error calling model: {e}")
            continue

        stop_spinner.set()
        spinner_thread.join()

        try:
            response_body = json.loads(response.get('body').read())
            ai_response = response_body.get('results')[0].get('outputText', "").strip()
        except Exception as e:
            print(f"\n❌ Error parsing model response: {e}")
            continue

        conversation_history += f"User: {user_input}\nAI: {ai_response}\n"
        conversation_history = trim_history(conversation_history, MAX_PROMPT_CHARS)
        save_history(conversation_history)
        print(f"\nAI: {ai_response}")


if __name__ == "__main__":
    main()