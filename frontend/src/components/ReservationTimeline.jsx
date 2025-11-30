import React, { useEffect, useState } from 'react';
import { fetchReservations, deleteReservation } from '../api';

const ReservationTimeline = ({ refreshTrigger }) => {
    const [reservations, setReservations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadReservations = async () => {
        try {
            const data = await fetchReservations();
            // Sort by start time descending
            data.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
            setReservations(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadReservations();
    }, [refreshTrigger]);

    const handleDelete = async (id) => {
        if (!window.confirm('本当にこの予約を削除しますか？')) return;
        try {
            await deleteReservation(id);
            loadReservations();
        } catch (err) {
            alert('予約の削除に失敗しました: ' + err.message);
        }
    };

    if (loading) return <div>予約を読み込み中...</div>;
    if (error) return <div className="error">エラー: {error}</div>;

    return (
        <div className="reservation-timeline">
            <h2>予約一覧</h2>
            <table className="reservation-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>GPU ID</th>
                        <th>ユーザー</th>
                        <th>目的</th>
                        <th>開始</th>
                        <th>終了</th>
                        <th>ステータス</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {reservations.map((res) => (
                        <tr key={res.id}>
                            <td>{res.id}</td>
                            <td>{res.gpu_id}</td>
                            <td>{res.user}</td>
                            <td>{res.purpose}</td>
                            <td>{new Date(res.start_time).toLocaleString()}</td>
                            <td>{new Date(res.end_time).toLocaleString()}</td>
                            <td>{res.status}</td>
                            <td>
                                <button onClick={() => handleDelete(res.id)} className="delete-btn">削除</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default ReservationTimeline;
