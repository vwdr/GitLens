import "./QueryBox.css";

interface CodeSnippet {
  file_path: string;
  code: string;
  score: number;
  repo_name: string;
  repo_url: string;
  repo_description: string;
}

const getColor = (score: number) => {
  if (score >= 7) {
    return "green";
  } else if (score >= 4 && score <= 6) {
    return "yellow";
  } else {
    return "red";
  }
};

export const QueryBox = (props: {
  query: string;
  score: number;
  code_snippets: CodeSnippet[];
}) => {
  return (
    <div className="analysis-container">
      <div className="queryBoxTitle">
        <h3>{props.query}</h3>
        <div className={`score ${getColor(props.score)}`}>{props.score}</div>
      </div>
      <div className="code-snippets">
        {props.score <= 3 ? (
          <p>No relevant code to show.</p>
        ) : (
          props.code_snippets.map((snippet, index) => (
            <CodeSnippet key={index} {...snippet} />
          ))
        )}
      </div>
    </div>
  );
};

const CodeSnippet = (props: CodeSnippet) => {
  return (
    <div className="code-snippet">
      <div className="code-snippet-title">
        <h4 className="code-snippet-title">{props.repo_name}</h4>
        <a
          href={props.repo_url}
          target="_blank"
          rel="noopener noreferrer"
          className="code-snippet-url"
        >
          Visit Repository
        </a>
      </div>

      <p className="code-snippet-description">{props.repo_description}</p>

      <pre className="code-snippet-code">{props.code}</pre>
    </div>
  );
};
