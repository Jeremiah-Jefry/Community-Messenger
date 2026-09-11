import { useState, useEffect } from "react";

function App() {
  const [message, setMessage] = useState("Loading....");

  useEffect(() => {
    fetch('http://127.0.0.1:8000/')
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => setMessage("Failed to reach the API"))
  }, []);

  return (
    <div>
      <h1>{message}</h1>
    </div>
  );
}

export default App;