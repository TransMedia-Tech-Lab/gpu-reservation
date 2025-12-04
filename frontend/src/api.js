const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const fetchGPUs = async () => {
    const response = await fetch(`${API_BASE}/gpus`);
    if (!response.ok) {
        throw new Error('Failed to fetch GPUs');
    }
    return response.json();
};

export const fetchReservations = async (start, end, gpuId) => {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    if (gpuId) params.append('gpu_id', gpuId);

    const response = await fetch(`${API_BASE}/reservations?${params.toString()}`);
    if (!response.ok) {
        throw new Error('Failed to fetch reservations');
    }
    return response.json();
};

export const createReservation = async (reservation) => {
    const response = await fetch(`${API_BASE}/reservations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(reservation),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create reservation');
    }
    return response.json();
};

export const deleteReservation = async (reservationId) => {
    const response = await fetch(`${API_BASE}/reservations/${reservationId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error('Failed to delete reservation');
    }
    return true;
};

export const checkAvailability = async (start, end) => {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);

    const response = await fetch(`${API_BASE}/availability?${params.toString()}`);
    if (!response.ok) {
        throw new Error('Failed to check availability');
    }
    return response.json();
}
