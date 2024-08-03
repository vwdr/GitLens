// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
	apiKey: "AIzaSyB_ah3WjjlPXD00bEK0neE9nJDCJkZIkqs",
	authDomain: "github-code-analyzer.firebaseapp.com",
	projectId: "github-code-analyzer",
	storageBucket: "github-code-analyzer.appspot.com",
	messagingSenderId: "497923885423",
	appId: "1:497923885423:web:fa7a2b61cc48bdd73e409a",
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
