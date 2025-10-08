import { useState } from "react";
import Header from "@/components/Header";
import ChatWindow from "@/components/ChatWindow";

// IMPORTANT: Update this URL to point to your Flask backend
const API_BASE_URL = "http://127.0.0.1:5000";

export default function Index() {
  const [selectedProject, setSelectedProject] = useState("");

  return (
    <div className="min-h-screen bg-background">
      <Header
        onProjectChange={setSelectedProject}
        selectedProject={selectedProject}
        apiBaseUrl={API_BASE_URL}
      />
      <ChatWindow selectedProject={selectedProject} apiBaseUrl={API_BASE_URL} />
    </div>
  );
}