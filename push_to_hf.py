import os
from huggingface_hub import HfApi, HfFolder

# Uses the native saved system token instead of a hardcoded one!
TOKEN = HfFolder.get_token()
REPO_ID = "omax404/aiko"
FOLDER = os.path.join(os.path.dirname(__file__), "cloud_bot")

def deploy():
    try:
        api = HfApi(token=TOKEN)
        print(f"Deploying to https://huggingface.co/spaces/{REPO_ID} ...")
        api.upload_folder(
            folder_path=FOLDER,
            repo_id=REPO_ID,
            repo_type="space",
            commit_message="Deploy standalone cloud CPU bot with local Qwen 4B",
        )
        print(f"Deployment Triggered! Check your Space at https://huggingface.co/spaces/{REPO_ID}")
    except Exception as e:
        print(f"Deployment failed: {e}")

if __name__ == "__main__":
    deploy()
