"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export default function SceneView({ scene }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadScene() {
      try {
        const response = await fetch(`${API_URL}/api/scenes/${scene}`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`API returned ${response.status}`);
        setData(await response.json());
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError("Unable to reach the GryphDeck API.");
        }
      }
    }

    loadScene();
    return () => controller.abort();
  }, [scene]);

  if (error) return <main className="scene error"><p>{error}</p></main>;
  if (!data) return <main className="scene loading"><p>Loading scene…</p></main>;

  return (
    <main className={`scene ${data.theme}`}>
      <div className="card">
        <p className="eyebrow">{data.scene}</p>
        <h1>{data.title}</h1>
        <p>{data.message}</p>

        {data.teams && (
          <div className="teams">
            <span>{data.teams[0]}</span>
            <strong>{data.score ? `${data.score.home} – ${data.score.away}` : "VS"}</strong>
            <span>{data.teams[1]}</span>
          </div>
        )}

        {data.routes && (
          <nav>
            {data.routes.map((route) => <a key={route} href={route}>{route}</a>)}
          </nav>
        )}
      </div>
    </main>
  );
}
