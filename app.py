#!/usr/bin/env python3

import requests
import os
import sys
import getpass
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

# Initialize the Rich console
console = Console()

load_dotenv()
API_KEY = os.environ.get("API_KEY")

# Updated slug to use Gemini 3.1 Flash Lite
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"

def main():
    if not API_KEY:
        console.print("[bold red]Error:[/bold red] Could not find API_KEY. Please ensure your .env file is set up correctly.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY
    }

    conversation_history = []
    last_response_text = None
    username = getpass.getuser()

    console.clear()

    # Updated welcome message to show shortcuts
    welcome_message = "[dim]Gemini Chat Shell | Exit: [bold]q[/bold], [bold]/q[/bold], [bold]quit[/bold], [bold]exit[/bold] | Prefix [bold]!g[/bold] for Google Search[/dim]"
    console.print(welcome_message)

    while True:
        try:
            user_input = console.input(f"[bold red]{username}:[/bold red] ")

            # Check if stripped input matches any of the exit commands
            if user_input.strip().lower() in ['quit', 'exit', 'q', '/q']:
                console.print("[dim]Ending session...[/dim]")
                break

            if user_input.lower() == 'clear':
                console.clear()
                console.print(welcome_message)
                if last_response_text:
                    console.print(Rule(title="[bold blue]Gemini[/bold blue]", style="blue", align="left"))
                    console.print(Markdown(last_response_text))
                continue

            if not user_input.strip():
                continue

            # Check for the grounding flag
            use_grounding = False
            prompt_text = user_input

            if user_input.startswith("!g "):
                use_grounding = True
                prompt_text = user_input[3:].strip() # Strip the '!g ' before sending to the model

            conversation_history.append({
                "role": "user",
                "parts": [{"text": prompt_text}]
            })

            payload = {"contents": conversation_history}

            # If the user requested grounding, add the tool to this specific payload
            if use_grounding:
                payload["tools"] = [{"googleSearch": {}}]

            with console.status("[bold blue]Thinking...", spinner="dots"):
                response = requests.post(URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            candidate = data['candidates'][0]
            model_text = candidate['content']['parts'][0]['text']

            # Check for grounding metadata and format it if it exists
            grounding_metadata = candidate.get('groundingMetadata', {})
            grounding_chunks = grounding_metadata.get('groundingChunks', [])

            if grounding_chunks:
                model_text += "\n\n---\n**Grounding Sources:**\n"
                for index, chunk in enumerate(grounding_chunks, start=1):
                    web_info = chunk.get('web', {})
                    title = web_info.get('title', 'Unknown Source')
                    uri = web_info.get('uri', '')
                    if uri:
                        # Format as a Markdown link
                        model_text += f"{index}. [{title}]({uri})\n"

            last_response_text = model_text

            console.print(Rule(title="[bold blue]Gemini[/bold blue]", style="blue", align="left"))
            console.print(Markdown(model_text))

            # Append model response (including the formatted sources) to history
            conversation_history.append({
                "role": "model",
                "parts": [{"text": model_text}]
            })

        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]API Error:[/bold red] {e}")
            if 'response' in locals() and response.text:
                console.print(f"[dim]{response.text}[/dim]")
            conversation_history.pop()
        except KeyError:
            console.print("[bold red]Error:[/bold red] Unexpected response structure.")
            conversation_history.pop()
        except KeyboardInterrupt:
            console.print("\n[dim]Ending session...[/dim]")
            break

if __name__ == "__main__":
    main()
