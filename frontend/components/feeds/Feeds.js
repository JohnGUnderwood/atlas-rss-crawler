
import styles from "./feeds.module.css";
import axios from 'axios';
import { useState, useEffect } from 'react';
import Feed from './Feed'
import Submit from "./Submit";
import Modal from "@leafygreen-ui/modal";
import { Subtitle, Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import Button from "@leafygreen-ui/button";

export default function Feeds(){
    const [feeds,setFeeds] = useState([])
    const [open, setOpen] = useState(false);

    useEffect(()=>{
        const fetchFeeds = async () => {
            console.log("fetching feeds")
            try {
                const response = await getFeeds();
                setFeeds(response.data);
            } catch (e) {
                console.log(e);
            }
        };
    
        fetchFeeds();  // fetch feeds immediately
    
        // const intervalId = setInterval(fetchFeeds, 20000);  // fetch feeds every 60 seconds
    
        // return () => clearInterval(intervalId);  // clear interval on component unmount
    },[])

    return (
        <div>
            <Button onClick={() => setOpen(true)}>Add Feed</Button>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(500px, 1fr))', gap:'10px', padding:"10px"}}>
            {
                feeds?.map(f => (
                    <Feed key={f._id} f={f}/>
                ))
            }
            </div>
            <Modal open={open} setOpen={setOpen}>
                <Subtitle>Add Feed</Subtitle>
                <Submit setFeeds={setFeeds}/>
            </Modal>
        </div>
        );
    };

async function getFeeds() {
    return new Promise((resolve) => {
        axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feeds`)
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
}