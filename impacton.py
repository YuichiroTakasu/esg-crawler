import requests
from bs4 import BeautifulSoup
import time, random
import os, json
from tqdm import tqdm


def preprocess(text):
    return text.replace('\n', ' ').replace('\t', ' ').replace('\r', '').replace(' ', '')


def get_article_links(url, suburl):
    html = requests.get(url+suburl)
    soup = BeautifulSoup(html.content, 'html.parser')

    page_links = list(set([x.get('href') for x in soup.find_all('ul', class_="pagination")[0].find_all('a')]))

    all_article_urls = []
    for page_link in page_links:
        html = requests.get(url + page_link)
        soup = BeautifulSoup(html.content, 'html.parser')
        article_urls = list(set([x.get('href') for x in soup.find_all('ul', class_="type2")[0].find_all('a')]))
        all_article_urls.append(article_urls)
        time.sleep(1)

    all_article_urls = [item for sublist in all_article_urls for item in sublist]

    return all_article_urls


def get_article_contents(url, suburl):
    html = requests.get(url+suburl)
    soup = BeautifulSoup(html.content, 'html.parser')

    # news
    news_dict = {}
    header = soup.find('h3', class_="heading").get_text()
    if soup.find('h4', class_="subheading") != None:
        subheader = soup.find('h4', class_="subheading").get_text()
        news_dict['subheader'] = subheader
    else:
        news_dict['subheader'] = ''
    article_body = [preprocess(x.get_text()) for x in soup.find_all('article', {"id": "article-view-content-div"})[0].find_all('p')]

    if soup.find('article', class_='relation') != None:
        related_articles = [x['href'] for x in soup.find('article', class_='relation').find_all('a')]
    else:
        related_articles = []

    news_dict['header'] = header
    news_dict['article_body'] = list(filter(None, article_body))
    news_dict['related_articles'] = related_articles

    return news_dict


def main():
    url = 'http://www.impacton.net'
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')

    # 기업, 정책, 글로벌 part 먼저 크롤링
    sections = [x.find_all('li', class_='sub') for x in soup.find_all('li', {"class": "secline"})[:3]]
    all_sections = []
    for section in sections:
        for x in section:
            section_url = x.find('a').get('href')
            section_title = x.get_text().replace('\n', '')
            all_sections.append((section_title, section_url))

    # get all article links
    for section in all_sections:
        section_title = section[0]
        section_url = section[1]
        all_articles = get_article_links(url=url, suburl=section_url)
        print(section_title, len(all_articles))

        if not os.path.exists(f'./{section_title}'):
            os.mkdir(f'./{section_title}')

        for article_url in tqdm(all_articles):
            article_id = article_url.split('=')[-1]
            article_filepath = os.path.join(section_title, article_id + '.json')

            if not os.path.exists(article_filepath):
                try:
                    news = get_article_contents(url, article_url)
                    with open(article_filepath, 'w') as fp:
                        json.dump(news, fp)
                except Exception as e:
                    print(article_url, e)

            time.sleep(random.uniform(0.5, 1.5))

        time.sleep(random.uniform(5, 10))


if __name__ == "__main__":
    main()

    # url = 'http://www.impacton.net'
    # suburl = '/news/articleView.html?idxno=100'
    #
    # print(get_article_contents(url, suburl))