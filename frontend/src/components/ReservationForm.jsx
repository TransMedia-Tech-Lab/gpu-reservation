import React, { useState, useEffect } from 'react';
import { fetchGPUs, createReservation } from '../api';

const ReservationForm = ({ onReservationCreated }) => {
    const [gpus, setGpus] = useState([]);
    const [formData, setFormData] = useState({
        gpu_id: '',
        user: '',
        purpose: '',
        start_time: '',
        end_time: '',
    });
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    useEffect(() => {
        const loadGPUs = async () => {
            try {
                const data = await fetchGPUs();
                setGpus(data);
                if (data.length > 0) {
                    setFormData(prev => ({ ...prev, gpu_id: data[0].gpu.id }));
                }
            } catch (err) {
                console.error('Failed to load GPUs', err);
            }
        };
        loadGPUs();
    }, []);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const toIsoString = (value) => {
        // datetime-local はタイムゾーン情報を含まないので、ローカル時刻として解釈し UTC ISO に変換する
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? null : date.toISOString();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);

        const startIso = toIsoString(formData.start_time);
        const endIso = toIsoString(formData.end_time);

        if (!startIso || !endIso) {
            setError('日時の形式が不正です');
            return;
        }

        try {
            await createReservation({
                ...formData,
                gpu_id: parseInt(formData.gpu_id),
                start_time: startIso,
                end_time: endIso,
            });
            setSuccess('予約を作成しました！');
            setFormData({
                ...formData,
                purpose: '',
                start_time: '',
                end_time: '',
            });
            if (onReservationCreated) onReservationCreated();
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="reservation-form">
            <h2>GPU予約</h2>
            {error && <div className="error">{error}</div>}
            {success && <div className="success">{success}</div>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>GPU:</label>
                    <select name="gpu_id" value={formData.gpu_id} onChange={handleChange} required>
                        {gpus.map(item => (
                            <option key={item.gpu.id} value={item.gpu.id}>{item.gpu.name} ({item.gpu.model})</option>
                        ))}
                    </select>
                </div>
                <div className="form-group">
                    <label>ユーザー:</label>
                    <input type="text" name="user" value={formData.user} onChange={handleChange} required />
                </div>
                <div className="form-group">
                    <label>目的:</label>
                    <input type="text" name="purpose" value={formData.purpose} onChange={handleChange} required />
                </div>
                <div className="form-group">
                    <label>開始日時:</label>
                    <input type="datetime-local" name="start_time" value={formData.start_time} onChange={handleChange} required />
                </div>
                <div className="form-group">
                    <label>終了日時:</label>
                    <input type="datetime-local" name="end_time" value={formData.end_time} onChange={handleChange} required />
                </div>
                <button type="submit">予約する</button>
            </form>
        </div>
    );
};

export default ReservationForm;
