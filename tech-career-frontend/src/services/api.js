import axios from 'axios';

// FastAPI Address
const API_BASE_URL = 'http://127.0.0.1:8000/api';

let sessionId = localStorage.getItem('tech_career_session_id');
if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('tech_career_session_id', sessionId);
}

export const searchJobs = async (searchQuery, uiFilters, limit = 50) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/jobs/search`, {
            search_query: searchQuery,
            ui_filters: uiFilters,
            limit: limit
        });
        return response.data.data;
    } catch (error) {
        console.error("Error occurred while searching for job:",error);
        throw error;
    }
};

export const uploadCv = async (file) => {
    const FormData = require ? require('form-data') : window.FormData; 
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await axios.post(`${API_BASE_URL}/cv/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    } catch (error) {
        console.error("Error occurred while uploading the CV.:", error);
        throw error;
    }
};

export const generateGalaxyMap = async (jobs, cvText = "") => {
    try {
        const response = await axios.post(`${API_BASE_URL}/galaxy-map`, {
            jobs: jobs,
            cv_text: cvText
        });
        return response.data.map_data;
    } catch (error) {
        console.error("Map could not be created.:", error);
        throw error;
    }
};

export const resetChatSession = async () => {
    try {
        const response = await axios.post(`${API_BASE_URL}/chat/reset`, {
            session_id: sessionId
        });
        return response.data;
    } catch (error) {
        console.error("Chat memory could not be reset:", error);
    }
};


export const streamChatResponse = async (userMessage, jobList, cvText, onChunkReceived) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                user_message: userMessage,
                job_list: jobList,
                cv_text: cvText
            })
        });

        if (!response.ok) {
            throw new Error('Chat response was received.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            onChunkReceived(chunk);
        }
    } catch (error) {
        console.error("Error occurred in the chat stream:", error);
        throw error;
    }
};

export { sessionId, API_BASE_URL };