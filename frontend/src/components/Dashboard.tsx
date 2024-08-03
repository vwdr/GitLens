import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import sparkles from "../assets/sparkles.svg";
import { sendAnalysisRequest } from "../data";
import { QueryResponse } from "../types/types";
import "./Dashboard.css";
import QueryResponseCard from "./QueryResponseCard";
import AnimateHeight from "react-animate-height";
import { ThreeCircles, ThreeDots } from "react-loader-spinner";
import { db } from "../firebase";
import { collection, doc, onSnapshot } from "firebase/firestore";

const QUERY_OPTIONS = [
	{
		name: "Web Development",
		value: "How competent is the candidate at web development?",
	},
	{
		name: "C++ Programming",
		value: "How competent is the candidate at C++ programming?",
	},
	{
		name: "Data Structures",
		value: "How competent is the candidate at using data structures?",
	},
	{
		name: "Algorithms",
		value: "How competent is the candidate at using algorithms?",
	},
	{
		name: "JavaScript",
		value: "How competent is the candidate at coding in JavaScript?",
	},
	{
		name: "Python",
		value: "How competent is the candidate at coding in Python?",
	},
	{
		name: "Code Organization",
		value: "How well does the candidate organize their code?",
	},
	{
		name: "Databases",
		value: "How competent is the candidate at using databases?",
	},
	{
		name: "Object-Oriented Programming",
		value:
			"How competent is the candidate at using object-oriented programming?",
	},
	{
		name: "React",
		value: "How competent is the candidate at using React?",
	},
];

// const sampleQueryResponses: QueryResponse[] = [
// 	{
// 		query: "How well can the user code in C++?",
// 		score: 85,
// 		details: [
// 			{
// 				name: "Pointers",
// 				criterion: "Code implements pointers",
// 				weight: 0.3,
// 				score: 90,
// 				codeSnippets: [
// 					{
// 						code: "int* ptr = new int;",
// 						path: "/path/to/file.cpp",
// 						url: "https://example.com/code_snippet_1",
// 					},
// 					{
// 						code: "int* ptr = nullptr;",
// 						path: "/path/to/another/file.cpp",
// 						url: "https://example.com/code_snippet_2",
// 					},
// 				],
// 			},
// 			{
// 				name: "Memory Management",
// 				criterion: "Code effectively manages memory",
// 				weight: 0.4,
// 				score: 80,
// 				codeSnippets: [
// 					{
// 						code: "delete ptr;",
// 						path: "/path/to/file.cpp",
// 						url: "https://example.com/code_snippet_3",
// 					},
// 					{
// 						code: "std::unique_ptr<int> ptr = std::make_unique<int>();",
// 						path: "/path/to/another/file.cpp",
// 						url: "https://example.com/code_snippet_4",
// 					},
// 				],
// 			},
// 			// Add more rubric items as needed
// 		],
// 	},
// 	{
// 		query: "How proficient is the user in Python?",
// 		score: 75,
// 		details: [
// 			{
// 				name: "Exception Handling",
// 				criterion: "Effectively handles exceptions",
// 				weight: 0.3,
// 				score: 70,
// 				codeSnippets: [
// 					{
// 						code: "try:\n    # Code block\nexcept Exception as e:\n    # Exception handling",
// 						path: "/path/to/python_script.py",
// 						url: "https://example.com/python_code_3",
// 					},
// 					{
// 						code: "raise ValueError('Invalid value')",
// 						path: "/path/to/another/python_script.py",
// 						url: "https://example.com/python_code_4",
// 					},
// 				],
// 			},
// 			{
// 				name: "String Manipulation",
// 				criterion: "Demonstrates proficiency in string manipulation",
// 				weight: 0.5,
// 				score: 80,
// 				codeSnippets: [
// 					{
// 						code: "str1 = 'Hello'\nstr2 = 'world'\nresult = str1 + ', ' + str2",
// 						path: "/path/to/python_script.py",
// 						url: "https://example.com/python_code_5",
// 					},
// 					{
// 						code: "result = ''.join([word.capitalize() for word in sentence.split()])",
// 						path: "/path/to/another/python_script.py",
// 						url: "https://example.com/python_code_6",
// 					},
// 				],
// 			},
// 			// Add more rubric items as needed
// 		],
// 	},
// 	{
// 		query: "How skilled is the user in JavaScript?",
// 		score: 92,
// 		details: [
// 			{
// 				name: "ES6 Features",
// 				criterion: "Utilizes ES6 features effectively",
// 				weight: 0.4,
// 				score: 95,
// 				codeSnippets: [
// 					{
// 						code: "const square = (x) => x * x;",
// 						path: "/path/to/javascript_code.js",
// 						url: "https://example.com/js_code_3",
// 					},
// 					{
// 						code: "const { name, age } = person;",
// 						path: "/path/to/another/javascript_code.js",
// 						url: "https://example.com/js_code_4",
// 					},
// 				],
// 			},
// 			{
// 				name: "DOM Manipulation",
// 				criterion: "Demonstrates proficiency in DOM manipulation",
// 				weight: 0.6,
// 				score: 90,
// 				codeSnippets: [
// 					{
// 						code: "document.getElementById('myElement').innerHTML = 'New content';",
// 						path: "/path/to/javascript_code.js",
// 						url: "https://example.com/js_code_5",
// 					},
// 					{
// 						code: "const element = document.createElement('div');\nelement.textContent = 'Hello, world!';",
// 						path: "/path/to/another/javascript_code.js",
// 						url: "https://example.com/js_code_6",
// 					},
// 				],
// 			},
// 			// Add more rubric items as needed
// 		],
// 	},
// ];

export const Dashboard = () => {
	const {
		register,
		handleSubmit,
		formState: { errors },
	} = useForm();

	const [isFetching, setIsFetching] = useState(false);
	const [hasFetched, setHasFetched] = useState(false);

	const [cardData, setCardData] = useState([]);
	const [doc_id, setDocId] = useState("");
	const [updateString, setUpdateString] = useState("Analyzing...");

	useEffect(() => {
		console.log(cardData);
		if (!doc_id) return;

		const docRef = doc(db, "analysis-jobs", doc_id);

		// subscribe to the document
		const unsubscribe = onSnapshot(docRef, (doc) => {
			console.log("Current data: ", doc.data());
			let data = doc.data();
			if (!data) return;

			if (data["status"] === "pending") {
				let lastUpdate = data["updates"][data["updates"].length - 1];
				setUpdateString(lastUpdate);
			} else if (data["status"] === "complete") {
				setCardData(data["data"]);
				setIsFetching(false);
				setHasFetched(true);
			} else if (data["status"] === "error") {
				setUpdateString("An error occurred while analyzing the profile.");
				setIsFetching(false);
			}
		});
		return () => {
			unsubscribe();
		};
	}, [doc_id]);

	return (
		<div className="page-container center">
			<div
				className="profile-input glasscard"
				style={{
					gap: "unset",
				}}
			>
				<div
					className="heading-subheading"
					style={{
						marginBottom: "2rem",
					}}
				>
					<h1>
						{" "}
						<img src={sparkles} alt="sparkles" /> Evaluate a New Applicant
					</h1>
					<p>
						GitGuage combs through GitHub profiles and analyzes them based on
						customizable criteria. This tool is designed to help employers and
						hiring managers quickly and effectively evaluate candidates'
						qualifications and skills.
					</p>
				</div>
				<AnimateHeight
					duration={500}
					height={isFetching || hasFetched ? 0 : "auto"}
				>
					<form
						className="inner-container subcard"
						onSubmit={handleSubmit((data) => {
							console.log(data);

							let selectedCriteria: string[] = [];
							for (let i = 0; i < QUERY_OPTIONS.length; i++) {
								if (data["query-option-" + i]) {
									selectedCriteria.push(QUERY_OPTIONS[i].value);
								}
							}
							let gitUrlParts = data.url.split("/");
							if (gitUrlParts[gitUrlParts.length - 1] === "") {
								// remove trailing slash
								gitUrlParts.pop();
							}
							let gitUsername = gitUrlParts[gitUrlParts.length - 1];

							setIsFetching(true);
							sendAnalysisRequest(gitUsername, selectedCriteria).then(
								(response) => {
									console.log(response);
									data = response.data;
									// setIsFetching(false);
									// setHasFetched(true);
									// @ts-ignore
									// setCardData(response.data);
									setDocId(response.data);
								}
							);
						})}
					>
						<h2 className="input-label">GitHub Profile Link</h2>
						<input
							{...register("url", { required: true })}
							className="input"
							placeholder="Enter a GitHub URL..."
							style={{ borderColor: errors.url ? "red" : undefined }}
						/>

						<h2 className="input-label">Desired Evaluation Criteria</h2>
						<div className="multiselect">
							{QUERY_OPTIONS.map((option, index) => {
								return (
									<div className="select-bubble" key={"option" + index}>
										<input
											type="checkbox"
											id={option.name}
											value={option.value}
											{...register("query-option-" + index)}
										/>
										<label htmlFor={option.name}>{option.name}</label>
									</div>
								);
							})}
						</div>

						<button type="submit" className="button">
							Analyze Profile
						</button>
					</form>
				</AnimateHeight>
				<AnimateHeight
					duration={500}
					height={isFetching && !hasFetched ? "auto" : 0}
				>
					<div
						style={{
							display: "flex",
							flexDirection: "column",
							alignItems: "center",
							justifyContent: "center",
						}}
					>
						{isFetching && (
							<ThreeDots color="#0258FF" height={30} width={100} />
						)}
						<h2
							style={{
								color: "gray",
								fontWeight: "normal",
								textAlign: "center",
								marginTop: "1rem",
								fontStyle: "italic",
							}}
						>
							{updateString}
						</h2>
					</div>
				</AnimateHeight>
			</div>

			{cardData.map((data, index) => {
				return <QueryResponseCard key={"qr" + index} queryResponse={data} />;
			})}
		</div>
	);
};
