
import styles from "./feeds.module.css";
import axios from 'axios';
import ExpandableCard from "@leafygreen-ui/expandable-card";
import { Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import { useRef, useState, useEffect } from 'react';
import Button from "@leafygreen-ui/button";

export default function Feed({f}){
    const [lastCrawl, setLastCrawl] = useState(null)
    const [feed, setFeed] = useState(f);
    const intervalId = useRef();


    useEffect(() => {
        if (feed.status && feed.status !== 'stopped' && feed.status !== 'stopping' && feed.status !== 'finished') {
            console.log(feed.status);
            intervalId.current = setInterval(() => {
                fetchFeed(feed._id).then(response => {
                    console.log('fetching feed');
                    setFeed(response.data);
                });
            }, 3000);
        } else if (feed.status === 'stopping') {
            intervalId.current = setInterval(() => {
                fetchFeed(feed._id).then(response => {
                    console.log('fetching feed');
                    setFeed(response.data);
                });
            }, 5000);
        } else {
            clearInterval(intervalId.current);
        }
        // Clean up on unmount
        return () => clearInterval(intervalId.current);
    }, [feed]);

    const start = (id) => {
        startCrawl(id).then(r => {
            console.log(r);
            setFeed(prevFeed => ({...prevFeed, status: r.data.status}))
        }).catch(e => console.log(e));
    };

    const stop = (id) => {
        stopCrawl(id).then(r => {
            console.log(r);
            setFeed(prevFeed => ({...prevFeed, status: r.data.status}))
        }).catch(e => console.log(e));
    };

    const clear = (id) => {
        clearCrawlHistory(id).then(response => setFeed(response.data)).catch(e => console.log(e));
    };

    return (
        <ExpandableCard
            style={{marginTop:"10px"}}
            title={`${feed.config.attribution} - ${feed._id}`}
            description={`${feed.status? feed.status : 'not run'}`}
            darkMode={false}
        >
            <div style={{ display: "grid", gridTemplateRows: "repeat(3, 1fr)", gap: "10px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
                    <p>
                        <span style={{ fontWeight: "bold" }}>URL: </span><span><Link>{feed.config.url}</Link></span>
                    </p>
                    <p>
                        <span style={{ fontWeight: "bold" }}>CSS Selector: </span><span>{feed.config.content_html_selector}</span>
                    </p>
                    <p>
                        <span style={{ fontWeight: "bold" }}>Language: </span><span>{feed.config.lang}</span>
                    </p>
                    <Button>Test</Button>
                </div>
                <div>
                    <div>
                        <span style={{ fontWeight: "bold" }}>Last Crawled: </span><span>{feed.crawl ? `${getElapsedTime(new Date(feed.crawl.start?.$date), new Date())} ago` : 'Never'}</span>
                    
                    
                        {
                            feed.crawl ?
                            feed.crawl.skipped.length >= feed.crawl.crawled.length?
                            <p>
                                <span>No new entries found.</span>
                            </p>
                            :<div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "10px" }}>
                            
                            <p>
                                <span style={{ fontWeight: "bold" }}>Crawled items: </span><span>{feed.crawl.crawled?.length}</span>
                            </p>
                            <p>
                                <span style={{ fontWeight: "bold" }}>Inserted items: </span><span>{feed.crawl.inserted?.length}</span>
                            </p>
                            <p>
                                <span style={{ fontWeight: "bold" }}>Skipped items: </span><span>{feed.crawl.skipped?.length}</span>
                            </p>
                            <p>
                                <span style={{ fontWeight: "bold" }}>Duplicates found: </span><span>{feed.crawl.duplicates?.length}</span>
                            </p>
                            <p>
                                <span style={{ fontWeight: "bold" }}>Errors: </span><span>{feed.crawl.errors?.length}</span>
                            </p>
                            </div>
                            :<></>
                        }
                    </div>
                    
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px" }}>
                    {feed.status == 'running'?<Button variant="danger" onClick={() => stop(feed._id)}>Stop</Button>
                    :feed.status == 'starting'? <Button variant="primaryOutline">Start</Button>
                    :feed.status == 'stopping'? <Button variant="dangerOutline">Stop</Button>
                    :<Button variant="primary" onClick={() => start(feed._id)}>Start</Button>}
                    <Button variant="dangerOutline" onClick={() => clear(feed._id)}>Clear Crawl History</Button>
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

async function fetchFeed(feedId) {
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feed/${feedId}`)
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

async function stopCrawl(feedId) {
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feed/${feedId}/stop`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}

async function clearCrawlHistory(feedId) {
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feed/${feedId}/history/clear`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}