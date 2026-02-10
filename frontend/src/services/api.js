import axios from "axios";

// SAME ORIGIN calls
const API = axios.create({
    baseURL: "/"
});

export const searchPapers = (data) =>
    API.post("/search", data);

export const downloadPdfUrl = (filename) =>
    `/download_pdf?filename=${filename}`;
