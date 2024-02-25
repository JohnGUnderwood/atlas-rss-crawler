
import styles from "../../styles.module.css";
import axios from 'axios';
import { useState, useEffect } from 'react';
import Feed from './Feed'

const Feeds = () => {
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

export default Feeds;

async function getFeeds() {
    return new Promise((resolve) => {
        axios.get('http://127.0.0.1:5000/feeds')
        .then(response => resolve(response))
        .catch((error) => {
            console.log(error)
            resolve(error.response.data);
        })
    });
  }