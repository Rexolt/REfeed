from flask import Flask, jsonify, render_template, request
import feedparser
import xml.etree.ElementTree as ET
import os
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenWeather API kulcs
WEATHER_API_KEY = "3e7a3c0795233115750485a55e0a4a99"

# Fájlnevek
RSS_FEEDS_FILE = 'rss_feeds.xml'  # Az RSS feed-eket tároló XML fájl
FAVORITES_FILE = 'favorites.xml'  # A kedvenceket tároló XML fájl

# Globális változó a város tárolásához
current_city = "Budapest"

# RSS feedek tárolása egy XML fájlban
def save_feed_to_xml(feed_url):
    if not os.path.exists(RSS_FEEDS_FILE):
        create_xml_file(RSS_FEEDS_FILE)

    tree = ET.parse(RSS_FEEDS_FILE)
    root = tree.getroot()

    for feed in root.findall('feed'):
        if feed.text == feed_url:
            return  # Már létezik, nem mentjük újra

    new_feed = ET.Element('feed')
    new_feed.text = feed_url
    root.append(new_feed)
    tree.write(RSS_FEEDS_FILE)

# XML fájl létrehozása, ha nem létezik
def create_xml_file(filename):
    root = ET.Element('feeds')
    tree = ET.ElementTree(root)
    tree.write(filename)

# Kedvencek hozzáadása egy XML fájlban
def add_favorite_to_xml(title, link, published):
    if not os.path.exists(FAVORITES_FILE):
        create_xml_file(FAVORITES_FILE)

    tree = ET.parse(FAVORITES_FILE)
    root = tree.getroot()

    for article in root.findall('article'):
        if article.find('link').text == link:
            return  # Már létezik, nem mentjük újra

    new_article = ET.Element('article')
    ET.SubElement(new_article, 'title').text = title
    ET.SubElement(new_article, 'link').text = link
    ET.SubElement(new_article, 'published').text = published
    root.append(new_article)
    tree.write(FAVORITES_FILE)

# Kedvenc eltávolítása az XML fájlból
def remove_favorite_from_xml(link):
    if not os.path.exists(FAVORITES_FILE):
        return

    tree = ET.parse(FAVORITES_FILE)
    root = tree.getroot()

    for article in root.findall('article'):
        if article.find('link').text == link:
            root.remove(article)
            tree.write(FAVORITES_FILE)
            return

# Ellenőrizzük, hogy a cikk kedvencként van-e elmentve
def is_article_favorite(link):
    if not os.path.exists(FAVORITES_FILE):
        return False

    tree = ET.parse(FAVORITES_FILE)
    root = tree.getroot()

    for article in root.findall('article'):
        if article.find('link').text == link:
            return True
    return False

# OpenWeather API hívás
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = {
            'temperature': round(data['main']['temp']),  # Kerekített hőmérséklet
            'description': data['weather'][0]['description'],
            'city': data['name']
        }
        return weather
    else:
        return None

# Kezdőlap időjárással
@app.route('/')
def index():
    weather = get_weather(current_city)  # Az aktuális város időjárása
    return render_template('index.html', weather=weather)

# RSS feed betöltése
@app.route('/rss')
def get_rss_feed():
    feed_url = request.args.get('feed_url', "https://index.hu/24ora/rss/")
    save_feed_to_xml(feed_url)
    feed = feedparser.parse(feed_url)

    articles = []
    for entry in feed.entries:
        image_url = None

        if 'media_content' in entry:
            image_url = entry.media_content[0]['url']
        elif 'image' in entry:
            image_url = entry.image.href
        elif 'links' in entry:
            for link in entry.links:
                if 'image' in link.type:
                    image_url = link.href

        is_liked = is_article_favorite(entry.link)

        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'image': image_url,
            'is_liked': is_liked
        })

    return jsonify(articles)

# Város beállítása API
@app.route('/set_city', methods=['POST'])
def set_city():
    global current_city
    data = request.json
    city = data.get('city')

    if city:
        current_city = city  # Beállítjuk az új várost
        return jsonify({"status": "success", "message": f"Város beállítva: {city}"}), 200
    else:
        return jsonify({"status": "error", "message": "Nincs város megadva!"}), 400

# Város lekérése API
@app.route('/get_city', methods=['GET'])
def get_city():
    return jsonify({"city": current_city}), 200

# Kedvenc hozzáadása vagy eltávolítása
@app.route('/favorites/toggle', methods=['POST'])
def toggle_favorite():
    data = request.json
    title = data.get('title')
    link = data.get('link')
    published = data.get('published')

    if is_article_favorite(link):
        remove_favorite_from_xml(link)
        return jsonify({'status': 'removed'})
    else:
        add_favorite_to_xml(title, link, published)
        return jsonify({'status': 'added'})

# Kedvencek megjelenítése
@app.route('/favorites')
def favorites():
    if not os.path.exists(FAVORITES_FILE):
        return render_template('favorites.html', favorites=[])

    tree = ET.parse(FAVORITES_FILE)
    root = tree.getroot()

    favorites_list = []
    for article in root.findall('article'):
        favorites_list.append({
            'title': article.find('title').text,
            'link': article.find('link').text,
            'published': article.find('published').text
        })

    return render_template('favorites.html', favorites=favorites_list)

# Redirect oldal
@app.route('/redirect')
def redirect_page():
    return render_template('redirect.html')

if __name__ == '__main__':
    if not os.path.exists(RSS_FEEDS_FILE):
        create_xml_file(RSS_FEEDS_FILE)
    if not os.path.exists(FAVORITES_FILE):
        create_xml_file(FAVORITES_FILE)

    app.run(debug=True)
