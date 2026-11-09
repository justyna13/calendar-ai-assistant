"use client";

import { useEffect, useState } from "react";
import { getSessionStatus, logout } from "@/lib/api";

type TSessionStatus = {
    authenticated: boolean;
    email: string | null;
};

export default function GoogleLoginStatus() {
    const [session, setSession] = useState<TSessionStatus | null>(null);
    const [isAvailable, setIsAvailable] = useState(true);
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const [logoutError, setLogoutError] = useState(false);

    useEffect(() => {
        getSessionStatus()
            .then(setSession)
            .catch(() => setIsAvailable(false))
    }, []);

    async function handleLogout() {
        setIsLoggingOut(true);
        setLogoutError(false);

        try {
            await logout();
            window.location.reload();
        } catch {
            setLogoutError(true);
        } finally {
            setIsLoggingOut(false);
        }
    }

    if (session === null) {
        return (
            <span role="status">
                {isAvailable ? "Checking sign-in…" : "Unable to check sign-in status"}
            </span>
        );
    }

    if (!session.authenticated) {
        return (
            <a href={`${process.env.NEXT_PUBLIC_API_URL}/auth/google`}>
                Connect with Google
            </a>
        );
    }

    return (
        <>
        <span role="status">{session.email ?? "Logged in"}</span>
        <button
         type="button" 
         onClick={handleLogout} 
         disabled={isLoggingOut}
         className={isLoggingOut ? 'cursor-disabled': 'cursor-pointer'}
        >
            | {isLoggingOut ? "Signing out..." : "Sign out"}
        </button>
        {logoutError && <span role="alert">Couldn&apos;t sign out. Please try again.</span>}
        </>
    )
}