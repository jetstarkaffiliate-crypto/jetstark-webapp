import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


async def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.smtp_host:
        print(f"[EMAIL] Would send to {to}: {subject}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_user:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send to {to}: {e}")
        return False


async def send_welcome_email(email: str, name: str) -> bool:
    html = f"""
    <div style="font-family:Inter,system-ui,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#050a15;padding:2rem;text-align:center;border-bottom:3px solid #00ff88;">
        <h1 style="color:#f0f9ff;margin:0;font-size:1.5rem;">Jetstark</h1>
      </div>
      <div style="background:#0a1428;padding:2rem;color:#a8b5c4;">
        <h2 style="color:#f0f9ff;">Welcome, {name}!</h2>
        <p>Your Jetstark account is ready. Start exploring the marketplace, create affiliate links, or list your products.</p>
        <a href="{settings.cors_origin_list[0] if settings.cors_origin_list else 'http://localhost:5500'}/marketplace.html"
           style="display:inline-block;background:#00ff88;color:#050a15;padding:0.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;margin-top:1rem;">
          Browse Marketplace
        </a>
      </div>
      <div style="background:#050a15;padding:1rem;text-align:center;color:#5a6a7a;font-size:0.8rem;">
        &copy; 2026 Jetstark Inc.
      </div>
    </div>
    """
    return await send_email(email, "Welcome to Jetstark!", html)


async def send_order_confirmation(email: str, name: str, order_id: str, total: str) -> bool:
    html = f"""
    <div style="font-family:Inter,system-ui,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#050a15;padding:2rem;text-align:center;border-bottom:3px solid #00ff88;">
        <h1 style="color:#f0f9ff;margin:0;font-size:1.5rem;">Jetstark</h1>
      </div>
      <div style="background:#0a1428;padding:2rem;color:#a8b5c4;">
        <h2 style="color:#f0f9ff;">Order Confirmed!</h2>
        <p>Hi {name}, your order <strong>#{order_id[:8]}</strong> has been placed successfully.</p>
        <p style="font-size:1.25rem;color:#00ff88;">Total: ₦{total}</p>
        <a href="{settings.cors_origin_list[0] if settings.cors_origin_list else 'http://localhost:5500'}/orders.html"
           style="display:inline-block;background:#00ff88;color:#050a15;padding:0.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;margin-top:1rem;">
          View Order
        </a>
      </div>
      <div style="background:#050a15;padding:1rem;text-align:center;color:#5a6a7a;font-size:0.8rem;">
        &copy; 2026 Jetstark Inc.
      </div>
    </div>
    """
    return await send_email(email, f"Order Confirmed — #{order_id[:8]}", html)


async def send_password_reset_email(email: str, name: str, reset_url: str) -> bool:
    html = f"""
    <div style="font-family:Inter,system-ui,sans-serif;max-width:600px;margin:0 auto;">
      <div style="background:#050a15;padding:2rem;text-align:center;border-bottom:3px solid #00ff88;">
        <h1 style="color:#f0f9ff;margin:0;font-size:1.5rem;">Jetstark</h1>
      </div>
      <div style="background:#0a1428;padding:2rem;color:#a8b5c4;">
        <h2 style="color:#f0f9ff;">Reset Your Password</h2>
        <p>Hi {name}, click the button below to reset your password. This link expires in 1 hour.</p>
        <a href="{reset_url}"
           style="display:inline-block;background:#00ff88;color:#050a15;padding:0.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;margin-top:1rem;">
          Reset Password
        </a>
        <p style="margin-top:1.5rem;font-size:0.85rem;color:#5a6a7a;">If you didn't request this, you can safely ignore this email.</p>
      </div>
      <div style="background:#050a15;padding:1rem;text-align:center;color:#5a6a7a;font-size:0.8rem;">
        &copy; 2026 Jetstark Inc.
      </div>
    </div>
    """
    return await send_email(email, "Reset Your Jetstark Password", html)