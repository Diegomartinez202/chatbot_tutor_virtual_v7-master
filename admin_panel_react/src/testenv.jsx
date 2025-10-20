import React from 'react';
import { API_URL, BOT_NAME } from './config';

const TestEnv = () => {
    return (
        <div style={{ padding: '20px', fontFamily: 'Arial' }}>
            <h2>🧪 Prueba de Variables de Entorno</h2>
            <p><strong>API_URL:</strong> {API_URL}</p>
            <p><strong>BOT_NAME:</strong> {BOT_NAME}</p>
        </div>
    );
};

export default TestEnv;
