
import styles from "./submit.module.css";
import axios from 'axios';
import { useEffect, useState } from 'react';
import { Subtitle, Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import TextInput from '@leafygreen-ui/text-input';
import Button from "@leafygreen-ui/button";
import Icon from "@leafygreen-ui/icon";

export default function Submit({setFeeds}){
    const [formData, setFormData] = useState(
        {
            _id:'',
            lang: '',
            url: '',
            attribution: '',
            content_html_selectors:[''],
            date_format: ''
        });

    const handleInputChange = (attribute, event, index=null) => {
        
        if(attribute === 'content_html_selectors'){
            setFormData({
                ...formData, 
                content_html_selectors: formData.content_html_selectors.map(
                    (value, i) => i === index ? event.target.value : value)
            });
        }else {
            setFormData({
                ...formData,
                [attribute]: event.target.value
            });
        }
            
    };

    const handleAddClick = () => {
        setFormData({
            ...formData, 
            content_html_selectors: formData.content_html_selectors.concat([''])
        });
    };

    const handleRemoveClick = () => {
        setFormData({
            ...formData, 
            content_html_selectors: formData.content_html_selectors.slice(0, formData.content_html_selectors.length - 1)
        });
    };

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

    useEffect(() => {
        console.log(formData);
    }, [formData]);

    return (
        <div>
            <div className={styles.formRow}>
                <Label htmlFor="_id">ID:</Label>
                <TextInput
                    className={styles.formInput}
                    type="text" id="_id" name="_id" required
                    onChange={event => handleInputChange('_id',event)}/>
                <div className={styles.spacer}></div>
            </div>
            <div className={styles.formRow}>
                <Label htmlFor="lang">Language:</Label>
                <TextInput
                    className={styles.formInput}
                    type="text" id="lang" name="lang" required
                    onChange={event => handleInputChange('lang',event)}/>
                <div className={styles.spacer}></div>
            </div>
            <div className={styles.formRow}>
                <Label htmlFor="url">URL:</Label>
                <TextInput
                    className={styles.formInput}
                    type="text" id="url" name="url" required
                    onChange={event => handleInputChange('url',event)}/>
                <div className={styles.spacer}></div>
            </div>
            <div className={styles.formRow}>
                <Label htmlFor="attribution">Attribution:</Label>
                <TextInput
                    className={styles.formInput}
                    type="text" id="attribution" name="attribution" required
                    onChange={event => handleInputChange('attribution',event)}/>
                <div className={styles.spacer}></div>
            </div>
            {formData.content_html_selectors.map((selector, index) => (
                <div className={styles.formRow} key={index}>
                    <Label htmlFor={`content_html_selector_${index}`}>Content HTML Selector:</Label>
                    <TextInput
                        className={styles.formInput}
                        type="text"
                        id={`content_html_selector_${index}`}
                        name={`content_html_selector_${index}`}
                        value={selector}
                        onChange={event => handleInputChange('content_html_selectors',event,index)}
                        required
                    />
                    {index === formData.content_html_selectors.length - 1 ? (
                        <div className={styles.iconContainer}>
                            <Icon onClick={handleAddClick} glyph={"PlusWithCircle"} fill="#C1C7C6" />
                            {formData.content_html_selectors.length > 1 ? (
                                <Icon onClick={handleRemoveClick} glyph={"XWithCircle"} fill="#C1C7C6" />
                            ):<div style={{width:"16px"}}></div>}
                        </div>
                    ):<div className={styles.spacer}></div>}
                </div>
            ))}
            {/* <button type="button" onClick={handleAddClick}>+</button> */}
            
            
            <Button onClick={handleSubmit}>Submit</Button>
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