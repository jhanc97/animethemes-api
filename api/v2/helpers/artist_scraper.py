from bs4 import BeautifulSoup
import json
import requests
import praw

from api.models import Artist, Theme

reddit = praw.Reddit(client_id="mS1uQkjEv2vxhg",
                     client_secret="Vs9q60YyROx780avM7AqsVFzfYM",
                     user_agent="Letrix's AnimeThemes API")


def get_cover(mal_id):
    print(mal_id)
    page = requests.get("https://myanimelist.net/people/{}".format(mal_id))
    body = BeautifulSoup(page.content, 'html.parser')
    cover = body.find('img', {'class': 'lazyload'}).get('data-src')
    return cover


def parse_themes(body):
    anime_list = body.findAll('h3')
    theme_list = []
    for anime in anime_list:
        mal_url = anime.find('a').get('href')
        if 'myanimelist' not in mal_url:
            continue
        mal_id = int("".join(filter(str.isdigit, mal_url)))
        print(mal_id)
        theme_entries = Theme.objects.filter(mal_id=mal_id).all()
        wiki_themes = anime.nextSibling.nextSibling.findAll('tr')[1:]
        if not wiki_themes:
            wiki_themes = anime.nextSibling.nextSibling.nextSibling.nextSibling.findAll('tr')[1:]
        for theme in wiki_themes:
            theme_type = theme.find('td').getText().split('"')[0][:-1]
            if not theme_type:
                continue
            for entry in theme_entries:
                if entry.type in theme_type:
                    # theme_list.append({'theme_title': entry.title, 'theme_id': entry.theme_id})
                    theme_list.append(entry.theme_id)
                    break
    return theme_list


def parse_artist(entry):
    name = entry.getText()
    print(name)
    wiki = entry.find('a').get('href').split('/')[4:]
    page = reddit.subreddit('AnimeThemes').wiki['/'.join(wiki)].content_html
    body = BeautifulSoup(page, 'html.parser')
    mal_url = body.find('h2').find('a').get('href')
    if 'myanimelist' not in mal_url:
        mal_id = None
    else:
        mal_id = body.find('h2').find('a').get('href').split('/')[-1]
        if not mal_id:
            mal_id = body.find('h2').find('a').get('href').split('/')[-2]
        mal_id = int("".join(filter(str.isdigit, mal_id)))
    Artist.create(mal_id, name, get_cover(mal_id), json.dumps(parse_themes(body)))
    return {'name': name, 'cover': get_cover(mal_id), 'themes': parse_themes(body)}


def get_list():
    page = reddit.subreddit('AnimeThemes').wiki['artist'].content_html
    body = BeautifulSoup(page, 'html.parser')
    artist_entries = body.findAll('p')[1:]
    artist_list = []
    for artist in artist_entries:
        artist_list.append(parse_artist(artist))
    return artist_list