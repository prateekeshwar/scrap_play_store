import requests
import re
from bs4 import BeautifulSoup
from urllib import quote_plus
from urlparse import urljoin


def details(app_id):
    url = build_url('details', app_id)
    params ={
        'hl': 'en',
        'gl': 'in'
    }
    try:
        response = send_request('GET', url, params=params)
        soup = BeautifulSoup(response.content, 'lxml', from_encoding='utf8')
    except requests.exceptions.HTTPError as e:
        raise ValueError('Invalid application ID: {app}. {error}'.format(
            app=app_id, error=e))

    app_json = parse_app_details(soup)
    app_json.update({
        'app_id': app_id,
        'url': url,
    })
    return app_json



def search(query):
    search_url='https://play.google.com/store/search'
    data = generate_post_data(0, 0)
    params ={
        'hl': 'en',
        'gl': 'in',
        'q': quote_plus(query),
        'c': 'apps',
    }
    response = send_request('POST', search_url, data, params)
    soup = BeautifulSoup(response.content, 'lxml', from_encoding='utf8')
    apps = [parse_card_info(app)
            for app in soup.select('div[data-uitype="500"]')]

    return apps

def generate_post_data(results=None, page=None, children=0):
    data = {
        'ipf': 1,
        'xhr': 1
    }
    if children:
        data['numChildren'] = children
    if results is not None:
        if page is not None:
            start = 0 if page <= 0 else results * page
            data['start'] = start
        data['num'] = results
    data['pagTok'] = ''
    return data


def send_request(method, url, data=None, params=None, headers=None,
                 timeout=30, verify=True, allow_redirects=False):
    data = {} if data is None else data
    params = {} if params is None else params
    headers = default_headers() if headers is None else headers
    if not data and method == 'POST':
        data = generate_post_data()
    try:
        response = requests.request(
            method=method,
            url=url,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
            verify=verify,
            allow_redirects=allow_redirects)
        if not response.status_code == requests.codes.ok:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(str(e))

    return response

def default_headers():
    user_agent=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/45.0.2454.101 Safari/537.36')
    return {
        'Origin': 'https://play.google.com',
        'User-Agent': user_agent,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }

def build_url(method, id_string):
    base_url='https://play.google.com/store/apps'
    if method == 'developer':
        id_string = quote_plus(id_string)

    url = "{base}/{method}?id={id}".format(
        base=base_url, method=method, id=id_string)
    return url


def parse_app_details(soup):
    title = soup.select_one('h1[itemprop="name"] span').text
    if soup.select_one('.dQrBL img.ujDFqe') is not None:
        icon = (soup.select_one('.dQrBL img.ujDFqe')
                .attrs['src']
                .split('=')[0])
    else:
        icon = None
    editors_choice = bool(
        soup.select_one('meta[itemprop="editorsChoiceBadgeUrl"]'))

    # Main category will be first
    category = [c.attrs['href'].split('/')[-1]
                for c in soup.select('a[itemprop="genre"]')]

    # Let the user handle modifying the URL to fetch different resolutions
    # Removing the end `=w720-h310-rw` doesn't seem to give original res?
    # Check 'src' and 'data-src' since it can be one or the other
    screenshots = [parse_screenshot_src(img)
                   for img in soup.select('button.NIc6yf img.lxGQyd')]

    try:
        video = (soup.select_one('button[data-trailer-url^="https"]')
                     .attrs.get('data-trailer-url'))
        if video is not None:
            video = video.split('?')[0]
    except AttributeError:
        video = None

    description_soup = soup.select_one(
        'div[itemprop="description"] content div')
    if description_soup:
        description = '\n'.join(description_soup.stripped_strings)
        description_html = description_soup.encode_contents()
    else:
        description = description_html = None

    # Reviews & Ratings
    try:
        score = soup.select_one('div.BHMmbe').text
    except AttributeError:
        score = None

    histogram = {}
    try:
        reviews = int(soup.select_one('span[aria-label$="ratings"]')
                          .text
                          .replace(',', ''))
        ratings_section = soup.select_one('div.VEF2C')
        num_ratings = [int(rating.attrs.get('title', "0,0").replace(',', ''))
                       for rating in ratings_section.select(
                           'div span[style^="width:"]')]
        for i in range(5):
            histogram[5 - i] = num_ratings[i]
    except AttributeError:
        reviews = 0

    try:
        changes_soup = soup.select('div[itemprop="description"] content')[1]
        recent_changes = '\n'.join([x.string.strip() if x.string is not None else ''
                                    for x in changes_soup])
    except (IndexError, AttributeError):
        recent_changes = None

    try:
        price = soup.select_one('meta[itemprop="price"]').attrs['content']
    except AttributeError:
        try:
            price = soup.select_one('not-preregistered').string.strip()
        except AttributeError:
            price = None
    free = (price == '0')
    additional_info_data = parse_additional_info(
        soup.select_one('.IxB2fe'))
    offers_iap = bool(additional_info_data.get('iap_range'))
    try:
        dev_id = soup.select_one('a.hrTbp.R8zArc').attrs['href'].split('=')[1]
    except IndexError:
        dev_id = None
    developer_id = dev_id if dev_id else None
    data = {
        'title': title,
        'icon': icon,
        'screenshots': screenshots,
        'video': video,
        'category': category,
        'score': score,
        'histogram': histogram,
        'reviews': reviews,
        'description': description,
        'description_html': description_html,
        'recent_changes': recent_changes,
        'editors_choice': editors_choice,
        'price': price,
        'free': free,
        'iap': offers_iap,
        'developer_id': developer_id,
    }
    data.update(additional_info_data)
    return data

def parse_screenshot_src(img):
    src = img.attrs.get('src')
    if src is None or not src.startswith('https://'):
        src = img.attrs.get('data-src')
    return src


def parse_additional_info(soup):
    # This is super ugly because the CSS is obfuscated and doesn't have good
    # distinguishing selectors available; each section's markup is nearly
    # identical, so we get the values with a similar function.
    section_titles_divs = [x for x in soup.select('div.hAyfc div.BgcNfc')]

    title_normalization = {
        'Updated': 'updated',
        'Size': 'size',
        'Installs': 'installs',
        'Current Version': 'current_version',
        'Requires Android': 'required_android_version',
        'Content Rating': 'content_rating',
        'In-app Products': 'iap_range',
        'Interactive Elements': 'interactive_elements',
        'Offered By': 'developer',
        'Developer': 'developer_info',
    }

    data = {
        'updated': None,
        'size': None,
        'installs': None,
        'current_version': None,
        'required_android_version': None,
        'content_rating': None,
        'iap_range': None,
        'interactive_elements': None,
        'developer': None,
        'developer_email': None,
        'developer_url': None,
        'developer_address': None,
    }

    for title_div in section_titles_divs:
        section_title = title_div.string
        if section_title in title_normalization:
            title_key = title_normalization[section_title]
            value_div = title_div.next_sibling.select_one('span.htlgb')

            if title_key == 'content_rating':
                # last string in list is 'Learn more' link
                value = [rating.strip()
                         for rating in value_div.strings][:-1]
            elif title_key == 'interactive_elements':
                value = [ielement.strip()
                         for ielement in value_div.strings]
            elif title_key == 'iap_range':
                iaps = re.search(r'(\$\d+\.\d{2}) - (\$\d+\.\d{2})',
                                 value_div.string)
                if iaps:
                    value = iaps.groups()
            elif title_key == 'developer_info':
                developer_email = value_div.select_one('a[href^="mailto:"]')
                if developer_email:
                    developer_email = (developer_email.attrs['href']
                                                      .split(':')[1])
                developer_url = value_div.select_one('a[href^="http"]')
                if developer_url:
                    developer_url = developer_url.attrs['href']

                developer_address = value_div.select('div')[-1].contents[0]
                if developer_address.name is not None:
                    developer_address = None
                if developer_address is not None:
                    developer_address = developer_address.strip()

                dev_data = {'developer_email': developer_email,
                            'developer_url': developer_url,
                            'developer_address': developer_address}
                data.update(dev_data)
                continue
            else:
                value = value_div.text

            data[title_key] = value
    return data


def parse_card_info(soup):
    base_url='https://play.google.com/store/apps'
    app_id = soup.attrs['data-docid']
    url = urljoin(base_url,
                  soup.select_one('a.card-click-target').attrs['href'])
    icon = urljoin(
        base_url,
        soup.select_one('img.cover-image').attrs['src'].split('=')[0])
    title = soup.select_one('a.title').attrs['title']

    dev_soup = soup.select_one('a.subtitle')
    developer = dev_soup.attrs['title']
    try:
        developer_id = dev_soup.attrs['href'].split('=')[1]
    except IndexError:
        developer_id = None

    description = soup.select_one('div.description').text.strip()
    score = soup.select_one('div.tiny-star')
    if score is not None:
        score = score.attrs['aria-label'].strip().split(' ')[1]

    try:
        price = soup.select_one('span.display-price').text
    except AttributeError:
        try:
            # Pre-register apps are 'Coming Soon'
            price = soup.select_one('a.price').text
        except AttributeError:
            # Country restricted, no price or buttons shown
            price = None

    full_price = None
    if price is not None:
        try:
            full_price = soup.select_one('span.full-price').text
        except AttributeError:
            full_price = None

    free = (price is None)
    if free is True:
        price = '0'

    return {
        'app_id': app_id,
        'url': url,
        'icon': icon,
        'title': title,
        'developer': developer,
        'developer_id': developer_id,
        'description': description,
        'score': score,
        'full_price': full_price,
        'price': price,
        'free': free
    }
