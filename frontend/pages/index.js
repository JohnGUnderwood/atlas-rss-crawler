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
  const [feeds,setFeeds] = useState([])

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
    <>
    <Head>
        <title>RSS Feeds</title>
        <link rel="icon" href="/favicon.ico" />
    </Head>
    <div style={{display:"grid",gridTemplateColumns:"10% 80%",gap:"",alignItems:"start", paddingLeft:"10px"}}>
      <div style={{width:"160px"}}>
        <H1 style={{textAlign:"center"}}><MongoDBLogoMark height={35}/>Atlas</H1>
        <H3 style={{textAlign:"center"}}>RSS Crawl</H3>
        <Button style={{marginLeft:"35px"}} onClick={() => setOpen(true)}>Add Feed</Button>
      </div>
      <div style={{paddingTop:"30px",paddingRight:"100px",justifyContent:"right", display:"grid",gridTemplateColumns:"90% 70px",gap:"10px",alignItems:"middle", paddingLeft:"16px"}}>
        {/* <div><SearchInput onChange={handleQueryChange} aria-label="some label" style={{marginBottom:"20px"}}></SearchInput></div>
        <div><Button onClick={()=>handleSearch()} variant="primary">Search</Button></div> */}
        {/* <div>
          <Select 
            label="Languages"
            placeholder="All"
            name="Languages"
            size="xsmall"
            defaultValue="all"
            onChange={handleLanguageChange}
          >
            <Option value="en">English</Option>
            <Option value="fr">French</Option>
            <Option value="es">Spanish</Option>
          </Select>
        </div> */}
      </div>
    </div>

    <Modal open={open} setOpen={setOpen}>
      <Subtitle>Add Feed</Subtitle>
      <Submit setFeeds={setFeeds}/>
    </Modal>
    <div>
      <Feeds feeds={feeds}/>
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
      })
  });
}