
import styles from "./feeds.module.css";
import axios from 'axios';
import { useState, useEffect } from 'react';
import Feed from './Feed'

export default function Feeds(){
    const [feeds,setFeeds] = useState([])

    useEffect(()=>{
        getFeeds()
            .then(r => {
                setFeeds(r.data);
            })
            .catch(e => {
                console.log(e);
            })
    },[])

    return (
        <div>
        {
            feeds?.map(f => (
                <Feed key={f._id} feed={f}/>
            ))
        }
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