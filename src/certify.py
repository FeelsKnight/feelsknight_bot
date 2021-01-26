import random
import requests
import json
import logging
from alphabet_detector import AlphabetDetector
from urllib.parse import quote as encode_url
from PIL import Image
from io import BytesIO
from keys import bot_token

alphabet_detector = AlphabetDetector()
certified_entities = [
    "me",
    "nessie",
    "несси",
    "sanya",
    "саня",
    "liza",
    "лиза",
    "ramazan",
    "рамазан"
]
certified_substrings = [
    "nsys",
    "diag",
    "inventory",
    "buyback"
]
searx_instances_url = "https://searx.space/data/instances.json"
searx_instances_blacklist = [
]
sticker_url = dict({
    True: "https://i.imgur.com/LGk4DPt.png",
    False: "https://i.imgur.com/c6VVBKz.png"
})
verdict = dict({
    True: "NSYS Certified",
    False: "Grade F"
})


def search(query):
    result = ""
    try:
        searx_instances = json.loads(requests.get(searx_instances_url).content)["instances"]
        searx_url = sorted((x for x in searx_instances.keys()
                            if searx_instances[x]["http"]["status_code"] == 200 and
                            "grade" in searx_instances[x]["http"] and
                            searx_instances[x]["http"]["grade"] == "A+" and
                            "normal" == searx_instances[x]["network_type"] and
                            "timing" in searx_instances[x] and
                            x not in searx_instances_blacklist),
                           key=lambda x: searx_instances[x]["timing"]["initial"]["all"]["value"])[0]

        language = "en" if alphabet_detector.is_latin(query) else "ru-RU"
        request_url = f"{searx_url}search?q={encode_url(query)}&categories=images&format=json&language={language}"
        logging.info(request_url)
        image_urls = json.loads(requests.get(request_url).content)
        image_urls = [str(x["img_src"] if "http" in x["img_src"] else ("https:" + x["img_src"]))
                      for x in image_urls["results"]
                      if "img_src" in x and
                      "//" in x["img_src"] and
                      ".svg" not in x["img_src"] and
                      ".gif" not in x["img_src"] and
                      "/" != x["img_src"][-1] and
                      (x["img_src"][-4] == "." or x["img_src"][-5] == ".")][:10]

        logging.info(image_urls)
        result = random.choice(image_urls)
        logging.info(result)
        """
        service = build(
            "customsearch",
            "v1",
            developerKey=google_cse,
            cache_discovery=False
        )
        query = encode_url(query)
        response = service.cse().list(
            q=query,
            cx=google_cx,
            searchType="image",
            num=1,
            safe="off"
        ).execute()

        print(response)
        if "items" in response:
            result = response["items"][0]["link"]
            if "?" in result:
                result = result[:result.index("?")]
        print(result)
        """
    except Exception as e:
        logging.error(f"Error: {e}")

    return result


def should_certify(entity=""):
    rnd = bool(random.randint(0, 1))
    if entity:
        return entity in certified_entities or any(s in entity for s in certified_substrings) or rnd
    else:
        return rnd


def with_sticker(image_url, certified):
    image = Image.open(requests.get(url=image_url, stream=True).raw).convert("RGB")
    # sticker_dimension = int(random.uniform(0.2, 0.8) * min(image.size[0], image.size[1]))
    sticker_dimension = int(min(image.size[0], image.size[1]) * 0.8)
    sticker = Image.open(requests.get(url=sticker_url[certified], stream=True).raw) \
        .convert("RGBA") \
        .resize((sticker_dimension, sticker_dimension))
    image.paste(
        sticker,
        (
            # int(image.size[0] * 0.15 + (random.uniform(0, 1) * (image.size[0] * 0.70 - sticker_dimension))),
            # int(image.size[1] * 0.15 + (random.uniform(0, 1) * (image.size[1] * 0.70 - sticker_dimension)))
            int((image.size[0] - sticker_dimension) // 2),
            int((image.size[1] - sticker_dimension) // 2)
        ),
        sticker
    )
    bio = BytesIO()
    bio.name = "image.jpeg"
    image.save(bio, "JPEG")
    bio.seek(0)
    return bio


def certify_handler(update, context):
    logging.info("---------------------------------------------------------------------------------------------------------------------------------------")
    logging.info(update)
    logging.info(update.message.text if update.message.text else update.message.caption)
    if update.message.text or update.message.caption:
        command, *message = (update.message.text if update.message.text else update.message.caption).lower().split(" ")
        if command != "/certify":
            return

        if update.message.photo or update.message.document or update.message.sticker:
            photo = update.message.document if update.message.document and "image" in update.message.document.mime_type\
                else max(update.message.photo, key=lambda e: e.width if e.width > e.height else e.height)

            request_image_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={photo.file_id}"
            response = json.loads(requests.get(request_image_url).content)
            if not response or response["ok"] is False:
                logging.error("Error: can't get image from Telegram server")
                return

            image_url = f"https://api.telegram.org/file/bot{bot_token}/{response['result']['file_path']}"
            certified = should_certify()
            image = with_sticker(image_url, certified)
            caption = verdict[certified]
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=image, caption=caption)
        else:
            entity = " ".join(message)
            random.seed(entity)
            certified = should_certify(entity)
            caption = (entity.title() + " is " if entity else "") + verdict[certified]
            image = sticker_url[certified]
            image_url = search(entity).encode("utf-8")
            if image_url:
                image = with_sticker(image_url, certified)
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=image, caption=caption)
