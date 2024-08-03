import { QueryResponse } from "../types/types";
import { Strength } from "./Strength";

interface Props {
	queryResponse: QueryResponse;
}

const QueryResponseCard = (props: Props) => {
	return (
		<div
			className="strengths-container glasscard"
			style={{
				display: "flex",
				flexDirection: "column",
				gap: "1rem",
			}}
		>
			<div className="heading-subheading">
				{/* <h1>{props.queryResponse.query}</h1> */}
				<h2>{props.queryResponse.query}</h2>
			</div>
			<div
				style={{
					display: "flex",
					flexDirection: "column",
					gap: "1rem",
					width: "100%",
				}}
			>
				{props.queryResponse.details.map((data, index) => {
					return <Strength key={"strength" + index} rubricItem={data} />;
				})}

				{!props.queryResponse.details && (
					<p>We couldn't find any relevant code for this query :/</p>
				)}
			</div>
		</div>
	);
};

export default QueryResponseCard;
