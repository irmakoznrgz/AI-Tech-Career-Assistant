import axios from 'axios';

const API_BASE_URL = 'https://3.120.210.213.nip.io/api';

let sessionId = localStorage.getItem('tech_career_session_id');
if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('tech_career_session_id', sessionId);
}

export const searchJobs = async (searchQuery, uiFilters, limit = 50, cvText = "") => {
    try {
        const response = await axios.post(`${API_BASE_URL}/jobs/search`, {
            search_query: searchQuery,
            ui_filters: uiFilters,
            limit: limit,
            cv_text: cvText 
        });
        return response.data?.data || [];
    } catch (error) {
        console.error("Error occurred while searching for job:", error);
        return []; 
    }
};

export const uploadCv = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await axios.post(`${API_BASE_URL}/cv/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    } catch (error) {
        console.error("Error uploading CV:", error);
        throw error;
    }
};

export const generateGalaxyMap = async (jobs, cvText = "") => {
    try {
        const response = await axios.post(`${API_BASE_URL}/galaxy-map`, {
            jobs: jobs || [],
            cv_text: cvText
        });
        return response.data?.map_data || [];
    } catch (error) {
        console.error("Map could not be created:", error);
        throw error;
    }
};

export const resetChatSession = async () => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat/reset`, { session_id: sessionId });
        return response.data;
    } catch (error) {
        console.error("Chat memory reset failed:", error);
    }
};

export const streamChatResponse = async (userMessage, jobList, cvText, onChunkReceived) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                user_message: userMessage,
                job_list: jobList || [],
                cv_text: cvText || ""
            })
        });

        if (!response.ok) throw new Error('Chat response failed.');

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            onChunkReceived(chunk);
        }
    } catch (error) {
        console.error("Chat stream error:", error);
        throw error;
    }
};

export const getFilters = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/jobs/filters`);
        return response.data?.data || { locations: [], work_models: [], job_types: [], experiences: [], domains: [] };
    } catch (error) {
        console.error("Filters error:", error);
        return { locations: [], work_models: [], job_types: [], experiences: [], domains: [] };
    }
};

export const checkExpiredJobs = async (jobIds) => {
    if (!jobIds || jobIds.length === 0) return [];
    try {
        const response = await axios.post(`${API_BASE_URL}/jobs/check-expired`, {
            job_ids: jobIds
        });
        return response.data?.expired_ids || [];
    } catch (error) {
        console.error("Expired jobs check failed:", error);
        return [];
    }
};

export const getDashboardStats = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/dashboard/stats`);
        return response.data?.data || { work_models: [], experiences: [], locations: [], domains: [], timeline: [] };
    } catch (error) {
        console.error("Dashboard stats error:", error);
        return { work_models: [], experiences: [], locations: [], domains: [], timeline: [] };
    }
};

export const getChartInsight = async (chartName, chartData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/dashboard/insight`, {
            chart_name: chartName,
            chart_data: chartData
        });
        return response.data?.insight || "Analysis could not be retrieved.";
    } catch (error) {
        console.error("Insight error:", error);
        return "Analysis could not be retrieved.";
    }
};

export { sessionId, API_BASE_URL };