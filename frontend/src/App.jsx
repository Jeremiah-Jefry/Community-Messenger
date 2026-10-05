import { useState, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [message, setMessage] = useState("Loading....");

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch(() => setMessage("Failed to reach the API"))
  }, []);

  return (
    <div>
      <h1>{message}</h1>
    </div>
  );
}

export default App;