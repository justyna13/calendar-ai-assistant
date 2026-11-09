type TApiHealthResponse = {
    message: string;
}

export const getHealth = async (): Promise<TApiHealthResponse> => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);

    if (!response.ok) {
        throw Error('Api health check failed');
    }

    return response.json();
}

type TSessionStatus = {
    authenticated: boolean;
    email: string | null;
}

export const getSessionStatus = async (): Promise<TSessionStatus> => {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/session`,
        {
            credentials: "include",
            cache: "no-store"
        },
    );

    if (!response.ok) {
        throw Error("Session status check failed");
    }

    return response.json();
}

export const logout = async (): Promise<void> => {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/logout`,
        {
            method: "POST",
            credentials: "include"
        },
    );

    if (!response.ok) {
        throw Error("Logout failed");
    }
}