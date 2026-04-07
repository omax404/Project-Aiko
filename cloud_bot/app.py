import os
import threading
import telebot
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import gradio as gr

print("Downloading and Loading Qwen 4B GGUF Model into memory...")
print("This may take a minute on Space startup...")

# Qwen1.5 4B optimized for free CPU tier
repo_id = "Qwen/Qwen1.5-4B-Chat-GGUF"
filename = "qwen1_5-4b-chat-q4_k_m.gguf"

try:
    model_path = hf_hub_download(repo_id=repo_id, filename=filename)
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4, # Maximize vCPUs allocated to free space
        verbose=False
    )
    print("Neural Engine Loaded Successfully.")
except Exception as e:
    print(f"Failed to load engine: {e}")
    llm = None

# Telegram Bot Setup
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

def generate_aiko_response(user_input):
    if not llm:
        return "Neural Engine is currently offline."
    
    prompt = f"<|im_start|>system\nYou are Aiko, an intelligent AI companion. You are currently running on a cloud CPU engine.<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
    
    output = llm(
        prompt,
        max_tokens=256,
        stop=["<|im_end|>"],
        echo=False
    )
    return output["choices"][0]["text"].strip()

if bot:
    @bot.message_handler(func=lambda msg: True)
    def handle_message(message):
        print(f"[TG] {message.from_user.first_name}: {message.text}")
        try:
            reply = generate_aiko_response(message.text)
            bot.reply_to(message, reply)
        except Exception as e:
             bot.reply_to(message, f"Core error: {e}")

    def run_bot():
        print("Telegram WebHook Polling Started.")
        bot.infinity_polling()

    threading.Thread(target=run_bot, daemon=True).start()
else:
    print("No TELEGRAM_BOT_TOKEN found in Secrets. Bot is disabled.")

# Gradio Interface (Mandatory for Hugging Face Spaces to stay 'Running')
def chat_ui(message, history):
    return generate_aiko_response(message)

demo = gr.ChatInterface(
    fn=chat_ui,
    title="Aiko Neural Core Dashboard",
    description="Engine: Qwen 4B CPU. The Telegram bot is running in the background. Note: HF free spaces pause after 48h of web UI inactivity."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
