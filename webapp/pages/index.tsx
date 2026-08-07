import { useState } from "react";

type Score = {
  entity_id: string;
  score: number;
  model_version: string;
  served_version: string;
  request_id: string;
};

export default function Home() {
  const [customerId, setCustomerId] = useState("7590-VHVEG");
  const [score, setScore] = useState<Score | null>(null);

  async function loadScore() {
    const response = await fetch(`/api/v1/score?customer_id=${encodeURIComponent(customerId)}`);
    if (!response.ok) throw new Error("Unable to load score");
    const envelope = (await response.json()) as { data: Score };
    setScore(envelope.data);
  }

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 720, margin: "4rem auto" }}>
      <h1>Enterprise ML Workflow</h1>
      <p>Churn reference adapter: authoritative score, lineage, and governed explanation.</p>
      <label htmlFor="customer-id">Customer ID</label>
      <div>
        <input id="customer-id" value={customerId} onChange={(event) => setCustomerId(event.target.value)} />
        <button onClick={loadScore}>Evaluate</button>
      </div>
      {score && (
        <section aria-label="score" style={{ marginTop: "2rem" }}>
          <h2>Churn score: {score.score.toFixed(2)}</h2>
          <p>Model version: {score.model_version}</p>
          <p>Served version: {score.served_version}</p>
          <small>Request: {score.request_id}</small>
        </section>
      )}
    </main>
  );
}
