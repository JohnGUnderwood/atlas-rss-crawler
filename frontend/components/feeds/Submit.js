
import styles from "./feeds.module.css";
import axios from 'axios';
import { Subtitle, Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import TextInput from '@leafygreen-ui/text-input';

export default function Submit({setFeeds}){
    const handleSubmit = (event) => {
        console.log(event.target);
        event.preventDefault();
        const formData = new FormData(event.target);
        const newFeed = {
            '_id': formData.get('id'),
            'config': {
                'lang': formData.get('lang'),
                'url': formData.get('url'),
                'content_html_selector': formData.get('content_html_selector'),
                'attribution': formData.get('attribution')
            }
        };
        // Submit the new feed data
        submitFeed(newFeed).then(response => setFeeds(response.data))
        .catch(e => console.log(e));
        
    }

    return (
        <div className={styles.formContainer}>
                <form onSubmit={handleSubmit}>
                {/* <TextInput
                    id="_id"
                    label="ID"
                    description="Unique identifier for the feed"
                /> */}
                    <label htmlFor="id">ID:</label>
                    <input type="text" id="id" name="id" required />
                    <label htmlFor="lang">Language:</label>
                    <input type="text" id="lang" name="lang" required />
                    <label htmlFor="url">URL:</label>
                    <input type="text" id="url" name="url" required />
                    <label htmlFor="content_html_selector">Content HTML Selector:</label>
                    <input type="text" id="content_html_selector" name="content_html_selector" required />
                    <label htmlFor="attribution">Attribution:</label>
                    <input type="text" id="attribution" name="attribution" required />
                    <button type="submit">Submit</button>
                </form>
            </div>
    );
}


async function submitFeed(feed) {
    const headers = {
        'Content-Type': 'application/json'
    }
    console.log(feed);
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