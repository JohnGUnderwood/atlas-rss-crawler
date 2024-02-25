
import styles from "../../styles.module.css";
import axios from 'axios';
import ExpandableCard from "@leafygreen-ui/expandable-card";
import { Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import { useState, useEffect } from 'react';

const Feed = ({feed}) => {
    const [lastCrawl, setLastCrawl] = useState(null)

    useEffect(()=>{
        if(feed.crawlId){
            getCrawl(feed.crawlId.$oid)
                .then(r => {
                    setLastCrawl(r.data)
                })
                .catch(e => {
                    console.log(e)
                })
        }
    },[feed.crawlId])

 return (
    <ExpandableCard
        style={{marginTop:"10px"}}
        title={`${feed.attribution} - ${feed._id}`}
        description={`${feed.status? feed.status : 'stopped'}`}
        darkMode={false}
    >
        <div>
            <p>
                <span style={{fontWeight:"bold"}}>URL: </span><span><Link>{feed.url}</Link></span>
            </p>
            <p>
                <span style={{fontWeight:"bold"}}>CSS Selector: </span><span>{feed.content_html_selector}</span>
            </p>
            <p>
                <span style={{fontWeight:"bold"}}>Language: </span><span>{feed.lang}</span>
            </p>
            <p>
                <span style={{fontWeight:"bold"}}>Last Crawled: </span><span>{feed.lastCrawl? Date(feed.lastCrawl.$date) : 'Never'}</span>
            </p>
            {
                lastCrawl?
                <>
                    <p>
                        <span style={{fontWeight:"bold"}}>Crawled items: </span><span>{lastCrawl.crawled?.length}</span>
                    </p>
                    <p>
                        <span style={{fontWeight:"bold"}}>Inserted items: </span><span>{lastCrawl.inserted?.length}</span>
                    </p>
                    <p>
                        <span style={{fontWeight:"bold"}}>Errors: </span><span>{lastCrawl.errors?.length}</span>
                    </p>
                </>
                :<></>
            }
        </div>

        {/* "attribution": "BBC",
        "content_html_selector": "article > div[data-component=\"text-block\"]",
        "crawlId": {
        "$oid": "65db9120f1b894618b8c9a94"
        },
        "lang": "en",
        "lastCrawl": {
        "$date": 1708888352531
        },
        "status": "stopped", */}
    </ExpandableCard>
    );
};

export default Feed;

async function getCrawl(crawlId) {
    return new Promise((resolve) => {
        axios.get(`http://127.0.0.1:5000/crawl/${crawlId}`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
  }