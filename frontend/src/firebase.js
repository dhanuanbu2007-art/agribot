import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAoT_EZ5TPPSf9BXn0-uZJ7NpDC_-QeqXo",
  authDomain: "agriguide-838da.firebaseapp.com",
  projectId: "agriguide-838da",
  storageBucket: "agriguide-838da.firebasestorage.app",
  messagingSenderId: "275731343031",
  appId: "1:275731343031:web:b02ac226de914d345d8f32"
};


const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
