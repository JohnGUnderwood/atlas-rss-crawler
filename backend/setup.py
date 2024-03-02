from feeds import feeds
from crawler import MongoDBConnection
from pymongo.errors import CollectionInvalid,OperationFailure

connection=MongoDBConnection()
db=connection.connect()

for c in ["feeds","queue","logs","docs"]:
    try:
        db.create_collection(c,check_exists=True)
    except CollectionInvalid as e:
        print("The {} collection already exists:".format(c), e)
        pass

feeds_search_index = {
    "name":"default",
    "definition":{
        "mappings": {
            "dynamic": False,
            "fields": {
                "_id": {
                    "type": "autocomplete"
                },
                "attribution":{
                    "type": "autocomplete"
                },
                'url':{
                    "type": "autocomplete",
                    "tokenization":"nGram",
                    "minGram":3,
                    "maxGram":20
                }
            }
        }
    }
}

docs_search_index = {
    "name":"searchIndex",
    "definition":{
        "mappings": {
            "dynamic": False,
            "fields": {
            "published": [
                {
                "type": "date"
                },
                {
                "type": "dateFacet"
                }
            ],
            "attribution": [
                {
                "type": "string"
                },
                {
                "type": "token"
                },
                {
                "type": "stringFacet"
                }
            ],
            "authors": [
                {
                "type": "string"
                },
                {
                "type": "token"
                },
                {
                "type": "stringFacet"
                }
            ],
            "lang": [
                {
                "type": "token"
                },
                {
                "type": "stringFacet"
                }
            ],
            "tags": [
                {
                "type": "string"
                },
                {
                "type": "token"
                },
                {
                "type": "stringFacet"
                }
            ],
            "summary": {
                "type": "document",
                "fields": {
                "en": {
                    "type": "string",
                    "analyzer": "lucene.english",
                    "searchAnalyzer": "lucene.english"
                },
                "es": {
                    "type": "string",
                    "analyzer": "lucene.spanish",
                    "searchAnalyzer": "lucene.spanish"
                },
                "fr": {
                    "type": "string",
                    "analyzer": "lucene.french",
                    "searchAnalyzer": "lucene.french"
                }
                }
            },
            "content": {
                "type": "document",
                "fields": {
                "en": {
                    "type": "string",
                    "analyzer": "lucene.english",
                    "searchAnalyzer": "lucene.english"
                },
                "es": {
                    "type": "string",
                    "analyzer": "lucene.spanish",
                    "searchAnalyzer": "lucene.spanish"
                },
                "fr": {
                    "type": "string",
                    "analyzer": "lucene.french",
                    "searchAnalyzer": "lucene.french"
                }
                }
            },
            "title": {
                "type": "document",
                "fields": {
                "en": [
                    {
                    "type": "string",
                    "analyzer": "lucene.english",
                    "searchAnalyzer": "lucene.english"
                    },
                    {
                    "type": "autocomplete"
                    }
                ],
                "es": [
                    {
                    "type": "string",
                    "analyzer": "lucene.spanish",
                    "searchAnalyzer": "lucene.spanish"
                    },
                    {
                    "type": "autocomplete"
                    }
                ],
                "fr": [
                    {
                    "type": "string",
                    "analyzer": "lucene.french",
                    "searchAnalyzer": "lucene.french"
                    },
                    {
                    "type": "autocomplete"
                    }
                ]
                }
            }
            }
        }
        }
}
     

for m in [{'c':"feeds",'m':feeds_search_index},{'c':"docs",'m':docs_search_index}]:
    try:
        db.get_collection(m['c']).create_search_index(model=m['m'])
    except OperationFailure as e:
        if 'codeName' in e.details and e.details['codeName'] == 'IndexAlreadyExists':
            print("Index already exists")
            pass
        else:
            print("Error creating index:", e)
            raise e

installed = list(db["feeds"].find())
if len(installed) < 1:
    db['feeds'].insert_many(feeds)
    print("Installed all feeds: {}".format(", ".join([feed["_id"] for feed in feeds])))
else:
    for feed in feeds:
        print("Processing feed {}".format(feed['_id']))
        if feed['_id'] in [item['_id'] for item in installed]:
            print("\tFeed is already installed") 
        else:
            print("\tAdding config for feed.")
            db['feeds'].insert_one(feed)
connection.close()