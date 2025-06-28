import React, { useState, useEffect } from 'react';
import axios from 'axios';

const HealthCheckPanel: React.FC = () => {
  const [isHealthy, setIsHealthy] = useState<boolean>(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get('http://localhost:8000/health');
        if (response.status === 200) {
          setIsHealthy(true);
        }
      } catch (error) {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center justify-center h-full">
      <div className={`w-4 h-4 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <p className="ml-2">{isHealthy ? 'Backend Conectado' : 'Error de Conexión'}</p>
    </div>
  );
}

export default HealthCheckPanel;
