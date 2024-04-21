import os
import glob
import json
import httpx
import logging
import chardet

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

TOP_LEVEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_event_details(event_url):
    try:
        api_url = event_url.replace("ctftime.org/event/", "ctftime.org/api/v1/events/")
        r = httpx.get(api_url + "/")
        r.raise_for_status()  # Raise an exception for non-2xx status codes
        event_details = r.json()
        return event_details["description"], event_details["title"]
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logging.error(f"Error fetching event details: {e}")
        return None, None


def read_descriptions(file_path):
    try:
        with open(file_path, "rb") as f:
            result = chardet.detect(f.read())
            encoding = result["encoding"]
        with open(file_path, "r", encoding=encoding) as f:
            descriptions = json.load(f)
        return descriptions
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logging.error(f"Error reading descriptions file: {e}")
        return None


def generate_readme(
    event_name,
    event_url,
    event_description,
    directory_list,
    subdirectory_list,
    descriptions,
    output_path,
):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {event_name}\n\n")
            f.write(f"{event_url}\n\n")
            f.write("## Event Description\n\n")
            f.write(f"{event_description}\n\n")
            for directory in directory_list:
                directory_name = os.path.basename(directory)
                f.write(f"## [{directory_name}](<{directory_name}/>)\n")
                for subdirectory in subdirectory_list:
                    if os.path.dirname(subdirectory) == directory:
                        subdirectory_name = os.path.basename(subdirectory)
                        f.write(
                            f" * #### [{subdirectory_name}](<{directory_name}/{subdirectory_name}/>)\n"
                        )
    except IOError as e:
        logging.error(f"Error writing to {output_path}: {e}")


def main():
    DIRECTORY_LIST = [
        os.path.normpath(y)
        for y in glob.glob(os.path.join(TOP_LEVEL_DIR, "*"))
        if os.path.isdir(y)
    ]
    DIRECTORY_LIST.sort()

    SUB_DIRECTORY_LIST = [
        os.path.normpath(y)
        for x in DIRECTORY_LIST
        for y in glob.glob(os.path.join(x, "*"))
        if os.path.isdir(y)
    ]
    SUB_DIRECTORY_LIST.sort()

    event_file_path = os.path.join(AUTOMATION_DIR, "Change-Me", "event.txt")
    descriptions_file_path = os.path.join(
        AUTOMATION_DIR, "Read-Only", "descriptions.json"
    )

    try:
        with open(event_file_path, "r") as f:
            event_url = f.read().strip()
    except FileNotFoundError:
        logging.error(f"Event file '{event_file_path}' not found.")
        return

    event_description, event_name = fetch_event_details(event_url)
    if event_description is None or event_name is None:
        return

    descriptions = read_descriptions(descriptions_file_path)
    if descriptions is None:
        return

    top_level_readme_path = os.path.join(TOP_LEVEL_DIR, "README.md")
    generate_readme(
        event_name,
        event_url,
        event_description,
        DIRECTORY_LIST,
        SUB_DIRECTORY_LIST,
        descriptions,
        top_level_readme_path,
    )

    for directory in DIRECTORY_LIST:
        directory_readme_path = os.path.join(directory, "README.md")
        with open(directory_readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {os.path.basename(directory)}\n\n")
            f.write("### Category Description\n\n")
            for category in descriptions["categories"]:
                if os.path.basename(directory) in category["name"]:
                    f.write(f"{category['details']['description']}\n\n")
            f.write("## Challenges\n\n")
            for subdirectory in SUB_DIRECTORY_LIST:
                if os.path.dirname(subdirectory) == directory:
                    f.write(
                        f"- ### [{os.path.basename(subdirectory)}](<{os.path.basename(subdirectory)}/>)\n"
                    )

    logging.info("README files generated successfully.")


if __name__ == "__main__":
    main()
