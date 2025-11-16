from typing import List
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from collections import namedtuple

HTMLDataTuple = namedtuple("HTMLDataTuple", ["type", "content"])

def get_header_tuple(header) -> HTMLDataTuple:
    return HTMLDataTuple(type="header-primary", content=header.get_text(strip=True))

def get_content_tuples(content) -> List[HTMLDataTuple]:
    content_tuple_list = []
    outer = content.find(class_="white-stone accent-before")
    if outer:
        inner = outer.find('div')
        for child in inner.find_all(recursive=False):
            if child.name:
                if child.name == "span" and child.get("class") and "content-border" in " ".join(child.get("class")):
                    try:
                        for child in child.find_all(recursive=False):
                            if child.name == "img":
                                content_tuple_list.append(HTMLDataTuple(type="img", content=child['src']))
                            elif child.name == "a":
                                content_tuple_list.append(HTMLDataTuple(type="href", content=child['href']))
                    except KeyError:
                        print('no src')
                elif child.name in ["ul", "ol"]:  
                    for li in child.find_all("li"):
                        content_tuple_list.append(HTMLDataTuple(type="li", content=f'• {li.get_text(strip=True)}\n'))
                elif child.get("class") and "blockquote context" in " ".join(child.get("class")):
                    content_tuple_list.append(HTMLDataTuple(type="blockquote", content=f'"{child.get_text(separator=" ", strip=True)}"\n'))
                elif child.get("class") and "change-detail-title" in " ".join(child.get("class")):
                    content_tuple_list.append(HTMLDataTuple(type="change-detail-title", content=child.get_text(strip=True)))
                elif child.get("class") and "divider" in " ".join(child.get("class")):
                    content_tuple_list.append(HTMLDataTuple(type="divider", content="\n"))
                else:
                    content_tuple_list.append(HTMLDataTuple(type="p", content=f'{child.get_text(strip=True)}\n'))
    return content_tuple_list
    
async def get_patch_note_data(link) -> List[HTMLDataTuple]:
    tft_page_text = None
    tft_data_list = []
    async with ClientSession() as session:
        async with session.get(link) as response:
            if response.status != 200:
                print('Failed to retrieve patch notes')
                return []
            tft_page_text = await response.text()
    patch_html = BeautifulSoup(tft_page_text, 'html.parser')
    error = patch_html.find(class_="page-not-found_errorCode__ZNHNq")
    if error is not None:
        return []
    patch_notes_container = patch_html.find(id="patch-notes-container")
    for child in patch_notes_container.find_all(recursive=False):
        if child.get("class") and "header-primary" in " ".join(child.get("class")):
            tft_data_list.append(get_header_tuple(child))
        elif child.get("class") and "content-border" in " ".join(child.get("class")):
            tft_data_list.extend(get_content_tuples(child))
    return tft_data_list


async def get_recent_tft_data() -> List[HTMLDataTuple]:
    tft_patch_notes_text = None
    bot_message = []
    patch_notes_url = "https://www.leagueoflegends.com/en-us/news/tags/teamfight-tactics-patch-notes/"

    async with ClientSession() as session:
        async with session.get(patch_notes_url) as response:
            if response.status != 200:
                print('Failed to retrieve patch notes')
                return []
            tft_patch_notes_text = await response.text()


    soup = BeautifulSoup(tft_patch_notes_text, 'html.parser')
    section = soup.find("section", {"data-testid": "article-card-grid"})

    articles = section.find_all("a", href=True)
    
    for article in articles:
        title_tag = article.find("div", {"data-testid": "card-title"})
        if title_tag:  
            title = title_tag.get_text(strip=True)
            if 'Teamfight Tactics patch' in title:
                link = article['href']

                bot_message.append(HTMLDataTuple(type="patch-title", content=title))
                bot_message.extend(await get_patch_note_data(link))
                return bot_message

    return []


async def get_recent_patch_title() -> str:
    tft_patch_notes_text = None
    
    patch_notes_url = "https://www.leagueoflegends.com/en-us/news/tags/teamfight-tactics-patch-notes/"

    async with ClientSession() as session:
        async with session.get(patch_notes_url) as response:
            if response.status != 200:
                print('Failed to retrieve patch notes')
                return ''
            tft_patch_notes_text = await response.text()

    soup = BeautifulSoup(tft_patch_notes_text, 'html.parser')
    section = soup.find("section", {"data-testid": "article-card-grid"})
    if not section:
        return ''  

    articles = section.find_all("a", href=True)

    for article in articles:
        title_tag = article.find("div", {"data-testid": "card-title"})
        if title_tag:
            title = title_tag.get_text(strip=True)
            if 'Teamfight Tactics patch' in title:
                return title  

    return ''  

