import datetime
import json
import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://paperswithcode.com/api/v1/"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def translate_gcp(text):
    try:
        res = requests.post(
            f"https://translation.googleapis.com/language/translate/v2?key={os.getenv('GCP_API_KEY')}",
            json={"q": text, "target": "ja"},
        )
        result = res.json()["data"]["translations"][0]["translatedText"]
    except Exception as e:
        print(f"GCP: {e}")
        result = ""
    return result


def translate_deepl(text):
    try:
        res = requests.post(
            f"https://api.deepl.com/v2/translate",
            data={
                "auth_key": os.getenv("DEEPL_TOKEN"),
                "text": text,
                "target_lang": "JA",
            },
        )
        res.raise_for_status()
        result = res.json()["translations"][0]["text"]
    except Exception as e:
        print(f"DeepL: {e}")
        result = ""
    return result


def post_slack(channel="#通知", username="通知", message=""):
    response = requests.post(
        os.getenv("SLACK_WEBHOOK"),
        headers={"Content-Type": "application/json"},
        json={
            "channel": channel,
            "text": message,
            "username": username,
            "icon_emoji": ":ghost:",
        },
    )
    return response.status_code


def call_pwc_api(url: str) -> dict:
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"RequestError: {e}")
        return {}
    return response.json()


def main():
    today = datetime.date.today()
    trend_url = BASE_URL + "search/"

    res = call_pwc_api(trend_url)

    if not res.get("results"):
        logging.error("No results")
        return

    # check cache
    cache = {}
    if os.path.exists(".cache/trend.json"):
        with open(".cache/trend.json", "r") as f:
            cache = json.load(f)

    for i, result in enumerate(res["results"]):
        if i >= 20:
            break
        if result["paper"]["id"] in cache:
            continue
        cache[result["paper"]["id"]] = result

        info = {
            "id": result["paper"]["id"],
            "title": result["paper"]["title"],
            "published": result["paper"]["published"],
            "abstract": result["paper"]["abstract"],
            "url": f"https://paperswithcode.com/paper/{result['paper']['id']}",
        }

        info["abstract_ja"] = ""
        info["abstract_ja"] = translate_deepl(info["abstract"])
        if not info["abstract_ja"]:
            info["abstract_ja"] = translate_gcp(info["abstract"])
            if info["abstract_ja"]:
                info["abstract_ja"] += "\nTranslated by GCP"
                logger.info(f"Translated: {info['title']} by GCP")
        else:
            info["abstract_ja"] += "\nTranslated by DeepL"
            logger.info(f"Translated: {info['title']} by DeepL")

        post_slack(
            channel="#paper",
            username=f"PapersWithCode Trend Papers({today})",
            message=(
                f"*PapersWithCode Trend Papers({today})*\n"
                f"【タイトル】: {info['title']}\n"
                f"【URL】: {info['url']}\n"
                f"【Date】{info['published']}\n"
                f"【Fetch Date】{today}\n"
                f"【Abst】: {info['abstract_ja']}\n"
                f"【Abst_en】: {info['abstract']}\n"
            ),
        )

    os.makedirs(".cache", exist_ok=True)
    with open(f".cache/trend.json", "w") as f:
        json.dump(cache, f, indent=2)


if __name__ == "__main__":
    main()
