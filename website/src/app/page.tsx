import { Nav } from "@/components/sections/Nav";
import { Hero } from "@/components/sections/Hero";
import { Problem } from "@/components/sections/Problem";
import { Architecture } from "@/components/sections/Architecture";
import { Capabilities } from "@/components/sections/Capabilities";
import { QuickStart } from "@/components/sections/QuickStart";
import { Roadmap } from "@/components/sections/Roadmap";
import { Footer } from "@/components/sections/Footer";
import { ScrollOrchestrator } from "@/components/providers/ScrollOrchestrator";

export default function Home() {
  return (
    <>
      <a
        href="#positioning"
        className="fixed top-4 left-4 z-[10000] -translate-y-20 rounded-full bg-lavender px-4 py-2 text-sm text-void opacity-0 transition focus:translate-y-0 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-mist"
      >
        Skip to content
      </a>
      <ScrollOrchestrator />
      <Nav />
      <main>
        <Hero />
        <Problem />
        <Architecture />
        <Capabilities />
        <QuickStart />
        <Roadmap />
      </main>
      <Footer />
    </>
  );
}
