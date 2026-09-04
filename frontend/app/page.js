import Link from "next/link";

const scenes = ["idle", "pregame", "ingame", "UI"];

export default function Home() {
  return (
    <main className="scene ui">
      <div className="card">
        <p className="eyebrow">GryphDeck</p>
        <h1>Scene previews</h1>
        <nav>
          {scenes.map((scene) => (
            <Link key={scene} href={`/${scene}`}>
              /{scene}
            </Link>
          ))}
        </nav>
      </div>
    </main>
  );
}
