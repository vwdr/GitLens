export interface CodeSnippet {
	code: string;
	file_path: string;
	repo_url: string;
	repo_name: string;
	repo_description: string;
}

export interface RubricItem {
	name: string;
	criterion: string;
	weight: number;
	score: number;
	snippets: CodeSnippet[];
}

export interface QueryResponse {
	query: string;
	score: number;
	details: RubricItem[];
}
