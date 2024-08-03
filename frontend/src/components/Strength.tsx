import { useState } from "react";
import AnimateHeight from "react-animate-height";
import { CodeBlock } from "react-code-blocks";
import { RubricItem } from "../types/types";
import "./Strength.css";

interface StrengthProps {
	rubricItem: RubricItem;
}

export const Strength = (props: StrengthProps) => {
	const [open, setOpen] = useState(false);

	let goodColor = "green";

	if (props?.rubricItem.score >= 5) {
		goodColor = "green";
	} else if (props?.rubricItem.score >= 3) {
		goodColor = "#FFA500";
	} else {
		goodColor = "red";
	}

	return (
		<div
			className="subcard"
			style={{
				gap: 0,
				padding: "1rem",
				width: "100%",
			}}
		>
			<div
				style={{
					display: "flex",
					width: "100%",
					alignItems: "center",
				}}
			>
				<button
					className="toggle-open"
					onClick={() => setOpen(!open)}
					style={{
						fontSize: "1.25rem",
						padding: "0.5rem",
						backgroundColor: "transparent",
						border: "none",
						cursor: "pointer",
						height: "2rem",
						display: "flex",
						alignItems: "center",
						justifyContent: "center",
					}}
				>
					{open ? "▲" : "▼"}
				</button>

				<h2
					style={{
						marginLeft: "1rem",
					}}
				>
					{props?.rubricItem.name}
				</h2>
				<div style={{ flex: 1 }}></div>

				<div
					className="strength-bar"
					style={{
						display: "flex",
						gap: "0.25rem",
						overflow: "hidden",
						borderRadius: "0.5rem",
					}}
				>
					{Array.from({ length: 10 }, (_, i) => (
						<div
							key={i}
							className="bar"
							style={{
								width: "3rem",
								height: "1.5rem",
								backgroundColor:
									i < props?.rubricItem.score ? goodColor : "lightgrey",
							}}
						></div>
					))}
				</div>
			</div>
			<AnimateHeight duration={500} height={open ? "auto" : 0}>
				<div
					className="strength-content"
					style={{
						marginTop: "1rem",
					}}
				>
					{props?.rubricItem?.snippets && props.rubricItem.score > 4 ? (
						props.rubricItem.snippets.map((snippet, index) => {
							let extension = snippet.file_path.split(".").pop();
							return (
								<div
									key={"snippet" + index}
									className="code-snippet"
									style={{
										width: "100%",
										overflow: "hidden",
									}}
								>
									<p
										style={{
											color: "grey",
											// italics
											fontStyle: "italic",
											fontSize: "0.8rem",
										}}
									>
										From {snippet.file_path} in {snippet.repo_name}
									</p>
									<CodeBlock
										codeContainerStyle={{
											width: "100%",
											// backgroundColor: "#f5f5f5",
											fontSize: "0.8rem",
											maxHeight: "20rem",
											// overflowX: "hidden",
										}}
										text={snippet.code}
										language={extension}
										showLineNumbers={false}
									/>
								</div>
							);
						})
					) : (
						<p>No relevant code to show.</p>
					)}
				</div>
			</AnimateHeight>
		</div>
	);
};
