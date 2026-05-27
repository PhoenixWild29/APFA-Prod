import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertTriangle, XCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { authConfig } from '@/config/auth';

type VerifyStatus = 'loading' | 'success' | 'already_verified' | 'expired' | 'error';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<VerifyStatus>('loading');
  const [message, setMessage] = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const [resendStatus, setResendStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No verification token found in the URL.');
      return;
    }

    const verify = async () => {
      try {
        const res = await fetch(
          `${authConfig.apiEndpoint}/register/verify/${encodeURIComponent(token)}`
        );
        const data = await res.json();

        if (res.ok) {
          setStatus(data.status === 'already_verified' ? 'already_verified' : 'success');
          setMessage(data.message);
        } else if (res.status === 410) {
          setStatus('expired');
          setMessage(data.detail || 'Verification link has expired.');
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed.');
        }
      } catch {
        setStatus('error');
        setMessage('Network error. Please try again.');
      }
    };

    verify();
  }, [token]);

  const handleResend = async () => {
    if (!resendEmail.trim()) return;
    setResendStatus('sending');
    try {
      const res = await fetch(`${authConfig.apiEndpoint}/register/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resendEmail.trim() }),
      });
      if (res.ok) {
        setResendStatus('sent');
      } else {
        setResendStatus('error');
      }
    } catch {
      setResendStatus('error');
    }
  };

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border bg-card p-8 shadow-card">
        {status === 'loading' && (
          <div className="flex flex-col items-center gap-4 text-center">
            <Loader2 className="h-10 w-10 animate-spin text-teal-600" />
            <p className="text-sm text-muted-foreground">Verifying your email...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="flex flex-col items-center gap-4 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-600" />
            <h2 className="text-xl font-semibold">Email Verified!</h2>
            <p className="text-sm text-muted-foreground">{message}</p>
            <Button className="mt-2" onClick={() => navigate('/auth')}>
              Go to Login
            </Button>
          </div>
        )}

        {status === 'already_verified' && (
          <div className="flex flex-col items-center gap-4 text-center">
            <CheckCircle2 className="h-12 w-12 text-blue-500" />
            <h2 className="text-xl font-semibold">Already Verified</h2>
            <p className="text-sm text-muted-foreground">
              Your email is already verified. You can log in.
            </p>
            <Button className="mt-2" onClick={() => navigate('/auth')}>
              Go to Login
            </Button>
          </div>
        )}

        {status === 'expired' && (
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertTriangle className="h-12 w-12 text-amber-500" />
            <h2 className="text-xl font-semibold">Link Expired</h2>
            <p className="text-sm text-muted-foreground">{message}</p>

            <div className="mt-4 w-full space-y-3">
              <p className="text-xs text-muted-foreground">
                Enter your email to receive a new verification link:
              </p>
              <input
                type="email"
                value={resendEmail}
                onChange={(e) => setResendEmail(e.target.value)}
                placeholder="your@email.com"
                className="w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <Button
                className="w-full"
                onClick={handleResend}
                disabled={resendStatus === 'sending' || resendStatus === 'sent'}
              >
                {resendStatus === 'sending' && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {resendStatus === 'sent' ? 'Link Sent!' : 'Resend Verification'}
              </Button>
              {resendStatus === 'sent' && (
                <p className="text-xs text-green-600">
                  If an account exists, a new verification link has been sent.
                </p>
              )}
              {resendStatus === 'error' && (
                <p className="text-xs text-red-500">
                  Something went wrong. Please try again.
                </p>
              )}
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center gap-4 text-center">
            <XCircle className="h-12 w-12 text-red-500" />
            <h2 className="text-xl font-semibold">Verification Failed</h2>
            <p className="text-sm text-muted-foreground">{message}</p>
            <Button variant="outline" className="mt-2" onClick={() => navigate('/auth')}>
              Back to Login
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
