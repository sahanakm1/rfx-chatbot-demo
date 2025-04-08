import os

def read_file_with_fallback(path):
    for encoding in ["utf-8", "windows-1252", "iso-8859-1"]:
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("Unable to decode the file with known encodings.")

def summarize_documents():
    folder = "docs"
    summaries = []

    if not os.path.exists(folder):
        return "📁 No 'docs/' folder found."

    files = [f for f in os.listdir(folder) if f.endswith(".txt")]
    if not files:
        return "⚠️ No .txt documents found in the docs/ folder."

    for file in files:
        path = os.path.join(folder, file)
        try:
            content = read_file_with_fallback(path)
            snippet = content[:500]  # Basic truncation
            summaries.append(f"🔹 **{file}**:\n{snippet}...\n")
        except Exception as e:
            summaries.append(f"❌ Error reading {file}: {e}")

    return "\n".join(summaries)