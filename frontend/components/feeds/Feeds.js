
import styles from "./feeds.module.css";
import { useState, useEffect } from 'react';
import Feed from './Feed'
import Modal from "@leafygreen-ui/modal";
import { Subtitle, Label, Description, Overline, Link} from "@leafygreen-ui/typography";
import Button from "@leafygreen-ui/button";

export default function Feeds({feeds,setFeeds}){
    return (
        <div>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(500px, 1fr))', gap:'10px', padding:"10px"}}>
            {feeds?
                Object.keys(feeds).map(key => (
                    <Feed key={key} f={feeds[key]} feeds={feeds} setFeeds={setFeeds}/>
                ))
            :<></>
            }
            </div>
        </div>
        );
    };