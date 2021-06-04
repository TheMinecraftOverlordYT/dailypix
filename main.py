import time

from gphotospy.album import *
from gphotospy import authorize
from gphotospy.media import *
import datetime
import random as rand
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from sheet_manager import SheetManager
from image_compression import ImageCompression


def remove(name):
    if os.path.exists(name):
        os.remove(name)


# Military time
SEND_HOUR = 3 + 12

# Initialize fields, read in passwords
file = open("creds/pass.txt", "r", 1)
mine = file.readline()
recipient = file.readline()
sms_gateway = file.readline()
pass_ = file.readline()
file.close()
# Auth into Google Photos
CLIENT_SECRET_FILE = "creds/gphoto_oauth.json"
service = authorize.init(CLIENT_SECRET_FILE)

while True:
    mgr = SheetManager()

    # Get Rocku album
    album_manager = Album(service)
    album_iterator = album_manager.list()
    album_as_list = list(album_iterator)
    first_album = album_as_list[1]
    second_album = album_as_list[0]  # Get Jahnu's album as well and combine them

    media_manager = Media(service)
    album_media_list = list(media_manager.search_album(first_album.get("id")))
    second_media_list = list(media_manager.search_album(second_album.get("id")))
    album_media_list.extend(second_media_list)  # Add the albums together

    # Since we can only get the bytes of the item, videos don't work, so we filter them out
    album_media_list = list(filter(lambda x: x.get("mimeType") == "image/jpeg", album_media_list))

    # Get specific pic
    pic = album_media_list[rand.randint(0, len(album_media_list))]

    # Save to disk
    media = MediaItem(pic)
    with open(media.filename(), "wb") as output:
        output.write(media.raw_download())
        filename = media.filename()

    # If our file is greater than 20MB (25 is limit), compress it
    if os.path.getsize(filename) / 1000000 > 20:
        ic = ImageCompression(filename)
        ic.compress()

    meta = pic.get("mediaMetadata")
    # Format date and time for text body
    date = datetime.datetime.strptime(meta.get("creationTime")[0:10], "%Y-%m-%d")
    year = date.strftime("%Y")
    month = date.strftime("%B")
    day = date.strftime("%d")

    hour = int(datetime.datetime.today().strftime("%H"))
    if hour < SEND_HOUR:
        print(f"It's too early! Sleeping for {SEND_HOUR - hour} hours")
        time.sleep((SEND_HOUR - hour) * 60 * 60)

    # Shorten URL
    base_url = pic.get("baseUrl")
    image_url = "{}=w300-h300".format(base_url)
    if mgr.check_cell():
        # Start SMTP server
        server = smtplib.SMTP_SSL("smtp.gmail.com", port=465)
        server.login(mine, pass_)

        # Send via email
        msg = MIMEMultipart()
        msg["From"] = mine
        msg["To"] = sms_gateway
        msg["Subject"] = f"Daily Dog Pic from {month} {day}, {year}\n"

        img_data = open(filename, "rb").read()

        mime_image = MIMEImage(img_data, name=os.path.basename(filename))
        msg.attach(mime_image)
        sms = msg.as_string()
        server.sendmail(mine, sms_gateway, sms)
        server.quit()

        remove(filename)
        mgr.set_cell(date, image_url)
        print(f"Daily pic {datetime.date.today()} has been successfully delivered")
    else:
        print("Daily pic has already been delivered")
        remove(filename)
        time.sleep(6 * 60 * 60)
