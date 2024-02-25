import styles from "../styles.module.css";
import Feeds from "../components/feeds/Feeds";

const Home = () => {
  return (
    <div className={styles.hello}>
      <Feeds/>
    </div>
  );
};

export default Home;