import React, { useEffect, useState } from 'react';
import { fetchGPUs } from '../api';

const GPUList = () => {
    const [gpus, setGpus] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadGPUs = async () => {
            try {
                const data = await fetchGPUs();
                setGpus(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        loadGPUs();
    }, []);

    if (loading) return <div>Loading GPUs...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    return (
        <div className="gpu-list">
            <h2>GPUリソース</h2>
            <div className="gpu-grid">
                {gpus.map((item) => (
                    <div key={item.gpu.id} className="gpu-card">
                        <h3>{item.gpu.name}</h3>
                        <p><strong>モデル:</strong> {item.gpu.model}</p>
                        <p><strong>メモリ:</strong> {item.gpu.memory_gb} GB</p>
                        <p><strong>ホスト:</strong> {item.gpu.hostname}</p>
                        <div className={`status-badge ${item.is_available_now ? 'available' : 'occupied'}`}>
                            {item.is_available_now ? '利用可能' : '使用中'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default GPUList;
