import hashlib
import json
import os

def generate_corpus_versions():
    versions = {}
    for f in os.listdir("data"):
        if f.endswith(".txt"):
            with open(f"data/{f}", "r", encoding="utf-8") as file:
                content = file.read()
                versions[f.replace(".txt", "")] = hashlib.md5(content.encode()).hexdigest()
    
    # Create a global version ID based on all the file hashes
    master_hash = hashlib.md5(str(versions).encode()).hexdigest()
    
    data = {
        "corpus_version": master_hash,
        "document_hashes": versions
    }
    
    with open("data/corpus_versions.json", "w") as f:
        json.dump(data, f)
    print(f"✅ Bumped corpus_version to {master_hash[:8]}...")

if __name__ == "__main__":
    generate_corpus_versions()