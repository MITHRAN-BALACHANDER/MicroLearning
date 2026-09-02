"""
Upload a staged directory to a Hugging Face Space as one commit.

Called by push-to-hf.sh. This exists instead of a plain `hf upload` call
because Git Bash on Windows runs MSYS2 glob expansion on arguments handed to
native executables, which turns the `--delete "*"` sync pattern into a list of
filenames before the CLI ever sees it. Going through the Python API sidesteps
the shell entirely.

Authentication comes from the token stored by `hf auth login`; no token is
read, printed, or passed on the command line here.

Usage:
    python deploy/hf_upload.py <repo_id> <staged_dir>
"""
import sys

from huggingface_hub import HfApi


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    repo_id, folder = sys.argv[1], sys.argv[2]

    commit = HfApi().upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=folder,
        commit_message="Deploy MicroLearning WhatsApp bot",
        commit_description=(
            "Docker Space serving the WhatsApp Cloud API webhook and /health "
            "on port 7860."
        ),
        # Makes the upload a sync: whatever is on the Space and not in this
        # payload is removed in the same commit, so the static template that
        # shipped with the Space does not linger alongside the app.
        delete_patterns=["*"],
    )

    print(f"Committed {getattr(commit, 'oid', '')}".rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
