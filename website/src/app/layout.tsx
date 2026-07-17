import type { Metadata, Viewport } from "next";
import { Fraunces, Outfit, JetBrains_Mono } from "next/font/google";
import { SmoothScroll } from "@/components/providers/SmoothScroll";
import { EmotionProvider } from "@/components/providers/EmotionProvider";
import { CustomCursor } from "@/components/ui/CustomCursor";
import "./globals.css";

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  axes: ["SOFT", "WONK", "opsz"],
  display: "swap",
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Aiko — Living Neural Ecosystem",
    template: "%s · Aiko",
  },
  description:
    "Self-hosted, you-owned AI companion with emotional depth, long-term memory, and real agency. Neuromodulator emotion engine, Unified Memory, local Pocket-TTS, multimodal vision, and a proactive ReAct agent.",
  keywords: [
    "Aiko",
    "AI companion",
    "self-hosted AI",
    "local LLM",
    "emotional AI",
    "Live2D",
    "Pocket-TTS",
    "Project-Aiko",
  ],
  authors: [{ name: "Aiko Team" }],
  openGraph: {
    title: "Aiko — Living Neural Ecosystem",
    description:
      "She doesn't just chat — she thinks, feels, remembers, sees, speaks, and acts. Self-hosted emotional intelligence.",
    type: "website",
    url: "https://github.com/omax404/Project-Aiko",
  },
  twitter: {
    card: "summary_large_image",
    title: "Aiko — Living Neural Ecosystem",
    description:
      "Self-hosted AI companion with neuromodulator emotions, unified memory, and real agency.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#0B0810",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${fraunces.variable} ${outfit.variable} ${jetbrains.variable} h-full antialiased`}
    >
      <body className="min-h-full font-sans">
        <EmotionProvider>
          <SmoothScroll>
            <CustomCursor />
            {children}
          </SmoothScroll>
        </EmotionProvider>
      </body>
    </html>
  );
}
