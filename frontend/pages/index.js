import Feeds from "../components/feeds/Feeds";
import Head from "next/head";

export default function Home(){
  return (
    <>
    <Head>
        <title>RSS Feeds</title>
        <link rel="icon" href="/favicon.ico" />
    </Head>
    <div>
      <Feeds/>
    </div>
    </>
  );
};