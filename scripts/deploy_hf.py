"""
deploy_hf.py — Upload the deploy-hf/ folder to Hugging Face Spaces
Run: python deploy_hf.py
"""
import os
from huggingface_hub import HfApi

REPO_ID = "omax404/aiko"
TOKEN   = "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"
FOLDER  = os.path.join(os.path.dirname(__file__), "deploy-hf")

def deploy():
    api = HfApi(token=TOKEN)
    print(f"Deploying to https://huggingface.co/spaces/{REPO_ID} ...")
    api.upload_folder(
        folder_path=FOLDER,
        repo_id=REPO_ID,
        repo_type="space",
        commit_message="Deploy Aiko — Vivian Live2D chat app",
    )
    print(f"Done! Visit: https://huggingface.co/spaces/{REPO_ID}")

if __name__ == "__main__":
    deploy()
