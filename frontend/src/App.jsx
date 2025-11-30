import React, { useState } from 'react';
import GPUList from './components/GPUList';
import ReservationForm from './components/ReservationForm';
import ReservationTimeline from './components/ReservationTimeline';
import './index.css';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleReservationCreated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="app-container">
      <header>
        <h1>GPU予約システム</h1>
      </header>
      <main>
        <section className="gpu-section">
          <GPUList key={refreshTrigger} /> {/* Refresh GPU list too as status might change */}
        </section>
        <section className="reservation-section">
          <div className="form-container">
            <ReservationForm onReservationCreated={handleReservationCreated} />
          </div>
          <div className="timeline-container">
            <ReservationTimeline refreshTrigger={refreshTrigger} />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
