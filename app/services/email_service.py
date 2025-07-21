

async def _send_password_reset_email(email: str, token: str, frontend_url: str):
    """
    Simulates sending a password reset email.
    In production, integrate with an actual email sending library/service.
    """
    print(f"\n--- SIMULATED EMAIL ---")
    print(f"To: {email}")
    print(f"Subject: Your Password Reset Link")
    print(f"Body: Click the following link to reset your password:")
    print(f"{frontend_url}/reset_password?token={token}")
    print(f"This link is valid for 60 minutes.")
    print(f"-----------------------\n")
    # Here you would integrate with SendGrid, Mailgun, etc.
    # For example:
    # from aiosmtplib import SMTP
    # smtp = SMTP(hostname='your_smtp_host', port=587, use_tls=True)
    # await smtp.connect()
    # await smtp.login('username', 'password')
    # await smtp.sendmail('from@example.com', email, f"Subject: Reset Password\n\nLink: {frontend_url}/reset-password?token={token}")
    # await smtp.quit()