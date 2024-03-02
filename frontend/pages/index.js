import styles from "./styles.module.css";
import Feeds from "../components/feeds/Feeds";
import Head from "next/head";
import { H1,H2, H3, Subtitle, Description, Label } from '@leafygreen-ui/typography';
import { MongoDBLogoMark } from "@leafygreen-ui/logo";
import {SearchInput} from '@leafygreen-ui/search-input';
import Submit from "../components/feeds/Submit";
import Modal from "@leafygreen-ui/modal";
import Button from "@leafygreen-ui/button";
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home(){
  const [open, setOpen] = useState(false);
  const [feeds,setFeeds] = useState(null)
  const [query, setQuery] = useState(null);

  useEffect(()=>{
      
  
      fetchFeeds();
  },[])

  const fetchFeeds = async () => {
    console.log("fetching feeds")
    try {
        const response = await getFeeds();
        setFeeds(response.data);
    } catch (e) {
        console.log(e);
    }
  };

  const handleSearch = () => {
    if(query && query != ""){
      getInstantResults(query)
      .then(resp => setFeeds(resp.data))
      .catch(error => console.log(error));
    }else{
      fetchFeeds();
    }
  };
  
  const handleQueryChange = (event) => {
    setFeeds(null);
    setQuery(event.target.value);
    if(event.target.value && event.target.value != ""){
      getInstantResults(event.target.value)
      .then(resp => setFeeds(resp.data))
      .catch(error => console.log(error));
    }else{
      fetchFeeds();
    }
  };

  return (
    <>
    <Head>
        <title>RSS Feeds</title>
        <link rel="icon" href="/favicon.ico" />
    </Head>
    {/* <div style={{display:"grid",gridTemplateColumns:"160px 80%",alignItems:"start", paddingLeft:"10px"}}> */}
    <div className={styles.container}>
      <div style={{width:"160px",alignItems:"center"}}>
        <H1 style={{textAlign:"center"}}><MongoDBLogoMark height={35}/>Atlas</H1>
        <H3 style={{textAlign:"center"}}>RSS Crawl</H3>
        <div style={{marginLeft:"20px"}}><Button onClick={() => setOpen(true)}>Add Feed</Button></div>
      </div>
      {/* <div style={{paddingTop:"30px",justifyContent:"right", display:"grid",gridTemplateColumns:"90% 70px",gap:"10px",alignItems:"middle", paddingLeft:"16px"}}> */}
      <div className={styles.container} style={{paddingTop:"30px",justifyContent:"end",width:"100%",alignItems:"middle",paddingLeft:"16px"}}>
        <div style={{width:"90%",marginRight:"10px"}}><SearchInput onChange={handleQueryChange} aria-label="some label" style={{marginBottom:"20px"}}></SearchInput></div>
        <div><Button onClick={()=>handleSearch()} variant="primary">Search</Button></div>
      </div>
    </div>

    <Modal open={open} setOpen={setOpen}>
      <Subtitle>Add Feed</Subtitle>
      <Submit setFeeds={setFeeds}/>
    </Modal>
    <div>
      <Feeds feeds={feeds} setFeeds={setFeeds}/>
    </div>
    </>
  );
};

async function getFeeds() {
  return new Promise((resolve) => {
      axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feeds`)
      .then(response => resolve(response))
      .catch((error) => {
          console.log(error)
          resolve(error.response.data);
      });
  });
};

async function getInstantResults(query) {
  return new Promise((resolve) => {
    axios.get(`${process.env.NEXT_PUBLIC_FEEDS_URL}:${process.env.NEXT_PUBLIC_FEEDS_PORT}/feeds/search?q=${query}`)
    .then(response => resolve(response))
    .catch((error) => {
        console.log(error)
        resolve(error.response.data);
    });
  });
};
