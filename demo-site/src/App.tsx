import { Hero } from "./components/Hero";
import { Problem } from "./components/Problem";
import { Roles } from "./components/Roles";
import { LiveEpisode } from "./components/LiveEpisode";
import { Rubric } from "./components/Rubric";
import { Tasks } from "./components/Tasks";
import { Results } from "./components/Results";
import { Footer } from "./components/Footer";
import { Nav } from "./components/Nav";

export default function App() {
  return (
    <div id="top" className="relative z-10">
      <Nav />
      <Hero />
      <Problem />
      <Roles />
      <LiveEpisode />
      <Rubric />
      <Tasks />
      <Results />
      <Footer />
    </div>
  );
}
