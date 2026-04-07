import React, { useEffect, useState } from 'react';
import axios from "axios";
import './App.css';

function App() {
    const [message, setMessage] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('http://localhost:3001/');
                setMessage(response.data);
            } catch (error) {
                console.error(error);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="App">
            <h1>Fullstack React, TypeScript, and Node.js</h1>
            <p>{message}</p>
        </div>
    );
}

export default App;