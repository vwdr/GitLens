import axios from "axios";

const BASE_URL = "http://localhost:8000";

export async function sendAnalysisRequest(username: string, queries: string[]) {
	return axios.post(`${BASE_URL}/analyze_account`, {
		username: username,
		queries: queries,
	});
}
