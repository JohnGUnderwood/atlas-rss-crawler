
import axios from 'axios';
import { useEffect, useState } from 'react';
import Button from "@leafygreen-ui/button";
import Form from "./Form";
import { Spinner } from '@leafygreen-ui/loading-indicator';
import Code from '@leafygreen-ui/code';

export default function Submit({setFeeds}){
    const [testResult, setTestResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState(
        {
            _id:'',
            lang: '',
            url: '',
            attribution: '',
            content_html_selectors:[''],
            date_format: ''
        });

    const handleSubmit = () => {
        const newFeed = {
            '_id': formData._id,
            'config': {
                'lang': formData.lang,
                'url': formData.url,
                'content_html_selectors': formData.content_html_selectors,
                'attribution': formData.attribution
            }
        };
        // Submit the new feed data
        submitFeed(newFeed).then(response => setFeeds(response.data))
        .catch(e => console.log(e));
    }

    const testFeed = () => {
        setLoading(true)
        fetchTestResult(formData).then(response => {
            setTestResult(response.data);
            setLoading(false);
        }).catch(e => console.log(e));
    };

    useEffect(() => {
        console.log(formData);
    }, [formData]);

    return (
        <div>
            {loading?
                <Spinner variant="large" description="Loading…"/>
            : testResult? 
                <>
                    <Code style={{whiteSpace:"break-spaces"}} language={'json'} copyable={false}>{JSON.stringify(testResult,null,2)}</Code>
                    <div style={{marginTop:"10px", display:"flex", gap:'10px'}}>
                        <Button variant="primary" onClick={testFeed}>Submit Feed</Button>
                        <Button variant="dangerOutline" onClick={() => setTestResult(null)}>Go Back</Button>
                    </div>
                </>
            :   <>
                    <Form formData={formData} setFormData={setFormData}></Form>
                    <Button onClick={testFeed}>Test Feed</Button>
                </>
            }
        </div>
    );
}

async function fetchTestResult(feed) {
    const headers = {
        'Content-Type': 'application/json'
    }
    return new Promise((resolve) => {
        axios.post(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/test`,
            feed,
            {headers: headers})
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}

async function submitFeed(feed) {
    const headers = {
        'Content-Type': 'application/json'
    }
    return new Promise((resolve) => {
        axios.post(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feeds`,
            feed,
            {headers: headers}
        )
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}