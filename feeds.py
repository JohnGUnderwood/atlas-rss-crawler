feeds = [
    {
        '_id':'bbc_world',
        'lang':'en',
        'url':"https://feeds.bbci.co.uk/news/world/rss.xml",
        'interval':1,
        'unit':'minutes',
        'date_format':'%a, %d %b %Y %H:%M:%S %Z',
        'content_html_selector':'article > div[data-component="text-block"]',
        'attribution':'BBC'
    },
    {
        '_id':'bbc_mundo',
        'lang':'es',
        'url':"https://feeds.bbci.co.uk/mundo/rss.xml",
        'interval':1,
        'unit':'minutes',
        'date_format':'%a, %d %b %Y %H:%M:%S %Z',
        'content_html_selector':'main > div > p',
        'attribution':'BBC Mundo'

    },
    {
        '_id':'france_24_en',
        'lang':'en',
        'url':"https://www.france24.com/en/rss",
        'interval':1,
        'unit':'minutes',
        'date_format':'%a, %d %b %Y %H:%M:%S %Z',
        'content_html_selector':"p.t-content__chapo,div.t-content__body > p",
        'attribution':'France24'
    },
    {
        '_id':'france_24_fr',
        'lang':'fr',
        'url':"https://www.france24.com/fr/rss",
        'interval':1,
        'unit':'minutes',
        'date_format':'%a, %d %b %Y %H:%M:%S %Z',
        'content_html_selector':"p.t-content__chapo,div.t-content__body > p",
        'attribution':'France24'
    },
    {
        '_id':'france_24_es',
        'lang':'es',
        'url':"https://www.france24.com/es/rss",
        'interval':1,
        'unit':'minutes',
        'date_format':'%a, %d %b %Y %H:%M:%S %Z',
        'content_html_selector':"p.t-content__chapo,div.t-content__body > p",
        'attribution':'France24'
    }
]