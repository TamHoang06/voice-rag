import os
from datetime import datetime

def update_readme():
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    news_update = f"<!-- NEWS_START -->\n> 📢 **Latest Update:** The system was optimized at {now}. <!-- NEWS_END -->"

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "<!-- NEWS_START -->" in content:
        import re
        new_content = re.sub(r"<!-- NEWS_START -->.*?<!-- NEWS_END -->", news_update, content, flags=re.DOTALL)
    else:
        new_content = content + "\n\n" + news_update

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    update_readme()