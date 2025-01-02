import React, { useEffect, useState } from "react";
import "./App.css"; // Ensure the App.css file is correctly imported

function App() {
  const [faculty, setFaculty] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/faculty")
      .then((response) => response.json())
      .then((data) => setFaculty(data))
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  return (
    <div>
      <header style={{ backgroundColor: "#007bff", color: "#fff", padding: "20px", textAlign: "center" }}>
        <h1>Faculty Dashboard</h1>
      </header>
      <main>
        <div className="faculty-container">
          {faculty.length === 0 ? (
            <p>No data available</p>
          ) : (
            faculty.map((facultyMember) => (
              <div className="faculty-card" key={facultyMember.id}>
                <div className="faculty-image">
                  <img
                    src={`https://via.placeholder.com/150?text=${facultyMember.name}`}
                    alt={facultyMember.name}
                  />
                </div>
                <div className="faculty-info">
                  <h3>{facultyMember.name}</h3>
                  <p><strong>Department:</strong> {facultyMember.department}</p>
                  <p><strong>Building:</strong> {facultyMember.building}</p>
                  <p><strong>Floor:</strong> {facultyMember.floor}</p>
                  <p><strong>Room:</strong> {facultyMember.room}</p>
                  <p><strong>Email:</strong> {facultyMember.email}</p>
                  <p><strong>Phone:</strong> {facultyMember.phone}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
