import axios from "axios";

const API = axios.create({
    baseURL: process.env.REACT_APP_API_URL
});

export const searchPapers = (data) =>
    API.post("/search", data);

export const downloadPdfUrl = (filename) =>
    `${API.defaults.baseURL}/download_pdf?filename=${filename}`;
