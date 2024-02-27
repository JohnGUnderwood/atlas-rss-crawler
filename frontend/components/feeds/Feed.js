
import styles from "./feeds.module.css";
import axios from 'axios';
import ExpandableCard from "@leafygreen-ui/expandable-card";
import { Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import { useState, useEffect } from 'react';
import Button from "@leafygreen-ui/button";

export default function Feed({feed}){
    const [lastCrawl, setLastCrawl] = useState(null)
    // const [status, setStatus] = useState(feed.status)

    useEffect(()=>{
    },[feed])



    const start = (id) => {
        startCrawl(id)
            .then(r => {
                feed = {...feed, 'status': r.data.insert.status}

            })
            .catch(e => {
                console.log(e)
            })
    };

    const stop = (id) => {
        stopCrawl(id);
    };

    return (
        <ExpandableCard
            style={{marginTop:"10px"}}
            title={`${feed.attribution} - ${feed._id}`}
            description={`${feed.status? feed.status : 'stopped'}`}
            darkMode={false}
        >
            <div style={{ display: "grid", gridTemplateRows: "repeat(4, 1fr)", gap: "10px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
                    <p>
                        <span style={{ fontWeight: "bold" }}>URL: </span><span><Link>{feed.url}</Link></span>
                    </p>
                    <p>
                        <span style={{ fontWeight: "bold" }}>CSS Selector: </span><span>{feed.content_html_selector}</span>
                    </p>
                    <p>
                        <span style={{ fontWeight: "bold" }}>Language: </span><span>{feed.lang}</span>
                    </p>
                    <Button>Test</Button>

                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
                    <p>
                        <span style={{ fontWeight: "bold" }}>Last Crawled: </span><span>{feed.lastCrawl ? `${getElapsedTime(new Date(feed.lastCrawl.start.$date), new Date())} ago` : 'Never'}</span>
                    </p>
                    {
                        feed.lastCrawl ?
                            <>
                            
                                <p>
                                    <span style={{ fontWeight: "bold" }}>Crawled items: </span><span>{feed.lastCrawl.crawled?.length}</span>
                                </p>
                                <p>
                                    <span style={{ fontWeight: "bold" }}>Inserted items: </span><span>{feed.lastCrawl.inserted?.length}</span>
                                </p>
                                <p>
                                    <span style={{ fontWeight: "bold" }}>Errors: </span><span>{feed.lastCrawl.errors?.length}</span>
                                </p>
                            </>
                            : <></>
                    }
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px" }}>
                    <Button variant="primary" onClick={() => start(feed._id)}>Start</Button>
                    <Button variant="dangerOutline" onClick={() => stop(feed.crawlId.$oid)}>Stop</Button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px" }}>
                    <Button variant="dangerOutline">Clear Crawl History</Button>
                    <Button variant="danger">Delete Docs</Button>
                </div>
            </div>
        </ExpandableCard>
    );
};

function getElapsedTime(date1, date2) {
    const elapsed = date2 - date1;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
        const remainingHours = hours % 24;
        const remainingMinutes = minutes % 60;
        return `${days} days, ${remainingHours} hours, ${remainingMinutes} minutes`;
    } else if (hours > 0) {
        const remainingMinutes = minutes % 60;
        return `${hours} hours, ${remainingMinutes} minutes`;
    } else {
        const remainingSeconds = seconds % 60;
        return `${minutes} minutes, ${remainingSeconds} seconds`;
    }
}

async function getCrawl(crawlId) {
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/crawl/${crawlId}`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}

async function startCrawl(feedId) {
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feed/${feedId}/start`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}

async function stopCrawl(crawlId) {
    if(!crawlId) return;
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/crawl/${crawlId}/stop`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}

async function getFeed(id) {
    if(!id) return;
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feed/${id}`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}