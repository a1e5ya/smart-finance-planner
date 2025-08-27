import { initializeApp } from 'firebase/app'
import { getAuth, signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider, createUserWithEmailAndPassword, signOut } from 'firebase/auth'

// Replace with your Firebase config from Step 1.3
const firebaseConfig = {
  apiKey: "AIzaSyBr4fjr3evFln-yyXwzVt-vK798QdEELs8",
  authDomain: "smart-finance-planner.firebaseapp.com",
  projectId: "smart-finance-planner",
  storageBucket: "smart-finance-planner.firebasestorage.app",
  messagingSenderId: "242305704892",
  appId: "1:242305704892:web:f3ec357c9720b8bd3d41b9"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()

// Auth functions
export const signInWithEmail = (email, password) => {
  return signInWithEmailAndPassword(auth, email, password)
}

export const signInWithGoogle = () => {
  return signInWithPopup(auth, googleProvider)
}

export const signUpWithEmail = (email, password) => {
  return createUserWithEmailAndPassword(auth, email, password)
}

export const logOut = () => {
  return signOut(auth)
}

console.log('Firebase initialized:', app.name) // This will help us debug