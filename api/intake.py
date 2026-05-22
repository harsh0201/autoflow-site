"""
Vercel Serverless Function — Proposal Engine
POST /api/intake

Receives intake form data → picks right plan → sends personalized HTML proposal email.

Env vars (set in Vercel dashboard after deploy):
  GMAIL_USER    = heyautoflow02@gmail.com
  GMAIL_PASS    = qbrynqtlmclabyyq
  SENDER_NAME   = Harsh
  PAYPAL_ME     = https://paypal.me/YOUR_HANDLE   (create at paypal.com/paypalme)
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── ENV ───────────────────────────────────────────────────────────────────────
GMAIL_USER  = os.environ.get("GMAIL_USER", "")
GMAIL_PASS  = os.environ.get("GMAIL_PASS", "").replace(" ", "")
SENDER_NAME = os.environ.get("SENDER_NAME", "Harsh")
PAYPAL_ME   = os.environ.get("PAYPAL_ME", "")   # e.g. https://paypal.me/yourname

def payment_link(amount: str) -> str:
    """Returns PayPal.me link with amount pre-filled, or a reply CTA if not set."""
    amt = amount.replace("$", "").replace(",", "").replace("/month", "").strip()
    if PAYPAL_ME:
        return f"{PAYPAL_ME.rstrip('/')}/{amt}USD"
    return f"mailto:{GMAIL_USER}?subject=Ready to get started"

# ── PLAN LOGIC ────────────────────────────────────────────────────────────────

def pick_plan(budget: str) -> dict:
    plans = {
        "under_1k": None,  # not a fit
        "1k_2k": {
            "name": "Starter",
            "price": "$1,500/month",
            "stripe": payment_link("1500"),
            "headline": "One core automation — deployed in 7 days",
            "includes": [
                "1 custom AI automation workflow",
                "7-day setup and deployment",
                "Full documentation and handoff",
                "1 monthly optimization session",
                "Email support",
            ],
        },
        "2k_5k": {
            "name": "Growth",
            "price": "$2,500/month",
            "stripe": payment_link("2500"),
            "headline": "Full ops automation — reporting, content, client updates",
            "includes": [
                "3 custom automation workflows",
                "Automated client reporting pipeline",
                "AI content brief generator",
                "Client update automation system",
                "Bi-weekly optimization calls",
                "Priority Slack support",
            ],
        },
        "5k_plus": {
            "name": "Scale",
            "price": "$4,500/month",
            "stripe": payment_link("4500"),
            "headline": "Full agency ops transformation — unlimited automations",
            "includes": [
                "Unlimited automation workflows",
                "Dedicated automation engineer",
                "Full ops audit and 90-day roadmap",
                "Weekly strategy sessions",
                "Custom AI model integrations",
                "White-glove onboarding",
            ],
        },
    }
    return plans.get(budget)


PAIN_LABELS = {
    "client_reporting": "client reporting",
    "content_briefs":   "content brief creation",
    "client_updates":   "client status updates",
    "lead_tracking":    "lead tracking",
    "invoicing":        "invoicing and billing",
    "internal_ops":     "internal operations",
    "onboarding":       "client onboarding",
    "data_sync":        "tool integrations",
}


def pain_summary(pains: list) -> str:
    labels = [PAIN_LABELS.get(p, p) for p in pains]
    if not labels:
        return "manual agency operations"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


# ── EMAIL BUILDER ─────────────────────────────────────────────────────────────

def build_proposal_email(data: dict, plan: dict) -> tuple[str, str, str]:
    """Returns (subject, body_text, body_html)"""
    fn      = data.get("first_name", "there")
    agency  = data.get("agency_name", "your agency")
    pains   = data.get("pain_points", [])
    size    = data.get("team_size", "")
    pain_str = pain_summary(pains)
    size_str = f"a {size}-person team" if size else "your team"

    subject = f"Your AutoFlow AI proposal for {agency}"

    text = f"""Hi {fn},

Thanks for filling out the form — here's your custom automation proposal for {agency}.

Based on what you shared, your biggest bottlenecks are {pain_str}. For {size_str}, that's likely costing 15–25 hours/week of manual work.

We recommend the {plan['name']} plan at {plan['price']}.

What's included:
{chr(10).join("• " + item for item in plan["includes"])}

Setup time: 7 business days from payment.
Guarantee: Save 10+ hours in 14 days or we work free until you do.

Ready to start? Pay via PayPal (takes 2 min):
{plan['stripe']}

Or just reply to this email and I'll send an invoice.

Questions? Just reply to this email.

— {SENDER_NAME}
AutoFlow AI"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e4e4e7;">

      <!-- Header -->
      <tr><td style="background:#0a0a0a;padding:28px 40px;">
        <span style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">Auto<span style="color:#818cf8;">Flow</span> AI</span>
      </td></tr>

      <!-- Body -->
      <tr><td style="padding:40px;">

        <p style="font-size:15px;color:#52525b;margin:0 0 24px;">Hi {fn},</p>

        <p style="font-size:15px;color:#18181b;line-height:1.7;margin:0 0 16px;">
          Thanks for taking the time — here's your custom automation proposal for <strong>{agency}</strong>.
        </p>

        <p style="font-size:15px;color:#18181b;line-height:1.7;margin:0 0 32px;">
          Based on what you shared, your team is losing the most time to <strong>{pain_str}</strong>.
          For {size_str}, that's typically <strong>15–25 hours/week</strong> of work that shouldn't exist.
          We can automate most of it in 7 days.
        </p>

        <!-- Plan card -->
        <div style="background:#fafafa;border:1px solid #e4e4e7;border-radius:12px;padding:32px;margin-bottom:32px;">
          <div style="font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6366f1;margin-bottom:8px;">Recommended Plan</div>
          <div style="font-size:32px;font-weight:800;letter-spacing:-1px;color:#0a0a0a;margin-bottom:4px;">{plan['name']}</div>
          <div style="font-size:24px;font-weight:700;color:#0a0a0a;margin-bottom:8px;">{plan['price']}</div>
          <div style="font-size:14px;color:#52525b;margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid #e4e4e7;">{plan['headline']}</div>
          <div style="font-size:13px;font-weight:700;color:#52525b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">What's included:</div>
          {''.join(f'<div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#22c55e;font-weight:700;flex-shrink:0;margin-top:1px;">✓</span><span style="font-size:14px;color:#18181b;line-height:1.5;">{item}</span></div>' for item in plan['includes'])}
        </div>

        <!-- Guarantee -->
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:20px;margin-bottom:32px;">
          <div style="font-size:14px;color:#15803d;font-weight:600;">🛡️ 14-Day Results Guarantee</div>
          <div style="font-size:14px;color:#166534;margin-top:6px;line-height:1.5;">
            If we don't save your team at least 10 hours in the first 14 days, we work for free until we do — or refund you in full.
          </div>
        </div>

        <!-- CTA -->
        <div style="text-align:center;margin-bottom:32px;">
          <a href="{plan['stripe']}"
             style="display:inline-block;background:#6366f1;color:#ffffff;padding:16px 40px;border-radius:10px;font-size:16px;font-weight:700;text-decoration:none;letter-spacing:-0.2px;">
            Pay via PayPal &amp; get started →
          </a>
          <div style="font-size:13px;color:#71717a;margin-top:12px;">Or reply to this email — I'll send an invoice directly.</div>
        </div>

        <hr style="border:none;border-top:1px solid #e4e4e7;margin-bottom:24px;">

        <p style="font-size:14px;color:#52525b;line-height:1.6;margin:0;">
          Questions before you pay? Just reply to this email — I'll get back to you within a few hours.
        </p>

      </td></tr>

      <!-- Footer -->
      <tr><td style="background:#fafafa;padding:24px 40px;border-top:1px solid #e4e4e7;">
        <p style="font-size:13px;color:#a1a1aa;margin:0;">
          AutoFlow AI &nbsp;·&nbsp; You received this because you filled out our intake form.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    return subject, text, html


def build_not_a_fit_email(data: dict) -> tuple[str, str, str]:
    """Sent when budget is under $1k — honest, no pitch."""
    fn     = data.get("first_name", "there")
    agency = data.get("agency_name", "your agency")

    subject = f"Re: your AutoFlow AI inquiry"
    text = f"""Hi {fn},

Thanks for reaching out about {agency}.

Based on the budget you shared, our retainer plans probably aren't the right fit right now — and I don't want to waste your time.

A couple of free options that might still help:
1. n8n.io (self-hosted automation, free) — good for basic workflow automation if you have someone technical
2. Make.com free tier — visual automation builder, 1,000 ops/month free

When budget grows and the pain is sharper, we're here.

— {SENDER_NAME}
AutoFlow AI"""

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;font-size:15px;color:#1a1a1a;max-width:560px;margin:40px auto;line-height:1.7;">
<strong style="font-size:18px;">Auto<span style="color:#6366f1;">Flow</span> AI</strong>
<hr style="border:1px solid #eee;margin:20px 0;">
<p>Hi {fn},</p>
<p>Thanks for reaching out about {agency}.</p>
<p>Based on the budget you shared, our retainer plans probably aren't the right fit right now — and I don't want to waste your time.</p>
<p>A couple of free options that might still help:</p>
<ul>
  <li><strong>n8n.io</strong> (self-hosted, free) — solid for basic workflow automation</li>
  <li><strong>Make.com free tier</strong> — visual builder, 1,000 ops/month free</li>
</ul>
<p>When budget grows and the pain is sharper, we're here.</p>
<p>— {SENDER_NAME}<br>AutoFlow AI</p>
</body>
</html>"""

    return subject, text, html


# ── SEND ──────────────────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, body_text: str, body_html: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SENDER_NAME} <{GMAIL_USER}>"
        msg["To"]      = to_email
        msg["Reply-To"] = GMAIL_USER
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[intake] Email send error: {e}")
        return False


# ── HANDLER ───────────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body)
        except Exception:
            self._respond(400, {"error": "invalid json"})
            return

        email  = (data.get("email") or "").strip().lower()
        budget = (data.get("budget") or "").strip()

        if not email or "@" not in email:
            self._respond(400, {"error": "invalid email"})
            return

        plan = pick_plan(budget)

        if plan is None:
            subject, text, html = build_not_a_fit_email(data)
        else:
            subject, text, html = build_proposal_email(data, plan)

        ok = send_email(email, subject, text, html)

        if ok:
            self._respond(200, {"ok": True})
        else:
            self._respond(500, {"error": "email send failed"})

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _respond(self, code: int, body: dict):
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        print(f"[intake] {fmt % args}")
