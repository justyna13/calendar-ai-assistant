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