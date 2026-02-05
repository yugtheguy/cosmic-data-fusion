import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const OAuthCallbackPage = () => {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const token = searchParams.get('token');
      const error = searchParams.get('error');

      if (error) {
        // Send error message to parent window
        if (window.opener) {
          window.opener.postMessage(
            { type: 'oauth-error', error: 'OAuth authentication failed' },
            window.location.origin
          );
          window.close();
        }
        return;
      }

      if (!token) {
        // Send error message to parent window
        if (window.opener) {
          window.opener.postMessage(
            { type: 'oauth-error', error: 'No authentication token received' },
            window.location.origin
          );
          window.close();
        }
        return;
      }

      try {
        // Fetch user data with the token
        const response = await fetch('http://localhost:8000/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }

        const userData = await response.json();

        // Send success message to parent window
        if (window.opener) {
          window.opener.postMessage(
            { type: 'oauth-success', token, userData },
            window.location.origin
          );
          window.close();
        }
      } catch (error) {
        console.error('OAuth callback error:', error);
        // Send error message to parent window
        if (window.opener) {
          window.opener.postMessage(
            { type: 'oauth-error', error: 'Failed to complete authentication' },
            window.location.origin
          );
          window.close();
        }
      }
    };

    handleOAuthCallback();
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
        <p className="text-white mt-4">Completing authentication...</p>
      </div>
    </div>
  );
};

export default OAuthCallbackPage;
