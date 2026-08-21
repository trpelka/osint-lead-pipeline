import { useEffect, useState } from "react";
import "./App.css";

const API_BASE =
  "https://crispy-goggles-g44pwjvpqw4v364v-8000.app.github.dev";

type Lead = {
  id: number;
  company: string;
  domain: string;
  email: string;
  notes: string | null;
};

export default function App() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadLeads() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        API_BASE + "/api/leads?limit=100"
      );

      if (!response.ok) {
        throw new Error(
          "API returned HTTP " + response.status
        );
      }

      const data = await response.json();
      setLeads(data);
    } catch (err) {
      console.error(err);
      setError(
        "Could not connect to the Codespaces API."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLeads();
  }, []);

  return (
    <div className="app">
      <header>
        <h1>OSINT Lead Pipeline</h1>
        <p>
          Company discovery, email extraction and lead
          management.
        </p>
      </header>

      <section className="card">
        <h2>Statistics</h2>
        <strong>{leads.length}</strong>
        <span> leads</span>
      </section>

      <section className="card">
        <h2>Leads</h2>

        {loading && <p>Loading...</p>}

        {error && (
          <p className="error">{error}</p>
        )}

        {!loading &&
          !error &&
          leads.length === 0 && (
            <p>No leads found.</p>
          )}

        {!loading &&
          !error &&
          leads.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Company</th>
                  <th>Domain</th>
                  <th>Email</th>
                  <th>Notes</th>
                </tr>
              </thead>

              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id}>
                    <td>{lead.id}</td>
                    <td>{lead.company}</td>
                    <td>{lead.domain}</td>
                    <td>{lead.email}</td>
                    <td>
                      {lead.notes || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </section>

      <footer>
        <a
          href={API_BASE + "/docs"}
          target="_blank"
          rel="noreferrer"
        >
          Open API documentation
        </a>
      </footer>
    </div>
  );
}