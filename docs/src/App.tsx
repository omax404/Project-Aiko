import { SoulProvider } from '@/context/SoulContext';
import ParticleCanvas from '@/components/ParticleCanvas';
import Navigation from '@/components/Navigation';
import Hero from '@/sections/Hero';
import TheBond from '@/sections/TheBond';
import Senses from '@/sections/Senses';
import SoulModes from '@/sections/SoulModes';
import Satellites from '@/sections/Satellites';
import NeuralHub from '@/sections/NeuralHub';
import SummonAiko from '@/sections/SummonAiko';
import Footer from '@/sections/Footer';

function App() {
  return (
    <SoulProvider>
      <div className="relative min-h-screen bg-obsidian text-moonlight overflow-x-hidden">
        {/* Persistent particle background */}
        <ParticleCanvas />

        {/* Navigation */}
        <Navigation />

        {/* Main content */}
        <main className="relative z-[1]">
          <Hero />
          <TheBond />
          <Senses />
          <SoulModes />
          <Satellites />
          <NeuralHub />
          <SummonAiko />
          <Footer />
        </main>
      </div>
    </SoulProvider>
  );
}

export default App;
