"use client";
import styles from "./login.module.css";
import { useState, useEffect } from "react";
import { useSignInWithEmailAndPassword } from "react-firebase-hooks/auth";
import { auth } from "@/app/firebase/config";
import { useRouter } from "next/navigation";
import { GoogleAuthProvider } from "firebase/auth";
import { signInWithPopup } from "firebase/auth";
import { UserAuth } from "../context/AuthContext";
import Image from "next/image";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signInWithEmailAndPassword] = useSignInWithEmailAndPassword(auth);
  const router = useRouter();
  const { user, googleSignIn, logOut } = UserAuth();
  const [loading, setLoading] = useState(true);

  const handleSignIn = async () => {
    try {
      await signInWithEmailAndPassword(email, password);
      setEmail("");
      setPassword("");
      router.push("/home/catalog");
    } catch (e) {
      console.error(e);
    }
  };

  const handleSignIng = async () => {
    try {
      await googleSignIn();
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
    const checkAuthentication = async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
      setLoading(false);
    };
    checkAuthentication();

    if (!loading && user) {
      router.push("/home/catalog");
    }
  }, [loading, user, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-sm w-full">
        <div className="text-center mb-8">
          <Image
            src="/logo.png"
            alt="Logo"
            width={100}
            height={100}
            className="mx-auto"
          />
        </div>
        <h1 className="text-3xl font-bold text-center mb-6 text-white">
          Login
        </h1>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-3 mb-4 bg-gray-700 rounded-lg border border-gray-600 focus:outline-none focus:border-indigo-400 transition text-white placeholder-gray-400"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-3 mb-4 bg-gray-700 rounded-lg border border-gray-600 focus:outline-none focus:border-indigo-400 transition text-white placeholder-gray-400"
        />
        <button
          onClick={handleSignIn}
          className="w-full p-3 bg-indigo-600 rounded-lg text-white hover:bg-indigo-500 transition shadow-md"
        >
          Sign In
        </button>

        <div className="text-center my-4 text-gray-400">or</div>

        <button
          onClick={handleSignIng}
          className="flex items-center justify-center w-full p-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition shadow-md"
        >
          <svg
            className="w-5 h-5 mr-2"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M22.674 11.24c0-.748-.068-1.464-.187-2.154H12v4.07h5.961c-.257 1.29-.998 2.381-2.112 3.109v2.566h3.418c2.006-1.85 3.156-4.569 3.156-7.591z"
              fill="#4285F4"
            />
            <path
              d="M12 23c3.106 0 5.705-1.034 7.606-2.806l-3.418-2.566c-.948.635-2.145 1.015-3.569 1.015-2.749 0-5.073-1.856-5.906-4.348H4.2v2.735C6.089 20.975 8.848 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M6.094 14.295a6.95 6.95 0 01-.365-2.295c0-.796.133-1.565.365-2.295V6.97H4.2a10.972 10.972 0 000 9.86l1.894-2.535z"
              fill="#FBBC05"
            />
            <path
              d="M12 4.856c1.512 0 2.868.52 3.937 1.542l2.936-2.936C16.59 1.977 14.284 1 12 1 8.848 1 6.089 3.025 4.2 6.971l1.894 2.735c.834-2.492 3.158-4.348 5.906-4.348z"
              fill="#EA4335"
            />
          </svg>
          Sign in with Google
        </button>

        <div className="flex justify-between items-center mt-6">
          <a href="#" className="text-sm text-indigo-400 hover:underline">
            Forgot password?
          </a>
          <a href="/signup" className="text-sm text-indigo-400 hover:underline">
            Sign Up
          </a>
        </div>
      </div>
    </div>
  );
}
