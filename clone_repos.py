import subprocess
import os

# Zielverzeichnis
target_dir = r"C:\Temp"

# Repos
repos = [
    "https://github.com/FHWN-Robotik/WS-KI.git",
    "https://github.com/FHWN-Robotik/WS-IndRob.git",
    "https://github.com/FHWN-Robotik/WS-MobRob.git"
]

def clone_repos():
    # Stelle sicher, dass Zielverzeichnis existiert
    os.makedirs(target_dir, exist_ok=True)

    for repo in repos:
        repo_name = repo.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(target_dir, repo_name)

        if os.path.exists(repo_path):
            print(f"{repo_name} existiert bereits, überspringe...")
        else:
            print(f"Cloning {repo} nach {repo_path}")
            subprocess.run(["git", "clone", repo, repo_path], check=True)

if __name__ == "__main__":
    clone_repos()
    print("Alle Repos wurden geklont oder existierten bereits.")
