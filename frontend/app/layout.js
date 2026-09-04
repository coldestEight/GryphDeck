import "./globals.css";

export const metadata = {
  title: "GryphDeck",
  description: "Gryphon Esports stream overlays",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
